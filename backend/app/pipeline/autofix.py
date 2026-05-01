from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from utils.logger import get_logger


log = get_logger("healpipe.autofix")


@dataclass
class AutoFixResult:
    changed: bool
    notes: str


def _replace_line(lines: list[str], pattern: re.Pattern[str], replacement: str) -> tuple[list[str], bool]:
    changed = False
    out: list[str] = []
    for line in lines:
        if pattern.search(line):
            log.info("autofix replacing line: %s -> %s", line.strip(), replacement.strip())
            out.append(replacement)
            changed = True
        else:
            out.append(line)
    return out, changed


def apply_autofixes(repo_dir: Path) -> AutoFixResult:
    req = repo_dir / "requirements.txt"
    if not req.exists():
        log.info("no requirements.txt found in %s — skipping autofixes", repo_dir)
        return AutoFixResult(changed=False, notes="no requirements.txt")

    original = req.read_text(encoding="utf-8", errors="ignore").splitlines()
    lines = original[:]
    log.info("requirements.txt has %d lines", len(lines))

    # Known-bad pins for modern Python: numpy 1.19.x doesn't support py3.10/3.11 and often fails to build.
    lines, changed_numpy = _replace_line(lines, re.compile(r"^\s*numpy==1\.19\.0\s*$", re.I), "numpy==1.26.4")

    # Remove empty trailing whitespace-only lines normalization (keep minimal).
    while lines and lines[-1].strip() == "":
        lines.pop()

    if lines != original:
        req.write_text("\n".join(lines) + "\n", encoding="utf-8")
        notes = []
        if changed_numpy:
            notes.append("bumped numpy==1.19.0 -> numpy==1.26.4")
        result_notes = ", ".join(notes) or "updated requirements"
        log.info("autofix applied requirements.txt changed=True notes=%s", result_notes)
        return AutoFixResult(changed=True, notes=result_notes)

    log.info("autofix: no changes needed in requirements.txt")
    return AutoFixResult(changed=False, notes="no changes")
