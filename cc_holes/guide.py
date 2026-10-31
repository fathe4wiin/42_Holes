"""Home-screen copy, the use guide, and the results log."""

from pathlib import Path

from cc_holes.model import Outcome

TAGLINE = "a TUI project to test your 42 project, made by student for students"

_GLYPHS: dict[str, tuple[str, str, str, str, str]] = {
    "4": (
        "█   █",
        "█   █",
        "█████",
        "    █",
        "    █",
    ),
    "2": (
        "█████",
        "    █",
        "█████",
        "█    ",
        "█████",
    ),
    "_": (
        "     ",
        "     ",
        "     ",
        "     ",
        "█████",
    ),
    "H": (
        "█   █",
        "█   █",
        "█████",
        "█   █",
        "█   █",
    ),
    "o": (
        "     ",
        " ███ ",
        "█   █",
        "█   █",
        " ███ ",
    ),
    "l": (
        "  █  ",
        "  █  ",
        "  █  ",
        "  █  ",
        "  █  ",
    ),
    "e": (
        "     ",
        "████ ",
        "█    ",
        "███  ",
        "████ ",
    ),
    "s": (
        "     ",
        " ████",
        "█    ",
        " ███ ",
        "████ ",
    ),
}


def _render_logo(title: str) -> str:
    lines = ["", "", "", "", ""]
    for index, char in enumerate(title):
        glyph = _GLYPHS[char]
        gap = " " if index else ""
        for row in range(5):
            lines[row] += gap + glyph[row]
    return "\n".join(lines)


LOGO = _render_logo("42_Holes")

SKIP_WHY: dict[str, str] = {
    "not a direct input": (
        "Fuzzer, speed check, sandbox, or a crash helper with no arguments in this file. "
        "A crash helper is the case where libc itself crashes. That input is undefined, "
        "and the subject allows a crash only then. It is not a pass."
    ),
    "argument is a harness name": (
        "The catalog stored a name. fsoares mem and dest are 256 bytes of 0x11 "
        "from reset() in utils.c, and war-machine fills are in each main.c. "
        "Those rows run. A name with no bytes in those files, or a rand() buffer, stays here."
    ),
    "check is not a direct call": (
        "The suite wrote a C or C++ check, for example l->content == (void*)1. "
        "The call text is kept for you to read. It is not executed."
    ),
    "not in libft.h": "libft.h in this project does not declare that function.",
    "print wrapper is custom": (
        "war-machine printed this result with a wrapper this tester cannot rebuild from the arguments."
    ),
    "inputs are not separated": (
        "The catalog kept the call as one string and did not split the arguments."
    ),
    "no runner for this function yet": (
        "This function is from an older libft. The tester does not call it yet."
    ),
    "null argument": "The call passes NULL. It is left to the crash checks, which are skipped.",
    "fd is not 1 or 2": "The call writes to a file descriptor other than stdout or stderr.",
    "count is too large to stage": "The size does not fit in a buffer this tester can build.",
    "no libc oracle": "Nothing in the catalog or in libc says what the return should be.",
    "oracle type is not handled": "The stored expected value is a kind this tester does not compare.",
}

GUIDE = """\
Skip is not a pass. The subject does not accept a wrong result.
A skipped row has no input this file can run. Your function can still be wrong.

What the subject (v19.2) requires, and this tester checks
  isalpha, isdigit, isalnum, isascii, isprint return exactly 1 or exactly 0.
  A return of 1024 fails, even though glibc does that.
  calloc(0, n), calloc(n, 0), and calloc(0, 0) return a pointer you can free.
  Lists are mandatory part 3. They are not a bonus.
  memset, bzero, memcpy, memmove, strlcpy, strlcat, strmapi, striteri,
  and every ft_lst* function have subject calls with a real buffer.
  A function the subject names and libft.h does not declare is a Fail.

Why a catalog row is still skipped
  not a direct input
      Fuzzer, speed check, or sandbox. No bytes to pass in.
      A crash row is the case where libc itself crashes. That is undefined.
      The subject allows a crash only for undefined behavior.
  argument is a harness name
      fsoares fills mem and dest with 256 bytes of 0x11. war-machine fills are in main.c.
      Those calls run. A rand() buffer still has no saved bytes, so that row stays here.
  check is not a direct call
      The suite wrote a C or C++ check, such as l->content == (void*)1.
      The subject list calls are the ones in the subject suite.
  not in libft.h
      The header does not declare it. For a subject function this is also a Fail.
  no runner for this function yet
      An older function that is not in this subject, such as ft_putchar.

What a call is
  The call is the line you would write, for example:
      ft_atoi("  123")
      ft_memset(buf, 'A', 4) on 8 bytes of 0xA5
  It is display text. The tester does not eval that string.

What each suite compares
  subject
      The behavior written in en.subject.pdf.
  fsoares
      Your function against libc, or against a stored string or the bytes written.
      strncmp and memcmp pass when the sign matches libc.
  Tripouille
      A direct call with an expected number, byte, string, or NULL.
      For the five is* functions, true means 1 and false means 0.
  war-machine
      The bytes the old test printed, including the loops i in 0..47.
  alelievr
      Sandbox and speed checks. The file has no input list for them.

Pass and Fail
  Pass means your result matched the subject, libc, or the stored value.
  Fail means the call ran and differed. The line under it is yours, then the supposed result.
  Select a function in the table to read the calls.

The log
  After a run, 42_holes.log is written in the project folder you gave.
  Every call is there: PASS, FAIL, or SKIP, then yours against the supposed result.
"""

CREDITS = """\
42_Holes
a TUI project to test your 42 project, made by student for students

The cases come from the francinette catalog:
  fsoares, Tripouille, war-machine, and alelievr.

libft is built with your Makefile, then each direct call is linked
against libft.a. libc is the oracle when the catalog does not store one.

ft_printf and get_next_line are listed. Their runners are not built yet.
"""


def write_log(folder: Path, sections: list[tuple[str, list[Outcome]]]) -> Path:
    """Write every call next to the result it was supposed to produce."""
    passed = failed = skipped = 0
    for _name, outcomes in sections:
        for item in outcomes:
            if item.status == "pass":
                passed += 1
            elif item.status == "fail":
                failed += 1
            else:
                skipped += 1
    lines = [
        "42_Holes",
        TAGLINE,
        f"project: {folder}",
        f"pass {passed}  fail {failed}  skip {skipped}",
        "",
        "Each call is the invocation from the catalog.",
        "PASS and FAIL show yours, then the supposed result (libc or the stored value).",
        "SKIP was not executed. The reason is under the call.",
        "",
        "Skip reasons",
    ]
    for reason, meaning in SKIP_WHY.items():
        lines.append(f"  {reason}")
        lines.append(f"      {meaning}")
    for function, outcomes in sections:
        lines.append("")
        lines.append(f"# {function}")
        for item in outcomes:
            lines.append(f"{item.status.upper():4}  {item.suite}  {item.part}")
            lines.append(f"  call: {item.call}")
            if item.status == "skip":
                lines.append(f"  why:  {item.detail}")
                meaning = SKIP_WHY.get(item.detail)
                if meaning:
                    lines.append(f"        {meaning}")
            else:
                lines.append(f"  check: {item.detail}")
    path = folder / "42_holes.log"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
