"""Grade push_swap against subject v1.2.

The first argument is the top of stack a. subjects/checker_linux runs the
operations and prints OK or KO. Already-sorted input must print nothing.
Inputs of 3 or fewer must use the shortest sequence. --bench writes the
disorder, the strategy, the complexity, and the operation counts to stderr.
100 and 500 numbers use the subject's pass limits. The student's checker
from make bonus is a separate row.
"""

import os
import random
import re
import shutil
import subprocess
import tempfile
from collections import deque
from pathlib import Path

from cc_holes.model import Outcome, build_row

_OPS = ("sa", "sb", "ss", "pa", "pb", "ra", "rb", "rr", "rra", "rrb", "rrr")
_FLAGS = ("--simple", "--medium", "--complex", "--adaptive")
_SCHOOL = Path(__file__).resolve().parent.parent / "subjects" / "checker_linux"


def _apply(stack_a: list[int], stack_b: list[int], op: str) -> None:
    def swap(stack: list[int]) -> None:
        if len(stack) >= 2:
            stack[0], stack[1] = stack[1], stack[0]

    def push(src: list[int], dst: list[int]) -> None:
        if src:
            dst.insert(0, src.pop(0))

    def rot(stack: list[int]) -> None:
        if len(stack) >= 2:
            stack.append(stack.pop(0))

    def rrot(stack: list[int]) -> None:
        if len(stack) >= 2:
            stack.insert(0, stack.pop())

    if op == "sa":
        swap(stack_a)
    elif op == "sb":
        swap(stack_b)
    elif op == "ss":
        swap(stack_a)
        swap(stack_b)
    elif op == "pa":
        push(stack_b, stack_a)
    elif op == "pb":
        push(stack_a, stack_b)
    elif op == "ra":
        rot(stack_a)
    elif op == "rb":
        rot(stack_b)
    elif op == "rr":
        rot(stack_a)
        rot(stack_b)
    elif op == "rra":
        rrot(stack_a)
    elif op == "rrb":
        rrot(stack_b)
    elif op == "rrr":
        rrot(stack_a)
        rrot(stack_b)
    else:
        raise ValueError(op)


def disorder(values: list[int]) -> float:
    """Subject ratio of inverted pairs. One element is 0."""
    total = 0
    mistakes = 0
    for left in range(len(values)):
        for right in range(left + 1, len(values)):
            total += 1
            if values[left] > values[right]:
                mistakes += 1
    if total == 0:
        return 0.0
    return mistakes / total


def _percent(values: list[int]) -> str:
    return f"{disorder(values) * 100:.2f}"


def _optimal(values: list[int]) -> int | None:
    """Shortest operation count. Only used for 3 numbers or fewer."""
    goal = tuple(sorted(values))
    start = (tuple(values), ())
    if start[0] == goal:
        return 0
    seen = {start}
    queue: deque[tuple[tuple[int, ...], tuple[int, ...], int]] = deque([(start[0], start[1], 0)])
    while queue:
        stack_a, stack_b, count = queue.popleft()
        if count >= 7:
            continue
        for op in _OPS:
            left = list(stack_a)
            right = list(stack_b)
            _apply(left, right, op)
            key = (tuple(left), tuple(right))
            if key in seen:
                continue
            seen.add(key)
            if key[0] == goal and not key[1]:
                return count + 1
            queue.append((key[0], key[1], count + 1))
    return None


def _parse_ops(stdout: bytes) -> tuple[list[str] | None, str | None]:
    if not stdout:
        return [], None
    try:
        text = stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None, "stdout is not text"
    if not text.endswith("\n"):
        return None, "the last operation has no newline"
    lines = text[:-1].split("\n")
    if any(line not in _OPS for line in lines):
        bad = next(line for line in lines if line not in _OPS)
        return None, f"unknown operation {bad!r}"
    return lines, None


def _invoke(binary: Path, args: list[str], stdin: bytes | None = None, timeout: float = 3):
    try:
        proc = subprocess.run(
            [str(binary), *args],
            input=stdin,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "timed out", b"", b""
    if proc.returncode < 0:
        return f"signal {-proc.returncode}", proc.stdout, proc.stderr
    return None, proc.stdout, proc.stderr


def _outcome(name: str, call: str, status: str, detail: str, part: str = "mandatory") -> Outcome:
    return Outcome(f"subject/push_swap/{name}", name, "subject", call, part, status, detail)


def _show(args: list[str]) -> str:
    return "push_swap " + " ".join(args)


def _quiet(problem: str | None, stdout: bytes, stderr: bytes) -> str | None:
    if problem:
        return problem
    if stdout or stderr:
        return "printed something. No arguments must print nothing."
    return None


def _error_text(problem: str | None, stdout: bytes, stderr: bytes) -> str | None:
    if problem:
        return problem
    if stdout:
        return "stdout is not empty"
    if stderr != b"Error\n":
        return "stderr is not Error followed by a newline"
    return None


def _school_checker() -> Path | None:
    if not _SCHOOL.is_file():
        return None
    if not os.access(_SCHOOL, os.X_OK):
        _SCHOOL.chmod(_SCHOOL.stat().st_mode | 0o111)
    return _SCHOOL


def _checker_says(values: list[int], ops: list[str], timeout: float) -> str | None:
    """None when subjects/checker_linux prints OK."""
    checker = _school_checker()
    if checker is None:
        return "subjects/checker_linux is missing"
    payload = "".join(f"{op}\n" for op in ops).encode()
    problem, stdout, stderr = _invoke(
        checker, [str(number) for number in values], stdin=payload, timeout=timeout
    )
    if problem:
        return f"checker {problem}"
    if stdout == b"OK\n" and not stderr:
        return None
    if stdout == b"KO\n":
        return "checker: KO"
    text = (stderr or stdout).decode("utf-8", "replace").strip()
    return f"checker: {text or 'no result'}"


def _sort_text(values: list[int], problem: str | None, stdout: bytes, stderr: bytes, exact: bool) -> str | None:
    if problem:
        return problem
    if stderr:
        return "stderr is not empty"
    ops, why = _parse_ops(stdout)
    if why or ops is None:
        return why
    why = _checker_says(values, ops, 5)
    if why:
        return why
    if exact:
        shortest = _optimal(values)
        if shortest is not None and len(ops) != shortest:
            return f"{len(ops)} operations, the shortest is {shortest}"
    elif not values or values == sorted(values):
        if ops:
            return "the stack is already sorted, so the shortest list is empty"
    return None


def _complexity(flag: str, values: list[int]) -> str:
    if flag == "--simple":
        return "n^2"
    if flag == "--medium":
        return "sqrt"
    if flag == "--complex":
        return "log"
    ratio = disorder(values)
    if ratio < 0.2:
        return "n^2"
    if ratio < 0.5:
        return "sqrt"
    return "log"


def _has_complexity(text: str, kind: str) -> bool:
    folded = text.lower().replace(" ", "")
    if kind == "n^2":
        return any(token in folded for token in ("n^2", "n2", "n²", "n**2"))
    if kind == "sqrt":
        return any(token in folded for token in ("sqrt", "√", "n^1.5", "n1.5"))
    return "log" in folded


def _bench_text(values: list[int], flag: str, problem: str | None, stdout: bytes, stderr: bytes) -> str | None:
    if problem:
        return problem
    ops, why = _parse_ops(stdout)
    if why or ops is None:
        return why
    why = _checker_says(values, ops, 5)
    if why:
        return why
    try:
        text = stderr.decode("utf-8")
    except UnicodeDecodeError:
        return "bench stderr is not text"
    if _percent(values) not in text:
        return f"bench disorder is not {_percent(values)}%"
    if flag not in text and flag[2:] not in text.lower():
        return f"bench does not name {flag[2:]}"
    kind = _complexity(flag, values)
    if not _has_complexity(text, kind):
        return f"bench complexity is not {kind}"
    counts = {op: ops.count(op) for op in _OPS}
    for op in ("rrr", "rra", "rrb", "rr", "ra", "rb", "sa", "sb", "ss", "pa", "pb"):
        match = re.search(rf"\b{op}\b\s*[:=]?\s*(\d+)", text)
        if match is None:
            return f"bench is missing {op}"
        found = int(match.group(1))
        if found != counts[op]:
            return f"bench {op} is {found}, the program printed {counts[op]}"
    return None


def _find(folder: Path, name: str) -> Path | None:
    direct = folder / name
    if direct.is_file() and os_access(direct):
        return direct
    for path in sorted(folder.glob(f"*/{name}")):
        if path.is_file() and os_access(path):
            return path
    return None


def os_access(path: Path) -> bool:
    return path.stat().st_mode & 0o111 != 0


def _sample(count: int, seed: int) -> list[int]:
    rng = random.Random(seed)
    return rng.sample(range(-count * 3, count * 3), count)


def run_push_swap(root: Path, control=None):
    """Yield the same events as the libft run."""
    from cc_holes.runner import (
        Done,
        Log,
        Plan,
        RunControl,
        Update,
        _blank_done,
        _make,
        _output_tail,
        _save_log,
        find_makefile,
    )

    control = control or RunControl()
    folder = root.expanduser()
    if not folder.is_absolute():
        folder = Path.cwd() / folder
    if shutil.which("make") is None:
        yield _blank_done("make is required.")
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
    binary = _find(folder, "push_swap")
    if code != 0 and binary is None:
        tail = _output_tail(output)
        if tail:
            yield Log(tail)
        yield _blank_done("make failed.")
        return
    if binary is None:
        yield _blank_done("push_swap was not found after make.")
        return
    if _school_checker() is None:
        yield _blank_done("subjects/checker_linux is missing.")
        return
    groups: dict[str, list[Outcome]] = {
        "arguments": [],
        "errors": [],
        "sort": [],
        "strategies": [],
        "bench": [],
        "100 numbers": [],
        "500 numbers": [],
        "checker": [],
    }

    def add(row: str, name: str, call: str, status: str, detail: str, part: str = "mandatory") -> None:
        groups[row].append(_outcome(name, call, status, detail, part))

    problem, stdout, stderr = _invoke(binary, [])
    why = _quiet(problem, stdout, stderr)
    add("arguments", "no-args", "push_swap", "fail" if why else "pass", why or "printed nothing")
    for label, values in (
        ("one", [42]),
        ("sorted", [1, 2, 3, 4]),
        ("ends", [-2147483648, 0, 2147483647]),
    ):
        args = [str(number) for number in values]
        problem, stdout, stderr = _invoke(binary, args)
        why = _sort_text(values, problem, stdout, stderr, exact=True)
        add("arguments", label, _show(args), "fail" if why else "pass", why or "sorted")
    errors = (
        ("word", ["0", "one", "2"]),
        ("duplicate", ["1", "2", "1"]),
        ("above-int", ["2147483648"]),
        ("below-int", ["-2147483649"]),
        ("empty", [""]),
        ("spaces", ["4 5"]),
        ("same-value", ["+1", "01"]),
        ("flag-dup", ["--simple", "3", "2", "3"]),
    )
    for name, args in errors:
        problem, stdout, stderr = _invoke(binary, args)
        why = _error_text(problem, stdout, stderr)
        add("errors", name, _show(args), "fail" if why else "pass", why or "Error")
    small = (
        [2, 1],
        [1, 3, 2],
        [3, 2, 1],
        [-1, -5, 3],
        [2, 1, 3, 6, 5, 8],
    )
    for values in small:
        args = [str(number) for number in values]
        problem, stdout, stderr = _invoke(binary, args)
        why = _sort_text(values, problem, stdout, stderr, exact=len(values) <= 3)
        add("sort", "n" + "-".join(args), _show(args), "fail" if why else "pass", why or "sorted")
    forced = [5, 4, 3, 2, 1]
    for flag in (*_FLAGS, ""):
        args = ([flag] if flag else []) + [str(number) for number in forced]
        problem, stdout, stderr = _invoke(binary, args, timeout=5)
        why = _sort_text(forced, problem, stdout, stderr, exact=False)
        label = flag or "default"
        add("strategies", label.strip("-"), _show(args), "fail" if why else "pass", why or "sorted")
    benches = (
        ("--adaptive", [1, 2, 3]),
        ("--adaptive", [2, 1, 3]),
        ("--adaptive", [3, 2, 1]),
        ("--simple", [3, 2, 1]),
        ("--medium", [1, 2, 3]),
        ("--complex", [1, 2, 3]),
    )
    for flag, values in benches:
        args = ["--bench", flag, *[str(number) for number in values]]
        problem, stdout, stderr = _invoke(binary, args, timeout=5)
        why = _bench_text(values, flag, problem, stdout, stderr)
        add("bench", flag.strip("-") + "-" + "-".join(args[2:]), _show(args), "fail" if why else "pass", why or "bench matches")
    limits = ((100, 2000, 1500, 700, 8), (500, 12000, 8000, 5500, 20))
    for count, ceiling, good, excellent, timeout in limits:
        values = _sample(count, count)
        args = [str(number) for number in values]
        problem, stdout, stderr = _invoke(binary, args, timeout=timeout)
        row = f"{count} numbers"
        if problem:
            add(row, "random", f"push_swap <{count} numbers>", "fail", problem)
            continue
        if stderr:
            add(row, "random", f"push_swap <{count} numbers>", "fail", "stderr is not empty")
            continue
        ops, why = _parse_ops(stdout)
        if why or ops is None:
            add(row, "random", f"push_swap <{count} numbers>", "fail", why or "no operations")
            continue
        why = _checker_says(values, ops, timeout)
        if why:
            add(row, "random", f"push_swap <{count} numbers>", "fail", why)
            continue
        total = len(ops)
        if total >= ceiling:
            add(row, "random", f"push_swap <{count} numbers>", "fail", f"{total} operations, the subject pass is under {ceiling}")
        else:
            rank = "excellent" if total < excellent else "good" if total < good else "pass"
            add(row, "random", f"push_swap <{count} numbers>", "pass", f"{rank}, {total} operations")
    handle, copied_name = tempfile.mkstemp(prefix="cc-holes-ps-")
    os.close(handle)
    copied = Path(copied_name)
    shutil.copy2(binary, copied)
    copied.chmod(0o755)
    yield Log("make bonus")
    code, output = _make(folder, control, "bonus")
    checker = _find(folder, "checker")
    if control.cancel.is_set():
        yield _blank_done("Stopped.")
        return
    if checker is None:
        detail = "make bonus did not produce checker. The bonus is not graded."
        if code != 0:
            detail = "make bonus failed. The bonus is not graded."
        add("checker", "missing", "checker", "warn", detail, "bonus")
    else:
        problem, stdout, stderr = _invoke(checker, [])
        why = _quiet(problem, stdout, stderr)
        add("checker", "no-args", "checker", "fail" if why else "pass", why or "printed nothing", "bonus")
        problem, stdout, stderr = _invoke(checker, ["3", "2", "one", "0"])
        why = _error_text(problem, stdout, stderr)
        add("checker", "bad-arg", "checker 3 2 one 0", "fail" if why else "pass", why or "Error", "bonus")
        values = [3, 2, 1, 0]
        problem, stdout, stderr = _invoke(copied, [str(number) for number in values])
        ops, ops_why = _parse_ops(stdout)
        if problem or ops_why or ops is None:
            add("checker", "ok", "push_swap | checker", "fail", problem or ops_why or "no operations", "bonus")
        else:
            problem, stdout, stderr = _invoke(checker, [str(number) for number in values], stdin=("\n".join(ops) + "\n").encode())
            if problem:
                add("checker", "ok", "push_swap | checker", "fail", problem, "bonus")
            elif stdout != b"OK\n" or stderr:
                add("checker", "ok", "push_swap | checker", "fail", "stdout is not OK", "bonus")
            else:
                add("checker", "ok", "push_swap | checker", "pass", "OK", "bonus")
        problem, stdout, stderr = _invoke(checker, ["3", "2", "1"], stdin=b"sa\n")
        if problem:
            add("checker", "ko", "checker 3 2 1 < sa", "fail", problem, "bonus")
        elif stdout != b"KO\n":
            add("checker", "ko", "checker 3 2 1 < sa", "fail", "stdout is not KO", "bonus")
        else:
            add("checker", "ko", "checker 3 2 1 < sa", "pass", "KO", "bonus")
        problem, stdout, stderr = _invoke(checker, ["3", "2", "1"], stdin=b"nope\n")
        why = _error_text(problem, stdout, stderr)
        add("checker", "bad-op", "checker < nope", "fail" if why else "pass", why or "Error", "bonus")
    copied.unlink(missing_ok=True)
    order = (
        ("arguments", "mandatory"),
        ("errors", "mandatory"),
        ("sort", "mandatory"),
        ("strategies", "mandatory"),
        ("bench", "mandatory"),
        ("100 numbers", "mandatory"),
        ("500 numbers", "mandatory"),
        ("checker", "bonus"),
    )
    rows = [build_row(name, groups[name], True, part=part) for name, part in order]
    yield Plan(rows)
    for row in rows:
        yield Update(row)
    log_path, log_error = _save_log(folder, [(name, groups[name]) for name, _part in order])
    if log_error:
        yield Log(f"Could not write 42_holes.log: {log_error}")
    flat = [item for name, _part in order for item in groups[name]]
    passed = sum(item.status == "pass" for item in flat)
    failed = sum(item.status == "fail" for item in flat)
    warned = sum(item.status == "warn" for item in flat)
    yield Done(passed, failed, 0, 0, [], None, log_path, warned)
