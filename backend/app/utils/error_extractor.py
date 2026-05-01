import re
from utils.logger import get_logger

log = get_logger("healpipe.extractor")

# More specific keywords to avoid false positives (e.g. "assert" in source code)
KEYWORDS = [
    re.compile(r"\bERROR\b"),
    re.compile(r"\bFAILED\b"),
    re.compile(r"Traceback \(most recent call last\)"),
    re.compile(r"AssertionError"),      # fixed typo from "AssertionError"
    re.compile(r"ModuleNotFoundError"),
    re.compile(r"ImportError"),
    re.compile(r"SyntaxError"),
    re.compile(r"NameError"),
    re.compile(r"TypeError"),
    re.compile(r"ValueError"),
]

CONTEXT_BEFORE = 10
CONTEXT_AFTER = 10
MAX_RESULTS = 15


def _line_matches(line: str) -> bool:
    return any(kw.search(line) for kw in KEYWORDS)


def extract_error(log_text: str) -> list[dict]:
    if not log_text:
        log.warning("extract_error called with empty log text")
        return []

    lines = log_text.split("\n")
    log.info("parsing %d lines for error patterns", len(lines))

    results: list[dict] = []
    covered: set[int] = set()  # track line indices already in a context window

    for i, line in enumerate(lines):
        if not _line_matches(line):
            continue

        # Skip if this line is already covered by a previous context window
        if i in covered:
            continue

        start = max(0, i - CONTEXT_BEFORE)
        end = min(len(lines), i + CONTEXT_AFTER)
        context = lines[start:end]

        # Mark these lines as covered to avoid duplicates
        for idx in range(start, end):
            covered.add(idx)

        error_type = None
        file_name = None
        line_no = None
        test_name = None

        for ctx_line in context:
            if "Traceback" in ctx_line:
                error_type = "Traceback"

            match = re.search(r'File "(.+?)", line (\d+)', ctx_line)
            if match:
                file_name = match.group(1)
                line_no = match.group(2)

            if "AssertionError" in ctx_line:
                error_type = "AssertionError"
            elif "ModuleNotFoundError" in ctx_line:
                error_type = "ModuleNotFoundError"
            elif "ImportError" in ctx_line:
                error_type = "ImportError"
            elif "SyntaxError" in ctx_line:
                error_type = "SyntaxError"

            if "FAILED" in ctx_line:
                error_type = error_type or "TestFailure"

            # pytest test name pattern
            test_match = re.search(r'::(test_\w+)', ctx_line)
            if test_match:
                test_name = test_match.group(1)

        results.append({
            "error_type": error_type,
            "file": file_name,
            "line": line_no,
            "test": test_name,
            "trigger_line": i,
            "context": context,
        })

        if len(results) >= MAX_RESULTS:
            log.warning("hit max results cap (%d), stopping extraction", MAX_RESULTS)
            break

    log.info("extracted %d unique error contexts from %d lines", len(results), len(lines))
    return results


def extract_errors(log_text: str) -> list[dict]:
    return extract_error(log_text)