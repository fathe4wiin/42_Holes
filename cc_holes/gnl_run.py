"""Grade get_next_line against subject v14.3.

The line includes the newline, except the last line of a file that has none.
NULL means the file is finished or the descriptor is unusable. A call must
return when it has a newline, without waiting for the end of the file.
Bonus is several descriptors at once, and only runs when the bonus files exist.
Valgrind checks a full read. A leak is a fail.
"""

import subprocess
import tempfile
from pathlib import Path

from cc_holes.leaks import check_leaks, valgrind_available
from cc_holes.model import Outcome, build_row, outcome_from

_SIZES = (1, 42)
_DRIVER = r"""
#include "{header}"
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void emit(const char *tag, char *line)
{{
	size_t i;
	size_t len;

	fputs(tag, stdout);
	if (!line)
	{{
		fputs(" NULL\n", stdout);
		fflush(stdout);
		return;
	}}
	len = strlen(line);
	fputs(" LINE ", stdout);
	for (i = 0; i < len; i++)
		printf("%02x", (unsigned char)line[i]);
	fputc('\n', stdout);
	fflush(stdout);
	free(line);
}}

static int open_read(const char *path)
{{
	int fd;

	fd = open(path, O_RDONLY);
	if (fd < 0)
	{{
		fprintf(stderr, "open failed\n");
		exit(2);
	}}
	return (fd);
}}

static void read_file(const char *path)
{{
	int fd;
	char *line;
	int count;

	fd = open_read(path);
	count = 0;
	while ((line = get_next_line(fd)) != NULL)
	{{
		emit("F", line);
		if (++count > 64)
			break;
	}}
	emit("F", NULL);
	close(fd);
}}

static void read_bad(const char *text)
{{
	emit("F", get_next_line(atoi(text)));
}}

static void read_pipe(const char *path, int leave_open)
{{
	unsigned char buf[4096];
	ssize_t got;
	int file;
	int ends[2];
	char *line;

	file = open_read(path);
	if (pipe(ends) < 0)
		exit(2);
	while ((got = read(file, buf, sizeof buf)) > 0)
	{{
		if (write(ends[1], buf, (size_t)got) != got)
			exit(2);
	}}
	close(file);
	if (!leave_open)
		close(ends[1]);
	line = get_next_line(ends[0]);
	emit("F", line);
	if (leave_open)
		return;
	while ((line = get_next_line(ends[0])) != NULL)
		emit("F", line);
	emit("F", NULL);
	close(ends[0]);
}}

static void read_two(const char *left, const char *right)
{{
	int a;
	int b;
	int i;
	char *line_a;
	char *line_b;

	a = open_read(left);
	b = open_read(right);
	i = 0;
	while (i < 8)
	{{
		line_a = get_next_line(a);
		line_b = get_next_line(b);
		emit("A", line_a);
		emit("B", line_b);
		if (!line_a && !line_b)
			break;
		i++;
	}}
	close(a);
	close(b);
}}

int main(int argc, char **argv)
{{
	alarm(2);
	if (argc < 3)
		return (2);
	if (strcmp(argv[1], "file") == 0)
		read_file(argv[2]);
	else if (strcmp(argv[1], "bad") == 0)
		read_bad(argv[2]);
	else if (strcmp(argv[1], "pipe") == 0 && argc == 4)
		read_pipe(argv[2], strcmp(argv[3], "open") == 0);
	else if (strcmp(argv[1], "two") == 0 && argc == 4)
		read_two(argv[2], argv[3]);
	else
		return (2);
	return (0);
}}
"""


def _lines_of(data: bytes) -> list[bytes]:
    if not data:
        return []
    found: list[bytes] = []
    start = 0
    for index, byte in enumerate(data):
        if byte == 10:
            found.append(data[start : index + 1])
            start = index + 1
    if start < len(data):
        found.append(data[start:])
    return found


def _hex(data: bytes) -> str:
    return data.hex()


def _expected_file(data: bytes) -> list[tuple[str, str | None]]:
    rows = [("F", _hex(line)) for line in _lines_of(data)]
    rows.append(("F", None))
    return rows


def _cases() -> list[tuple[str, str, list[tuple[str, str | None]]]]:
    long_line = b"x" * 200 + b"\n" + b"y"
    return [
        ("empty file", "file", _expected_file(b"")),
        ("line with a newline", "file", _expected_file(b"hello\n")),
        ("last line has no newline", "file", _expected_file(b"hello")),
        ("blank line in the middle", "file", _expected_file(b"a\n\nb\n")),
        ("newline only at the end of the first line", "file", _expected_file(b"a\nb")),
        ("only newlines", "file", _expected_file(b"\n\n")),
        ("line longer than the buffer", "file", _expected_file(long_line)),
        ("fd -1", "bad:-1", [("F", None)]),
        ("fd that was never opened", "bad:42", [("F", None)]),
        ("stop at the newline on a pipe", "pipe-open", [("F", _hex(b"ab\n"))]),
        ("read a pipe until it closes", "pipe-close", _expected_file(b"ab\ncd")),
    ]


def _write(folder: Path, name: str, data: bytes) -> Path:
    path = folder / name
    path.write_bytes(data)
    return path


def _sources(folder: Path, bonus: bool) -> list[Path]:
    if bonus:
        names = (
            "get_next_line_bonus.c",
            "get_next_line_utils_bonus.c",
        )
    else:
        names = ("get_next_line.c", "get_next_line_utils.c")
    return [folder / name for name in names if (folder / name).is_file()]


def _compile(folder: Path, sources: list[Path], header: str, size: int, binary: Path) -> str | None:
    driver = binary.with_suffix(".c")
    driver.write_text(_DRIVER.format(header=header), encoding="utf-8")
    command = [
        "gcc",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-Wno-unused-function",
        "-D",
        f"BUFFER_SIZE={size}",
        f"-I{folder}",
        str(driver),
        *[str(path) for path in sources],
        "-o",
        str(binary),
    ]
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode == 0:
        return None
    log = (proc.stderr or proc.stdout or "").strip()
    lines = [line for line in log.splitlines() if "error:" in line]
    return lines[0] if lines else (log.splitlines()[-1] if log else "compile failed")


def _run(binary: Path, args: list[str]) -> tuple[str | None, list[tuple[str, str | None]]]:
    try:
        proc = subprocess.run(
            [str(binary), *args],
            capture_output=True,
            timeout=4,
            start_new_session=True,
        )
    except subprocess.TimeoutExpired:
        return "timed out. The call has to return at the newline.", []
    if proc.returncode < 0:
        sig = -proc.returncode
        if sig == 14:
            return "timed out. The call has to return at the newline.", []
        return f"signal {sig}", []
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        return err or f"exited {proc.returncode}", []
    rows: list[tuple[str, str | None]] = []
    for raw in proc.stdout.splitlines():
        text = raw.decode("utf-8", "replace")
        tag, _, rest = text.partition(" ")
        if rest == "NULL":
            rows.append((tag, None))
        elif rest.startswith("LINE "):
            rows.append((tag, rest[5:]))
        else:
            return f"unreadable result {text[:80]}", []
    return None, rows


def _grade_one(got: list[tuple[str, str | None]], wanted: list[tuple[str, str | None]]) -> str | None:
    if got == wanted:
        return None
    if len(got) != len(wanted):
        return f"{len(got)} results, supposed {len(wanted)}"
    for index, (left, right) in enumerate(zip(got, wanted)):
        if left != right:
            return f"result {index + 1} differs"
    return "result differs"


def _one(
    ident: str,
    call: str,
    status: str,
    detail: str,
    part: str,
) -> Outcome:
    return Outcome(ident, "get_next_line", "subject", call, part, status, detail)


def run_gnl(root: Path, control=None):
    """Yield the same events as the libft run."""
    from cc_holes.runner import Done, Log, Plan, RunControl, Update, _blank_done, _save_log

    control = control or RunControl()
    folder = root.expanduser()
    if not folder.is_absolute():
        folder = Path.cwd() / folder
    if not folder.is_dir():
        yield _blank_done("That path is not a folder.")
        return
    source = folder / "get_next_line.c"
    header = folder / "get_next_line.h"
    if not source.is_file() or not header.is_file():
        yield _blank_done("get_next_line.c and get_next_line.h were not found in that folder.")
        return
    mandatory = _sources(folder, False)
    bonus_c = folder / "get_next_line_bonus.c"
    bonus_h = folder / "get_next_line_bonus.h"
    yield Log("Compiling get_next_line at BUFFER_SIZE 1 and 42.")
    outcomes: list[Outcome] = []
    bonus_outcomes: list[Outcome] = []
    leak_outcomes: list[Outcome] = []
    with tempfile.TemporaryDirectory(prefix="cc-holes-gnl-") as temporary:
        work = Path(temporary)
        binaries: dict[int, Path] = {}
        for size in _SIZES:
            if control.cancel.is_set():
                yield _blank_done("Stopped.")
                return
            binary = work / f"gnl-{size}"
            error = _compile(folder, mandatory, "get_next_line.h", size, binary)
            if error:
                yield _blank_done(f"BUFFER_SIZE={size}: {error}")
                return
            binaries[size] = binary
        payloads = {
            "file": {
                "empty file": b"",
                "line with a newline": b"hello\n",
                "last line has no newline": b"hello",
                "blank line in the middle": b"a\n\nb\n",
                "newline only at the end of the first line": b"a\nb",
                "only newlines": b"\n\n",
                "line longer than the buffer": b"x" * 200 + b"\n" + b"y",
            },
            "pipe-open": b"ab\nMORE",
            "pipe-close": b"ab\ncd",
        }
        leak_jobs: list[tuple[str, list[str]]] = []
        for name, mode, wanted in _cases():
            if mode == "file":
                path = _write(work, name.replace(" ", "_"), payloads["file"][name])
                args = ["file", str(path)]
            elif mode.startswith("bad:"):
                args = ["bad", mode.split(":", 1)[1]]
            elif mode == "pipe-open":
                path = _write(work, "pipe-open", payloads["pipe-open"])
                args = ["pipe", str(path), "open"]
            else:
                path = _write(work, "pipe-close", payloads["pipe-close"])
                args = ["pipe", str(path), "close"]
            if mode != "pipe-open":
                leak_jobs.append((name, args))
            failed = None
            for size in _SIZES:
                problem, got = _run(binaries[size], args)
                if problem:
                    failed = f"BUFFER_SIZE={size}: {problem}"
                    break
                mismatch = _grade_one(got, wanted)
                if mismatch:
                    failed = f"BUFFER_SIZE={size}: {mismatch}"
                    break
            if failed:
                outcomes.append(_one(f"subject/gnl/{name}", name, "fail", failed, "mandatory"))
            else:
                outcomes.append(
                    _one(f"subject/gnl/{name}", name, "pass", "matches at BUFFER_SIZE 1 and 42", "mandatory")
                )
        if bonus_c.is_file() and bonus_h.is_file():
            binary = work / "gnl-bonus"
            error = _compile(folder, _sources(folder, True), "get_next_line_bonus.h", 1, binary)
            call = "read fd A and fd B on alternate calls"
            if error:
                bonus_outcomes.append(
                    _one("subject/gnl/bonus", call, "fail", error, "bonus")
                )
            else:
                left = _write(work, "bonus-a", b"a\nb\n")
                right = _write(work, "bonus-b", b"c\nd\n")
                wanted = [
                    ("A", _hex(b"a\n")),
                    ("B", _hex(b"c\n")),
                    ("A", _hex(b"b\n")),
                    ("B", _hex(b"d\n")),
                    ("A", None),
                    ("B", None),
                ]
                problem, got = _run(binary, ["two", str(left), str(right)])
                if problem:
                    bonus_outcomes.append(_one("subject/gnl/bonus", call, "fail", problem, "bonus"))
                else:
                    mismatch = _grade_one(got, wanted)
                    if mismatch:
                        bonus_outcomes.append(
                            _one("subject/gnl/bonus", call, "fail", f"BUFFER_SIZE=1: {mismatch}", "bonus")
                        )
                    else:
                        bonus_outcomes.append(
                            _one("subject/gnl/bonus", call, "pass", "each descriptor keeps its own line", "bonus")
                        )
        else:
            bonus_outcomes.append(
                _one(
                    "subject/gnl/bonus",
                    "multiple file descriptors",
                    "warn",
                    "get_next_line_bonus.c is not in the folder. The bonus is not graded.",
                    "bonus",
                )
            )
        if not valgrind_available():
            leak_outcomes.append(
                _one("subject/gnl/leaks", "valgrind", "warn", "valgrind is not installed", "mandatory")
            )
        else:
            for name, args in leak_jobs:
                status, detail = check_leaks(binaries[1], args, timeout=20)
                leak_outcomes.append(_one(f"subject/gnl/leak/{name}", name, status, detail, "mandatory"))
            if bonus_c.is_file() and bonus_h.is_file() and (work / "gnl-bonus").is_file():
                left = work / "bonus-a"
                right = work / "bonus-b"
                status, detail = check_leaks(
                    work / "gnl-bonus", ["two", str(left), str(right)], timeout=20
                )
                leak_outcomes.append(
                    _one("subject/gnl/leak/bonus", "two descriptors", status, detail, "bonus")
                )
    rows = [
        build_row("get_next_line", outcomes, True, part="mandatory"),
        build_row("multiple fds", bonus_outcomes, True, part="bonus"),
        build_row("leaks", leak_outcomes, True, part="mandatory"),
    ]
    yield Plan(rows)
    for row in rows:
        yield Update(row)
    sections = [
        ("get_next_line", outcomes),
        ("multiple fds", bonus_outcomes),
        ("leaks", leak_outcomes),
    ]
    log_path, log_error = _save_log(folder, sections)
    if log_error:
        yield Log(f"Could not write 42_holes.log: {log_error}")
    everything = outcomes + bonus_outcomes + leak_outcomes
    passed = sum(item.status == "pass" for item in everything)
    failed = sum(item.status == "fail" for item in everything)
    warned = sum(item.status == "warn" for item in everything)
    yield Done(passed, failed, 0, 0, [], None, log_path, warned)
