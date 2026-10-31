"""Build a libft and run the cases this tester knows how to call."""

import os
import shutil
import signal
import subprocess
import tempfile
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from cc_holes.catalog import load_catalog, project_tests
from cc_holes.guide import write_log
from cc_holes.harness import compile_driver, render_driver, run_driver
from cc_holes.subject_cases import subject_cases
from cc_holes.model import (
    SUBJECT,
    Bound,
    Outcome,
    Row,
    build_row,
    classify,
    declared_functions,
    grade,
    outcome_from,
)

_HEADERS = (
    "libft.h",
    "includes/libft.h",
    "include/libft.h",
    "inc/libft.h",
    "headers/libft.h",
)
_MAKEFILES = ("Makefile", "makefile", "GNUmakefile")


class RunControl:
    """Stop make or a driver when the user leaves the run screen."""

    def __init__(self) -> None:
        self.cancel = threading.Event()
        self.proc: subprocess.Popen[str] | None = None

    def stop(self) -> None:
        self.cancel.set()
        proc = self.proc
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


@dataclass
class Log:
    text: str


@dataclass
class Plan:
    rows: list[Row] = field(default_factory=list)


@dataclass
class Update:
    row: Row


@dataclass
class Done:
    passed: int
    failed: int
    skipped: int
    other: int
    missing: list[str]
    error: str | None = None
    log_path: str | None = None


def find_header(root: Path) -> Path | None:
    for relative in _HEADERS:
        path = root / relative
        if path.is_file():
            return path
    return None


def find_makefile(root: Path) -> Path | None:
    for name in _MAKEFILES:
        path = root / name
        if path.is_file():
            return path
    return None


def find_archive(root: Path) -> Path | None:
    direct = root / "libft.a"
    if direct.is_file():
        return direct
    found = sorted(path for path in root.glob("*/libft.a") if path.is_file())
    if found:
        return found[0]
    return None


def _make(root: Path, control: RunControl) -> tuple[int, str]:
    proc = subprocess.Popen(
        ["make", "-C", str(root)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    control.proc = proc
    try:
        output, _ = proc.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        output, _ = proc.communicate()
        return 124, output or ""
    finally:
        control.proc = None
    return proc.returncode or 0, output or ""


def _blank_done(error: str, other: int = 0, log_path: str | None = None) -> Done:
    return Done(0, 0, 0, other, [], error, log_path)


def _save_log(
    folder: Path, sections: list[tuple[str, list[Outcome]]]
) -> tuple[str | None, str | None]:
    if not sections:
        return None, None
    try:
        return str(write_log(folder, sections)), None
    except OSError as exc:
        return None, str(exc)


def run_libft(root: Path, control: RunControl | None = None):
    """Yield log lines, a plan, one row update per function, then a summary."""
    control = control or RunControl()
    folder = root.expanduser()
    if not folder.is_absolute():
        folder = Path.cwd() / folder
    if shutil.which("make") is None or shutil.which("gcc") is None:
        yield _blank_done("make and gcc are required.")
        return
    if not folder.is_dir():
        yield _blank_done("That path is not a folder.")
        return
    if find_makefile(folder) is None:
        yield _blank_done("No Makefile in that folder.")
        return
    yield Log(f"make -C {folder}")
    code, output = _make(folder, control)
    if control.cancel.is_set():
        yield _blank_done("Stopped.")
        return
    archive = find_archive(folder)
    if code != 0 and archive is None:
        tail = "\n".join(output.strip().splitlines()[-12:])
        if tail:
            yield Log(tail)
        yield _blank_done("make failed.")
        return
    if code != 0:
        yield Log(f"make exited {code}. libft.a is there, continuing.")
    header = find_header(folder)
    if header is None or archive is None:
        yield _blank_done("libft.h or libft.a was not found after make.")
        return
    yield Log("A skip is not a pass. Subject calls still run.")
    try:
        text = header.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        yield _blank_done(f"Could not read {header.name}: {exc}")
        return
    declared = declared_functions(text)
    owned = subject_cases()
    cases = project_tests(load_catalog(), "libft")
    grouped: dict[str, list[dict]] = defaultdict(list)
    for case in cases:
        grouped[case["function"]].append(case)
    extras = sorted(
        name for name in grouped if name not in SUBJECT and name in declared
    )
    order = [name for name in SUBJECT if name in grouped or name in declared]
    order.extend(extras)
    other = sum(1 for case in cases if case["function"] not in order)
    prepared: list[tuple[str, list[Outcome], list[Bound], bool]] = []
    planned: list[Row] = []
    for function in order:
        present = function in declared
        outcomes: list[Outcome] = []
        live: list[Bound] = []
        incoming = list(grouped.get(function, []))
        if present:
            incoming.extend(owned.get(function, []))
        else:
            outcomes.append(
                outcome_from(
                    {
                        "id": f"subject/{function}/missing",
                        "function": function,
                        "suite": "subject",
                        "call": f"{function} is required by the subject",
                        "part": "",
                    },
                    "fail",
                    "libft.h does not declare it",
                )
            )
        for case in incoming:
            action = classify(case, declared)
            if action.status == "run" and action.bound is not None:
                live.append(action.bound)
            else:
                outcomes.append(outcome_from(case, "skip", action.reason))
        row = build_row(function, outcomes, present)
        if live and present:
            row.note = "running"
        prepared.append((function, outcomes, live, present))
        planned.append(row)
    yield Plan(planned)
    passed = 0
    failed = 0
    skipped = 0
    logged: list[tuple[str, list[Outcome]]] = []
    with tempfile.TemporaryDirectory(prefix="cc-holes-") as temporary:
        work = Path(temporary)
        for function, outcomes, live, present in prepared:
            if control.cancel.is_set():
                log_path, _error = _save_log(folder, logged)
                yield _blank_done("Stopped.", other, log_path)
                return
            if live:
                yield Log(f"{function}  {len(live)} calls")
                source = work / f"{function}.c"
                binary = work / function
                source.write_text(render_driver(live), encoding="utf-8")
                compiled, error = compile_driver(source, binary, header.parent, archive)
                if not compiled:
                    for bound in live:
                        outcomes.append(
                            outcome_from(bound.case, "fail", f"compile failed: {error}")
                        )
                else:
                    timeout = max(30.0, 5.0 * len(live))
                    results = run_driver(binary, live, timeout)
                    for bound in live:
                        student = results[bound.case["id"]]
                        status, detail = grade(bound.case, bound.spec, student, bound)
                        outcomes.append(outcome_from(bound.case, status, detail))
            row = build_row(function, outcomes, present)
            passed += row.passed
            failed += row.failed
            skipped += row.skipped
            logged.append((function, outcomes))
            yield Update(row)
    log_path, log_error = _save_log(folder, logged)
    if log_error:
        yield Log(f"Could not write 42_holes.log: {log_error}")
    missing = [name for name in SUBJECT if name not in declared and name in grouped]
    yield Done(passed, failed, skipped, other, missing, None, log_path)
