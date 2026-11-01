"""Build a libft or an ft_printf and run the cases this tester knows how to call."""

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
from cc_holes.printf_cases import ROW_ORDER, ROW_PART, printf_groups
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
    warned: int = 0


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


def _make(root: Path, control: RunControl, *goals: str) -> tuple[int, str]:
    proc = subprocess.Popen(
        ["make", "-C", str(root), *goals],
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
    yield Log("Running the calls that can break a libft.")
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
        row = build_row(function, outcomes, present)
        if live and present:
            row.note = "running"
        prepared.append((function, outcomes, live, present))
        planned.append(row)
    yield Plan(planned)
    passed = 0
    failed = 0
    warned = 0
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
            warned += row.warned
            skipped += row.skipped
            logged.append((function, outcomes))
            yield Update(row)
    log_path, log_error = _save_log(folder, logged)
    if log_error:
        yield Log(f"Could not write 42_holes.log: {log_error}")
    missing = [name for name in SUBJECT if name not in declared and name in grouped]
    yield Done(passed, failed, skipped, other, missing, None, log_path, warned)


_PRINTF_HEADERS = (
    "ft_printf.h",
    "includes/ft_printf.h",
    "include/ft_printf.h",
    "inc/ft_printf.h",
    "headers/ft_printf.h",
    "src/ft_printf.h",
)


def find_printf_header(root: Path) -> Path | None:
    for relative in _PRINTF_HEADERS:
        path = root / relative
        if path.is_file():
            return path
    return None


def find_printf_archive(root: Path) -> tuple[Path | None, bool]:
    """Return the archive and whether it sits at the repository root."""
    direct = root / "libftprintf.a"
    if direct.is_file():
        return direct, True
    found = sorted(path for path in root.glob("*/libftprintf.a") if path.is_file())
    if found:
        return found[0], False
    return None, False


def project_of(root: Path) -> str:
    """CLI picks ft_printf when that header is the project being built."""
    folder = root.expanduser()
    if not folder.is_absolute():
        folder = Path.cwd() / folder
    has_lib = find_header(folder) is not None
    has_printf = find_printf_header(folder) is not None
    if not has_printf:
        return "libft"
    if not has_lib:
        return "ft_printf"
    makefile = find_makefile(folder)
    text = ""
    if makefile is not None:
        try:
            text = makefile.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    if "libftprintf" in text:
        return "ft_printf"
    return "libft"


def _printf_includes(header: Path, root: Path) -> list[Path]:
    ordered = [header.parent, root]
    for relative in (
        "libft/includes",
        "libft/include",
        "libft",
        "includes",
        "include",
        "inc",
        "headers",
        "src",
    ):
        path = root / relative
        if path.is_dir():
            ordered.append(path)
    unique: list[Path] = []
    for path in ordered:
        if path not in unique:
            unique.append(path)
    return unique


def _printf_archives(root: Path, archive: Path) -> list[Path]:
    found: list[Path] = []
    for relative in ("libft/libft.a", "libft.a"):
        path = root / relative
        if path.is_file() and path.resolve() != archive.resolve():
            found.append(path)
    return found


def _output_tail(output: str) -> str:
    return "\n".join(output.strip().splitlines()[-12:])


def _missing_printf() -> dict:
    return {
        "id": "subject/ft_printf/missing",
        "function": "ft_printf",
        "suite": "subject",
        "call": "ft_printf is required by the subject",
        "part": "mandatory",
        "kind": "compare_libc",
        "args": [],
        "expected": None,
    }


def run_printf(root: Path, control: RunControl | None = None):
    """Yield log lines, a plan, one row update per conversion, then a summary."""
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
    archive, at_root = find_printf_archive(folder)
    if code != 0 and archive is None:
        tail = _output_tail(output)
        if tail:
            yield Log(tail)
        yield _blank_done("make failed.")
        return
    if code != 0:
        yield Log(f"make exited {code}. libftprintf.a is there, continuing.")
    header = find_printf_header(folder)
    if header is None or archive is None:
        yield _blank_done("ft_printf.h or libftprintf.a was not found after make.")
        return
    if not at_root:
        yield Log(
            "libftprintf.a is not at the repository root. "
            "The subject asks for it there. Continuing."
        )
    yield Log("Running the calls that can break an ft_printf.")
    try:
        text = header.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        yield _blank_done(f"Could not read {header.name}: {exc}")
        return
    declared = declared_functions(text)
    if "ft_printf" not in declared:
        outcomes = [
            outcome_from(_missing_printf(), "fail", "ft_printf.h does not declare it")
        ]
        row = build_row(
            "ft_printf",
            outcomes,
            False,
            part="mandatory",
            missing="required, not in ft_printf.h",
        )
        yield Plan([row])
        yield Update(row)
        log_path, log_error = _save_log(folder, [("ft_printf", outcomes)])
        if log_error:
            yield Log(f"Could not write 42_holes.log: {log_error}")
        yield Done(0, 1, 0, 0, ["ft_printf"], None, log_path, 0)
        return
    groups = printf_groups()
    root_warn = None
    if not at_root:
        root_warn = outcome_from(
            {
                "id": "subject/ft_printf/archive-root",
                "function": "",
                "suite": "subject",
                "call": "libftprintf.a is at the repository root",
                "part": "mandatory",
                "kind": "compare_libc",
                "args": [],
                "expected": None,
            },
            "warn",
            f"libftprintf.a was found at {archive}, not at the repository root. "
            "The subject asks for it there. This is a warning, not an error.",
        )
    prepared: list[tuple[str, list[Outcome], list[Bound], str]] = []
    planned: list[Row] = []
    warned_root = False
    for function in ROW_ORDER:
        live = groups.get(function, [])
        if not live:
            continue
        part = ROW_PART[function]
        outcomes = []
        if root_warn is not None and not warned_root:
            root_warn.function = function
            outcomes.append(root_warn)
            warned_root = True
        row = build_row(function, outcomes, True, part=part)
        if live:
            row.note = "running"
        prepared.append((function, outcomes, live, part))
        planned.append(row)
    yield Plan(planned)
    passed = 0
    failed = 0
    warned = 0
    skipped = 0
    logged: list[tuple[str, list[Outcome]]] = []
    includes = _printf_includes(header, folder)
    current = archive
    bonus_switched = False
    with tempfile.TemporaryDirectory(prefix="cc-holes-") as temporary:
        work = Path(temporary)
        saved = work / "mandatory-libftprintf.a"
        shutil.copy2(archive, saved)
        for index, (function, outcomes, live, part) in enumerate(prepared):
            if control.cancel.is_set():
                log_path, _error = _save_log(folder, logged)
                yield _blank_done("Stopped.", 0, log_path)
                return
            if part == "bonus" and not bonus_switched:
                yield Log("make bonus")
                bonus_code, bonus_output = _make(folder, control, "bonus")
                if control.cancel.is_set():
                    log_path, _error = _save_log(folder, logged)
                    yield _blank_done("Stopped.", 0, log_path)
                    return
                found, _root = find_printf_archive(folder)
                if bonus_code != 0:
                    yield Log("make bonus failed. Bonus calls use the library from make.")
                    tail = _output_tail(bonus_output)
                    if tail:
                        yield Log(tail)
                    current = found if found is not None else saved
                elif found is None:
                    yield Log(
                        "make bonus removed libftprintf.a. "
                        "Bonus calls use the library from make."
                    )
                    current = saved
                else:
                    current = found
                bonus_switched = True
            if live:
                yield Log(f"{function}  {len(live)} calls")
                source = work / f"pf_{index}.c"
                binary = work / f"pf_{index}"
                source.write_text(render_driver(live, header="ft_printf.h"), encoding="utf-8")
                compiled, error = compile_driver(
                    source,
                    binary,
                    header.parent,
                    current,
                    includes,
                    _printf_archives(folder, current),
                )
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
            row = build_row(function, outcomes, True, part=part)
            passed += row.passed
            failed += row.failed
            warned += row.warned
            skipped += row.skipped
            logged.append((function, outcomes))
            yield Update(row)
    log_path, log_error = _save_log(folder, logged)
    if log_error:
        yield Log(f"Could not write 42_holes.log: {log_error}")
    yield Done(passed, failed, skipped, 0, [], None, log_path, warned)
