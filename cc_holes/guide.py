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
        "Fuzzer, speed check, or sandbox. The file has no bytes to pass in. It is not a pass."
    ),
    "crash helper has no arguments": (
        "The catalog named a libc crash helper and did not store the input. "
        "The subject suite runs that probe. If libc crashes and your function returns, "
        "the result is a warning, not a pass and not an error."
    ),
    "guard helper has no arguments": (
        "The catalog named a part 2 guard and did not store the input. "
        "The subject suite runs that probe. A crash there is a warning, "
        "because the subject does not define the call."
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
    "null argument": (
        "The catalog call passes NULL and is not run as a value check. "
        "The subject crash probe covers that input."
    ),
    "fd is not 1 or 2": "The call writes to a file descriptor other than stdout or stderr.",
    "count is too large to stage": "The size does not fit in a buffer this tester can build.",
    "no libc oracle": "Nothing in the catalog or in libc says what the return should be.",
    "oracle type is not handled": "The stored expected value is a kind this tester does not compare.",
}

GUIDE = """\
The run lists calls that can break a libft. A catalog row that was only a name,
a C++ check, a fuzzer, or a sandbox program is not listed.

What the subject (v19.2) requires, and this tester checks
  isalpha, isdigit, isalnum, isascii, isprint return exactly 1 or exactly 0.
  A return of 1024 fails, even though glibc does that.
  calloc(0, n), calloc(n, 0), and calloc(0, 0) return a pointer you can free.
  Lists are mandatory part 3. They are not a bonus.
  memset, bzero, memcpy, memmove, strlcpy, strlcat, strmapi, striteri,
  and every ft_lst* function have subject calls with a real buffer.
  A function the subject names and libft.h does not declare is a Fail.

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

Pass, Fail, and Warning
  Pass means your result matched the subject, libc, or the stored value.
  Both crashing on the same undefined call is a Pass. That matches libc.
  Fail means the call ran and differed, or your function crashed where libc did not.
  Warning means libc crashed and your function returned. The subject says a crash
  is allowed only for undefined behavior, and part 1 still has to match libc.
  A warning is not an error. It does not fail the run. Select the function to read it.
  A part 2 call the subject does not define is a Warning when it crashes, and a Pass
  when it returns.

The log
  After a run, 42_holes.log is written in the project folder you gave.
  It lists FAIL and WARN only. A pass is not written.
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
    """Write failures and warnings. Passes are not logged."""
    failed = warned = 0
    blocks: list[str] = []
    for function, outcomes in sections:
        rows = [item for item in outcomes if item.status in {"fail", "warn"}]
        if not rows:
            continue
        blocks.append("")
        blocks.append(f"# {function}")
        for item in rows:
            if item.status == "fail":
                failed += 1
            else:
                warned += 1
            blocks.append(f"{item.status.upper():4}  {item.suite}  {item.part}")
            blocks.append(f"  call: {item.call}")
            blocks.append(f"  check: {item.detail}")
    lines = [
        "42_Holes",
        TAGLINE,
        f"project: {folder}",
        f"fail {failed}  warn {warned}",
        "",
        "FAIL is an error. WARN is libc crashing while your function returned,",
        "or a crash on a call the subject does not define. A warning is not an error.",
        "Passes are not listed.",
    ]
    lines.extend(blocks)
    path = folder / "42_holes.log"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
