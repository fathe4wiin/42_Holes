# 42_Holes context

Handoff as of 1 Nov 2026. Repo: `git@github.com:fathe4wiin/42_Holes.git`, branch `main`.

## What this is

A Python TUI that grades a student's libft or ft_printf. Libft subject is `libft_subject.pdf`, v19.2. Lists are mandatory part 3, not a bonus. ft_printf subject is `cc_holes/prinf_subject.pdf`, v12.1 (the file name is missing the t).

`francinette-tests.json` (schema `francinette-tests/1`) and `vendor/francinette/` were the kickstart. The subject wins when they disagree. Add a call when it breaks typical wrong code. Do not aim to cover every input. Part 1 is the exception: it must match libc, including a crash.

libft and ft_printf run. `get_next_line` is listed and its Run button stays disabled.

Tagline, exact, under the logo:

`a TUI project to test your 42 project, made by student for students`

Do not invent an author name. The logo is a 5-row block font in `cc_holes/guide.py`. Theme is dark red on black. Dependency is `textual>=8.2`. Verify the TUI with `App.run_test`, not a browser.

## Run

```sh
curl -fsSL https://raw.githubusercontent.com/fathe4wiin/42_Holes/main/run.sh | bash
curl -fsSL https://raw.githubusercontent.com/fathe4wiin/42_Holes/main/run.sh | bash -s -- ~/libft
```

`run.sh` installs `textual` for the user if it is missing. A piped run clones into `~/.cache/42_holes` (or `$XDG_CACHE_HOME/42_holes`). From this checkout, `./run.sh` uses this folder.

`curl | bash` leaves the script on stdin. The TUI redirect is on the `exec` line (`</dev/tty`). A redirect on an earlier line makes bash read the rest of the script from the terminal. Raw GitHub can serve the previous `run.sh` for about 5 minutes after a push.

`python3 holes.py` opens the TUI. `python3 holes.py /path/to/libft` grades that folder. Exit 1 if any call failed, 2 on a build or setup error. A warning does not fail the run.

Needs Python 3 with pip, git, gcc, and make. `strlcpy`, `strlcat`, and `strnstr` retry the link with `-lbsd`.

## Results

Pass, Fail, Warn. The table columns are Function, Part, Pass, Fail, Warn, Note. The banner is `Pass N   Fail N   Warn N`.

| Result | Meaning |
| --- | --- |
| Pass | Matched the subject, libc, or the stored value. Both crashing on the same undefined part 1 call is a pass. |
| Fail | The call differed, or the function crashed where libc did not. A missing subject function is one Fail: `libft.h does not declare it`. |
| Warn | libc crashed and the function returned, or a call the subject does not define crashed. A warning is not an error. |

`42_holes.log` in the project folder lists FAIL and WARN only. A clean run still writes the header with `fail 0  warn 0`.

Catalog rows that are only a name, a C++ assertion, a fuzzer, a sandbox, or a `rand()` buffer are dropped. They are not shown and not logged. `SKIP_WHY` in `guide.py` is unused. The guide subtitle in `app.py` still says "Skip"; the guide body does not.

Last full run of `/tmp/cc-holes-ref-libft` (not in this repo, and `/tmp` can disappear): 846 pass, 1 fail, 28 warn, about 15 seconds. The fail is `ft_strnstr(NULL, "a", 0)`: libbsd returns, that copy reads the haystack first. `ft_strnstr(NULL, "a", 1)` both crash and passes. The warnings are out-of-range character calls and part 2 NULL crashes. `/tmp/cc-holes-bad` only breaks `ft_atoi`.

## Screens

`HomeScreen` is a centered card, not the full terminal. `#brand` is 60% (logo and tagline), `#menu-slot` is 40%.

Home keys, all `priority=True`: `a` available tests, `g` guide, `c` credits, `q` quit. Arrows move. Enter opens the row. The menu is a `ListView`. It needs `focus()` and an index or Enter does nothing.

`Available tests` pushes `PickScreen`. Escape returns home. Enter opens `PathScreen`. The path is the folder with the Makefile. `get_next_line` opens it with Run disabled.

`RunScreen` keys: Escape back, `g` guide, `r` run again, `q` quit. Highlighting a row shows that function's fails, then its warnings.

`Static.content` is the text. There is no `renderable`.

## Subject rules

From `libft_subject.pdf` v19.2.

- Part 1 is the libc functions through `strdup` (23). Part 2 is `substr` through `putnbr_fd` (11). Part 3 is the nine `ft_lst*` functions.
- `isalpha`, `isdigit`, `isalnum`, `isascii`, `isprint` must return exactly 0 or 1. glibc `isalpha` returns 1024 for a letter. That fails. Other bools stay zero versus non-zero.
- `isascii` is graded as a value. Do not call libc for it. `_POSIX_C_SOURCE 200809L` hides the function, and glibc's macro does not crash.
- `toupper` / `tolower` of `EOF` is -1. Other out-of-range character mismatches are a warning (`soft`), not a fail.
- `calloc(0, *)` must return a unique pointer `free` accepts. `calloc((size_t)-1, (size_t)-1)` is compared by nullness and the pointer is not freed.
- Part 1 crash probes fork, silence stdio, and `alarm(1)`. libc crashed and the student returned: Warn. Student crashed and libc did not: Fail. Both crashed: Pass. Neither crashed on a pure crash probe: Pass.
- Part 2 and list calls the subject does not define: a crash is Warn, a return is Pass.
- `strncmp` and `memcmp` use the sign, not the magnitude.
- A negative count in the catalog is a `size_t`, not zero. String oracles stop at NUL. `_pad_mem` only pads a `mem` role when `0 <= n <= 2_000_000`.
- `ft_strncmp("1234", "1235", (size_t)-1)`, `ft_strnstr("aaabc", "abc", (size_t)-1)`, and the `strlcpy` / `strlcat` size `(size_t)-1` cases are real breakers.
- Leaks are not graded. There is no malloc hook. `ft_lstdelone` checks that `del` was called, not that the node was freed.

## Pipeline

1. `make -C <folder>` with a 180s timeout. If make fails and `libft.a` exists, continue.
2. Find `libft.h` in the root, `includes/`, `include/`, `inc/`, or `headers/`. Find `libft.a` in the root or one level down.
3. Parse `ft_*` from the header after stripping comments.
4. Group catalog tests by function. Append `subject_cases()` when the function is declared.
5. `classify` decides run or drop. `concretize` may replace a named buffer with bytes or a C snippet.
6. One driver per function: `gcc -Wall -Wextra -Wno-unused-function`. On link failure, retry with `-lbsd`.
7. One child per call, `alarm(3)`. The parent reads only when `poll` is ready. A blocking read after a timeout hung the suite.
8. Six tab fields, then `DONE`. Kinds include `int`, `size`, `null`, `bytes`, `mem`, `void`, `bad`, `lines`, `pair`, `ub`, and `guard`.
9. `grade` compares the observation to libc or to the stored value.
10. Write `42_holes.log`, including on cancel if anything was already graded.

The `call` string is display text. Nothing evals it. Arguments come from `args`. `INT_MAX` is the string `2147483647` when the parameter is a C string. `(e + "1").c_str()` is tab, newline, vertical tab, form feed, carriage return, then the quoted tail.

Named `mem` / `dest` / `src` bytes come from `cc_holes/buffers.py`, which follows `vendor/francinette/`. fsoares `reset` fills `0x11` for `MEM_SIZE` 256. `rand()` rows have no saved bytes. Do not invent a seed.

## Files

| Path | Role |
| --- | --- |
| `holes.py` | Launcher. Calls `cc_holes.__main__.main`. |
| `run.sh` | Curl and local launcher. |
| `cc_holes/catalog.py` | `json.load` the catalog. Order is libft, ft_printf, get_next_line, then the rest. |
| `cc_holes/model.py` | Subject list, classify, oracles, `grade`. |
| `cc_holes/harness.py` | C driver, crash probes, protocol. |
| `cc_holes/buffers.py` | Named buffers from the vendor C. |
| `cc_holes/subject_cases.py` | Subject snippets plus edge and breaker calls. |
| `cc_holes/printf_cases.py` | ft_printf subject breakers and the catalog slice. v12.1 decides mandatory vs bonus. |
| `cc_holes/runner.py` | make, plan, compile, run, log. Dropped cases are not recorded. |
| `cc_holes/guide.py` | Logo, tagline, guide, credits, `write_log`. |
| `cc_holes/app.py` | Textual screens and CSS. |
| `vendor/francinette/` | fsoares and war-machine sources for the buffer fills. |
| `francinette-tests.md` | Original catalog parse notes. The runner no longer surfaces skips. |

## Easy to break

- Capture stdout and stderr around the call, then restore the fds before the protocol `printf`.
- NULs are a byte array plus a trailing NUL. Char arguments are the byte 0..255.
- `emit_pair` is the strlcpy or strlcat return plus the buffer window.
- The driver is GNU C, not `-std=c99`. The subject forbids `restrict` in the student's prototypes. That constraint is theirs.
- New unused statics in the driver fail `-Werror` on unrelated functions unless marked unused. The compile line already passes `-Wno-unused-function`.
- Escape `\n` inside generated C strings. war-machine's diagnostic keeps the typo `adress`.
- `concretize` must ignore a case with no args. An empty crash row shares the name `ft_memset`.
- A pipe into `awk` hides `holes.py`'s exit code.

## ft_printf

Subject v12.1. Mandatory is bare conversions `cspdiuxX%`. Bonus is flags `-0.` plus a minimum field width (a number or `*`), and flags `#`, `+`, and space. The catalog still marks some of those flags as mandatory. The subject wins.

Stdout and the return value are compared with `printf` in one C driver. `%s` of NULL and `%p` of NULL follow this machine's libc. A `%c` of 0 must write a NUL byte. Leaks are not graded.

Rows are per conversion, plus `text`, `mix`, `ft_printf -0.`, and `ft_printf #+`. Not every catalog row runs. Subject breakers always run. Then up to 24 formats per row, plus a few edge values (0, -1, empty, NULL, INT_MIN, UINT_MAX). Length modifiers, positional `%1$`, and conversions outside `cspdiuxX%` are dropped.

`make`, then the mandatory rows. Then `make bonus`. If that fails or deletes `libftprintf.a`, bonus rows link the mandatory archive (a copy taken before `make bonus`). `ft_printf.h` is searched at the root and in `includes/`, `include/`, `inc/`, `headers/`, `src/`. `libft/libft.a` is linked when it exists. A library that is not at the repository root is a warning, and the run continues.

42 grades bonus only when mandatory is perfect. This tester still reports bonus fails.

## Still open

- `get_next_line` has no runner.
- No malloc interceptor, so a leak can pass.
- The reference libft is only in `/tmp`. Recreate it before trusting the 846 / 1 / 28 numbers.
