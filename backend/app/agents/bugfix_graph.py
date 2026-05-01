from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from openai import APITimeoutError

from config.settings import Settings, get_settings
from controller.llms import chat_complete
from utils.logger import get_logger

log = get_logger("healpipe.bugfix")


@dataclass
class PatchResult:
    ok: bool
    patch: str | None          # raw LLM response with SEARCH/REPLACE blocks
    raw: str
    notes: str
    edits: list[dict] = field(default_factory=list)  # parsed [{file, search, replace}, ...]


def _collect_repo_index(repo_dir: Path, *, max_files: int = 200) -> str:
    paths: list[str] = []
    for p in sorted(repo_dir.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(repo_dir)
        if ".git" in rel.parts:
            continue
        # Skip sandbox artifacts
        if rel.parts and rel.parts[0].startswith(".healpipe"):
            continue
        paths.append(str(rel))
        if len(paths) >= max_files:
            break
    return "\n".join(paths)


def _read_mentioned_files(repo_dir: Path, failure_summary: str, *, max_files: int = 10, max_chars: int = 8000) -> str:
    """Read the actual content of files mentioned in the error logs so the LLM can see the real code.
    Also reads ALL .py files in small repos to give the LLM maximum context."""
    import re
    # Extract filenames from error traces (Python-style tracebacks, import errors, etc.)
    patterns = [
        r'File "([^"]+\.py)"',          # Python traceback
        r'(\S+\.py):\d+',               # file.py:123
        r'in (\S+\.py)',                 # in module.py
        r'ModuleNotFoundError.*?(\S+)',  # missing modules
    ]
    mentioned = set()
    for pat in patterns:
        for match in re.finditer(pat, failure_summary):
            fname = match.group(1)
            # Only keep relative paths that exist in the repo
            candidate = repo_dir / fname
            if candidate.exists() and candidate.is_file():
                mentioned.add(fname)
            # Also try just the basename
            for p in repo_dir.rglob(Path(fname).name):
                if p.is_file() and ".git" not in p.relative_to(repo_dir).parts:
                    mentioned.add(str(p.relative_to(repo_dir)))

    # For small repos, also include all source files for maximum context
    all_source = []
    for p in sorted(repo_dir.rglob("*.py")):
        if p.is_file() and ".git" not in p.relative_to(repo_dir).parts and ".healpipe" not in str(p):
            all_source.append(str(p.relative_to(repo_dir)))
    if len(all_source) <= 15:
        for s in all_source:
            mentioned.add(s)

    parts = []
    for rel_path in sorted(mentioned)[:max_files]:
        fpath = repo_dir / rel_path
        try:
            content = fpath.read_text(errors="replace")
            if len(content) > max_chars:
                content = content[:max_chars] + "\n... (truncated)\n"
            # Add line numbers so LLM can reference exact lines
            numbered = "\n".join(f"{i+1:>4}| {line}" for i, line in enumerate(content.splitlines()))
            parts.append(f"=== {rel_path} ===\n{numbered}")
        except Exception:
            continue

    return "\n\n".join(parts)


def _is_bare_filepath(line: str) -> bool:
    """Check if a line looks like a standalone filepath (not actual code)."""
    s = line.strip()
    if not s:
        return False
    # Must look like a file path and NOT contain code-like characters
    code_chars = ('(', ')', '=', '+', '-', '*', '{', '}', '[', ']', ':', '#', 'import ', 'from ', 'def ', 'class ', 'return ')
    if any(c in s for c in code_chars):
        return False
    # Matches patterns like "app.py", "src/utils.py", "lib/index.js"
    import re
    return bool(re.match(r'^[\w./\-]+\.(py|js|ts|jsx|tsx|java|go|rs|rb|c|cpp|h|css|html)$', s))


def _parse_search_replace_blocks(text: str) -> list[dict]:
    """Parse SEARCH/REPLACE blocks from LLM response.
    
    Expected format:
    <<<<<<< SEARCH
    filepath: path/to/file.py
    old code here
    =======
    new code here
    >>>>>>> REPLACE
    """
    edits = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for SEARCH marker
        if "<<<<<<< SEARCH" in line or "<<<< SEARCH" in line:
            # Collect search block
            i += 1
            filepath = None
            search_lines = []
            replace_lines = []
            in_replace = False
            
            while i < len(lines):
                curr = lines[i]
                curr_stripped = curr.strip()
                
                # Check for filepath line (explicit "filepath:" tag)
                if not filepath and curr_stripped.startswith("filepath:"):
                    filepath = curr_stripped.split("filepath:", 1)[1].strip()
                    i += 1
                    continue
                
                # Check for separator
                if curr_stripped == "=======":
                    in_replace = True
                    i += 1
                    continue
                
                # Check for end marker
                if ">>>>>>> REPLACE" in curr_stripped or ">>>> REPLACE" in curr_stripped:
                    break
                
                if in_replace:
                    # Skip bare filepath lines that the LLM accidentally puts in the replacement
                    if not replace_lines and _is_bare_filepath(curr_stripped):
                        # If we already have a filepath, this is a duplicate — skip it
                        if filepath:
                            log.debug("skipping duplicate filepath in replace block: %s", curr_stripped)
                            i += 1
                            continue
                        # If we don't have a filepath yet, extract it
                        filepath = curr_stripped
                        i += 1
                        continue
                    replace_lines.append(curr)
                else:
                    # First non-filepath line in search could be the filepath
                    if not filepath and not search_lines and _is_bare_filepath(curr_stripped):
                        filepath = curr_stripped
                        i += 1
                        continue
                    search_lines.append(curr)
                
                i += 1
            
            if filepath and search_lines:
                edits.append({
                    "file": filepath,
                    "search": "\n".join(search_lines),
                    "replace": "\n".join(replace_lines),
                })
        i += 1
    
    return edits


def apply_edits(repo_dir: Path, edits: list[dict]) -> tuple[bool, str]:
    """Apply SEARCH/REPLACE edits to the repository files."""
    applied = 0
    failed = 0
    messages = []
    
    for edit in edits:
        filepath = repo_dir / edit["file"]
        if not filepath.exists():
            messages.append(f"SKIP: {edit['file']} does not exist")
            failed += 1
            continue
        
        try:
            content = filepath.read_text(errors="replace")
        except Exception as e:
            messages.append(f"SKIP: cannot read {edit['file']}: {e}")
            failed += 1
            continue
        
        search = edit["search"]
        replace = edit["replace"]
        
        # Try exact match first
        if search in content:
            content = content.replace(search, replace, 1)
            filepath.write_text(content)
            applied += 1
            messages.append(f"OK: {edit['file']} (exact match)")
            log.info("edit applied file=%s method=exact", edit["file"])
            continue
        
        # Try stripped match (ignore leading/trailing whitespace per line)
        search_stripped = "\n".join(l.strip() for l in search.split("\n"))
        content_lines = content.split("\n")
        search_lines = [l.strip() for l in search.split("\n") if l.strip()]
        
        # Sliding window match
        matched = False
        for start_idx in range(len(content_lines)):
            window = content_lines[start_idx:start_idx + len(search_lines)]
            window_stripped = [l.strip() for l in window]
            if window_stripped == search_lines:
                # Found! Replace these lines
                replace_lines = replace.split("\n")
                content_lines[start_idx:start_idx + len(search_lines)] = replace_lines
                filepath.write_text("\n".join(content_lines))
                applied += 1
                matched = True
                messages.append(f"OK: {edit['file']} (fuzzy match at line {start_idx + 1})")
                log.info("edit applied file=%s method=fuzzy line=%d", edit["file"], start_idx + 1)
                break
        
        if not matched:
            failed += 1
            messages.append(f"FAIL: {edit['file']} (search block not found in file)")
            log.warning("edit failed file=%s search_preview=%s", edit["file"], search[:80])
    
    summary = f"Applied {applied}/{applied + failed} edits"
    messages.insert(0, summary)
    all_ok = failed == 0 and applied > 0
    return all_ok, "\n".join(messages)


_SEARCH_REPLACE_PROMPT = """\
You are a senior Python engineer fixing bugs in a codebase.
You will be given the EXACT source code (with line numbers) and the test failure logs.

Your job: produce SEARCH/REPLACE edit blocks to fix the bug so all tests pass.

FORMAT (follow this EXACTLY — do NOT deviate):

<<<<<<< SEARCH
filepath: path/to/file.py
exact old code (WITHOUT line numbers, just raw code)
=======
new fixed code
>>>>>>> REPLACE

EXAMPLE — adding input validation to app.py:

<<<<<<< SEARCH
filepath: app.py
def calculate_discount(price, discount_percentage):
    final_price = price - (price * (discount_percentage / 100))
    return final_price
=======
def calculate_discount(price, discount_percentage):
    if discount_percentage < 0 or discount_percentage > 100:
        raise ValueError("Invalid discount percentage")
    final_price = price - (price * (discount_percentage / 100))
    return final_price
>>>>>>> REPLACE

CRITICAL RULES:
1. Copy the EXACT code from the source file into the SEARCH block (but strip line numbers — use raw code only).
2. The REPLACE block must contain ONLY the new code. NO filenames, NO markdown, NO explanations.
3. The filepath goes ONLY on the "filepath:" line after <<<<<<< SEARCH.
4. Do NOT write the filename anywhere in the REPLACE block.
5. Include 1-2 unchanged context lines around your changes in both SEARCH and REPLACE.
6. You can output MULTIPLE blocks for multiple changes.
7. Output NOTHING except SEARCH/REPLACE blocks.
8. Make sure the fixed code actually resolves the test failure shown in the error logs.
9. Add proper imports if your fix needs them (e.g. HTTPException for FastAPI).
"""


def generate_patch(
    *,
    repo_dir: Path,
    failure_summary: str,
    avoid_files: Optional[list[str]] = None,
    settings: Optional[Settings] = None,
) -> PatchResult:
    s = settings or get_settings()
    if not s.llm_api_key:
        log.warning("LLM not configured — skipping patch generation")
        return PatchResult(ok=False, patch=None, raw="", notes="LLM not configured (set HEALPIPE_LLM_API_KEY).")

    repo_index = _collect_repo_index(repo_dir)
    log.info("repo index: %d files collected", repo_index.count("\n") + 1 if repo_index else 0)

    # Read the actual source files mentioned in errors
    file_contents = _read_mentioned_files(repo_dir, failure_summary)
    log.info("read %d chars of mentioned file contents", len(file_contents))

    avoid_clause = ""
    if avoid_files:
        avoid_list = "\n".join(f"- {p}" for p in avoid_files)
        avoid_clause = (
            "\n\nConstraints:\n"
            "- Do NOT modify these files unless absolutely necessary:\n"
            f"{avoid_list}\n"
        )

    prompt = (
        "Repo file index (partial):\n"
        f"{repo_index}\n\n"
        f"{avoid_clause}"
        "Source files (relevant to the error):\n"
        f"{file_contents}\n\n"
        "Failure summary:\n"
        f"{failure_summary}\n"
    )

    def ask(extra: str) -> str:
        return chat_complete(
            [
                {"role": "system", "content": _SEARCH_REPLACE_PROMPT},
                {"role": "user", "content": prompt + "\n\n" + extra},
            ],
            model=s.llm_model,
            settings=s,
        )

    # Attempt 1
    log.info("LLM attempt 1 model=%s prompt_len=%d", s.llm_model, len(prompt))
    t0 = time.monotonic()
    try:
        raw1 = (ask("Fix the bug. Output ONLY SEARCH/REPLACE blocks. No explanations.") or "").strip()
    except APITimeoutError:
        log.error("LLM attempt 1 timed out after %.1fs", time.monotonic() - t0)
        return PatchResult(ok=False, patch=None, raw="", notes="LLM request timed out.")
    except Exception as e:
        log.error("LLM attempt 1 failed: %s: %s (%.1fs)", type(e).__name__, e, time.monotonic() - t0)
        return PatchResult(ok=False, patch=None, raw="", notes=f"LLM request failed: {type(e).__name__}: {e}")

    log.info("LLM attempt 1 done elapsed=%.1fs response_len=%d", time.monotonic() - t0, len(raw1))

    edits1 = _parse_search_replace_blocks(raw1)
    if edits1:
        log.info("LLM attempt 1 produced %d edit blocks", len(edits1))
        return PatchResult(ok=True, patch=raw1, raw=raw1, notes="ok", edits=edits1)

    # Attempt 2
    log.info("LLM attempt 1 did not produce valid edits, retrying (attempt 2)")
    t0 = time.monotonic()
    try:
        raw2 = (ask(
            "You MUST output SEARCH/REPLACE blocks in the exact format shown. "
            "Each block starts with <<<<<<< SEARCH and ends with >>>>>>> REPLACE. "
            "Include 'filepath: path/to/file.py' on the first line after SEARCH."
        ) or "").strip()
    except APITimeoutError:
        log.error("LLM attempt 2 timed out after %.1fs", time.monotonic() - t0)
        return PatchResult(ok=False, patch=None, raw=raw1, notes="LLM request timed out.")
    except Exception as e:
        log.error("LLM attempt 2 failed: %s: %s (%.1fs)", type(e).__name__, e, time.monotonic() - t0)
        return PatchResult(ok=False, patch=None, raw=raw1, notes=f"LLM request failed: {type(e).__name__}: {e}")

    log.info("LLM attempt 2 done elapsed=%.1fs response_len=%d", time.monotonic() - t0, len(raw2))

    edits2 = _parse_search_replace_blocks(raw2)
    if edits2:
        log.info("LLM attempt 2 produced %d edit blocks", len(edits2))
        return PatchResult(ok=True, patch=raw2, raw=raw2, notes="ok", edits=edits2)

    log.warning("LLM failed to produce valid edit blocks after 2 attempts")
    return PatchResult(ok=False, patch=None, raw=raw2 or raw1, notes="Model did not return valid SEARCH/REPLACE blocks.")


def generate_fix_summary(
    edits: list[dict],
    failure_summary: str,
    *,
    settings: Optional[Settings] = None,
) -> str:
    """Generate a human-readable summary of what was fixed."""
    s = settings or get_settings()
    if not s.llm_api_key:
        return "Fix applied (no summary available)."

    edits_text = ""
    for e in edits:
        edits_text += f"\nFile: {e['file']}\nOld:\n{e['search']}\nNew:\n{e['replace']}\n---\n"

    try:
        summary = chat_complete(
            [
                {"role": "system", "content": "You are a helpful assistant. Summarize code changes in 2-3 short sentences. Be specific about what bug was found and how it was fixed. Use simple language."},
                {"role": "user", "content": f"Error summary:\n{failure_summary[:2000]}\n\nChanges made:\n{edits_text[:3000]}\n\nWrite a brief, clear summary of what was wrong and how it was fixed."},
            ],
            model=s.llm_model,
            settings=s,
        )
        return (summary or "").strip()
    except Exception as e:
        log.warning("fix summary generation failed: %s", e)
        files_changed = list(set(e["file"] for e in edits))
        return f"Applied {len(edits)} edit(s) to {', '.join(files_changed)}."
