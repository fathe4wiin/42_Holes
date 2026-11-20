"""Valgrind leak check for push_swap and get_next_line.

A leak, an invalid read, or an invalid free is a fail. A missing valgrind
is a warning. The program's own exit code is not a leak.
"""

import re
import shutil
import subprocess
from pathlib import Path

_KINDS = ("definitely lost", "indirectly lost", "possibly lost", "still reachable")
_SKIP = (
    "HEAP SUMMARY",
    "LEAK SUMMARY",
    "ERROR SUMMARY",
    "total heap",
    "in use at exit",
    "All heap",
    "suppressed:",
    "For lists",
    "Use --",
    "To see",
    "Rerun",
)


def valgrind_available() -> bool:
    return shutil.which("valgrind") is not None


def _lost(text: str) -> list[str]:
    found: list[str] = []
    for kind in _KINDS:
        match = re.search(rf"{kind}: ([0-9,]+) bytes", text)
        if match is None:
            continue
        amount = int(match.group(1).replace(",", ""))
        if amount:
            found.append(f"{kind} {amount} bytes")
    return found


def _error_count(text: str) -> int:
    match = re.search(r"ERROR SUMMARY: (\d+) errors", text)
    if match is None:
        return 0
    return int(match.group(1))


def _first_error(text: str) -> str:
    for line in text.splitlines():
        cleaned = re.sub(r"^==\d+==\s?", "", line).strip()
        if not cleaned or cleaned.startswith(_SKIP):
            continue
        if cleaned.startswith(_KINDS):
            continue
        if "bytes" in cleaned and "blocks" in cleaned:
            continue
        return cleaned[:140]
    return "valgrind reported an error"


def check_leaks(
    binary: Path,
    args: list[str],
    stdin: bytes | None = None,
    timeout: float = 30,
) -> tuple[str, str]:
    """Return (status, detail). status is pass, fail, or warn."""
    if not valgrind_available():
        return "warn", "valgrind is not installed"
    command = [
        "valgrind",
        "--leak-check=full",
        "--show-leak-kinds=all",
        "--errors-for-leak-kinds=all",
        "--error-exitcode=99",
        str(binary),
        *args,
    ]
    try:
        proc = subprocess.run(
            command,
            input=stdin,
            capture_output=True,
            timeout=timeout,
            start_new_session=True,
        )
    except subprocess.TimeoutExpired:
        return "fail", "valgrind timed out"
    except FileNotFoundError:
        return "warn", "valgrind is not installed"
    text = proc.stderr.decode("utf-8", "replace")
    lost = _lost(text)
    if lost:
        return "fail", ", ".join(lost)
    if _error_count(text) or proc.returncode == 99:
        return "fail", _first_error(text)
    return "pass", "no leaks"
