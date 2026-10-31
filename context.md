# 42_Holes context

Handoff for the next session. This is the state of the libft tester as of 31 Oct 2026.

## What this project is

A Python TUI that grades a student's 42 project against the community francinette catalog, corrected against the current subject.

- Entry: `python3 holes.py` opens the TUI. `python3 holes.py /path/to/libft` runs libft on the command line (exit 1 if any fail, 2 on a build error).
- Catalog: `francinette-tests.json`, schema `francinette-tests/1`. Load it with `json.load`. Do not scan it as text.
- Parse contract: `francinette-tests.md`. Read it before changing what is skipped.
- Subject: `en.subject.pdf`, Libft version 19.2. Lists are mandatory part 3, not a bonus.
- Only libft runs. `ft_printf` (3547 tests) and `get_next_line` (94 tests) are listed and their Run button stays disabled. Any other project in the JSON is ignored.
- Theme is dark red on black: background `#070000`, hero `#ff5555`, panels `#140606` / `#100202`, borders `#6e1414` / `#8d1f1f`.
- Dependency: `textual>=8.2` (`requirements.txt`). The machine has Textual 8.2.8. There is no figlet. The logo is a hand-built 5-row block font in `cc_holes/guide.py`.

The tagline under the logo is exactly:

`a TUI project to test your 42 project, made by student for students`

Do not invent an author name.

## How to run and what was last measured

```sh
python3 holes.py
python3 holes.py /tmp/cc-holes-ref-libft
```

The reference library is not in this repo. It lives at `/tmp/cc-holes-ref-libft` (correct) and `/tmp/cc-holes-bad` (`ft_atoi` always returns 0). `/tmp` can disappear. Rebuild the reference before trusting a number.

Last full run of the correct reference, after the buffer recovery:

- 728 pass, 0 fail, 591 skip
- 416 tests belong to old functions that this reference does not declare
- `ft_memset` 11 calls, `ft_bzero` 5, `ft_memcpy` 5, `ft_memmove` 11, `ft_strlcpy` 12, `ft_strlcat` 28, `ft_memcmp` 18, `ft_calloc` 5, `ft_strmapi` 6, `ft_striteri` 5
- A full libft run is about 6 seconds

Earlier checkpoints, so a regression is obvious:

- First direct-call runner, before subject cases and loops: 562 pass, 0 fail, 730 skip
- After subject cases and war-machine loops, before named buffers: 646 pass, 0 fail, 673 skip
- Broken atoi, measured before those additions: 40 real `ft_atoi` fails (`yours 0, libc 123`)

The log is `<project folder>/42_holes.log`. It is plain text. Each call is `PASS`, `FAIL`, or `SKIP`, then yours against libc or the stored value. Skip reasons are expanded from `SKIP_WHY` in `cc_holes/guide.py`.

## Screens

`HolesApp` mounts `HomeScreen`.

The home card is `#window` (76 columns, 27 rows, centered in `#stage`). It is not the whole terminal. Inside that card:

- `#brand` is `height: 60%` and holds the ASCII `42_Holes` plus the tagline
- `#menu-slot` is `height: 40%` and holds the menu

Measured on a 100x36 terminal: the window content box is 25 rows, the brand is 15 (exactly 60%), the menu region is 10 (40%). `size.height` on the menu widget is smaller than its region because of padding. Trust the region.

Menu keys, all with `priority=True` so they work no matter which row is highlighted:

- `a` Available tests
- `g` Use guide
- `c` Credits
- `q` Quit
- Up and down move. Left and right move too. Enter opens the highlighted row.

`MenuList` is a `ListView`, not a stack of `Button`s. Buttons do not move on the arrow keys. A `ListView` does. Screen bindings need `priority=True` or the focused list eats the letter.

`Available tests` pushes `PickScreen`. Escape returns home. Enter on a project opens `PathScreen`. The path is the folder that contains the Makefile and the sources, not a path to one executable. `ft_printf` and `get_next_line` open the path screen with Run disabled.

`RunScreen` columns: Function, Part, Pass, Fail, Skip, Note. Keys: Escape back, `g` guide, `r` rerun, `q` quit. Highlighting a row rewrites the detail log with that function's fails, or skip samples. The banner after a run shows pass, fail, skip, missing subject functions, and the old-function count.

`Use guide` is the student-facing explanation of Skip, of what a call is, and of each suite. Keep it in agreement with this file and with `SKIP_WHY`.

Textual pitfalls already hit:

- `ListView` does nothing on Enter until it has `focus()` and `index` set. `PickScreen._ready` sets both.
- `Static.content` is the text. There is no `renderable` and `_content` is None.
- `run_worker(thread=True)` plus `call_from_thread` works under `App.run_test`.
- Verify the TUI with `App.run_test`. This is not a browser app.

## File map

| Path | Role |
| --- | --- |
| `holes.py` | Shebang launcher. Calls `cc_holes.__main__.main`. |
| `cc_holes/catalog.py` | `json.load`, schema check, project order libft / ft_printf / get_next_line then the rest. |
| `cc_holes/model.py` | Subject list, specs, bind, classify, oracles, grade, harness protocol parser. |
| `cc_holes/harness.py` | C driver. Forks one child per call, captures stdout and stderr around the call, prints a 6-field line. |
| `cc_holes/buffers.py` | Turns named `mem` / `dest` / `src` into the bytes from the original C. |
| `cc_holes/subject_cases.py` | Extra calls taken from `en.subject.pdf` when the catalog has no literal input. |
| `cc_holes/runner.py` | `make`, find `libft.h` and `libft.a`, plan rows, compile, run, write the log. |
| `cc_holes/guide.py` | Logo, tagline, guide text, credits, `write_log`. |
| `cc_holes/app.py` | Textual screens and CSS. |
| `vendor/francinette/fsoares/` | The C that defines `reset`, `MEM_SIZE`, and the fsoares tests. |
| `vendor/francinette/war-machine/` | The `main.c` files whose fills were copied into `buffers.py`. |

`vendor/francinette/fsoares/utils/utils.c` was not in the local `../francinette-image` checkout. The image's Dockerfile clones `xicodomingues/francinette`, but the copy under `francinette-image/francinette/tests/libft/fsoares/` has the `test_*.c` files and not `my_utils.c` or `utils/`. Those two were fetched from that GitHub repo and then copied into `vendor/`. `my_utils.c` is only the alarm and the test signature. The fill is `reset()` in `utils/utils.c`.

## Pipeline

1. `make -C <folder>` with a 180s timeout. If make is non-zero but `libft.a` exists, continue.
2. Find `libft.h` in the root, `includes/`, `include/`, `inc/`, or `headers/`. Find `libft.a` in the root or one level down.
3. Parse `ft_*` names out of the header with a regex, after stripping comments.
4. Group catalog tests by function. Append `subject_cases()` only when the function is declared.
5. `classify` each case into run or skip. `concretize` runs first and may replace a named buffer with real bytes or a C snippet.
6. One driver per function: `gcc -Wall -Wextra -Wno-unused-function -I<include> driver.c libft.a -Wl,--allow-multiple-definition`. On link failure, retry with `-lbsd` (strlcpy and strlcat are not in glibc).
7. Each case is a child with `alarm(3)`. The parent polls up to about 5 seconds and reads only when `poll` is ready. A blocking read after a timeout was a real bug. Do not put it back.
8. Protocol line, six tab fields: id, status, kind, payload, stdout hex, stderr hex, then a `DONE` line. Kinds: `int`, `size`, `null`, `bytes`, `mem`, `void`, `bad`, `lines`, `pair`.
9. `grade` compares the observation to libc or to the stored expected value.
10. Write `42_holes.log` in the project folder, including on cancel if anything was already graded.

A missing subject function is one Fail: `libft.h does not declare it`. Its catalog rows stay Skip with reason `not in libft.h`. The row note is `required, not in libft.h`. The banner also lists missing names.

Old functions that are not in `SUBJECT` and not in the header are counted as "old functions", not one table row each.

## Subject rules that changed the grader

From `en.subject.pdf` v19.2. These override "match glibc" where they disagree.

- Part 1 is the libc functions through `strdup` (23 functions). Part 2 is `substr` through `putnbr_fd` (11). Part 3 is the nine `ft_lst*` functions. `PART_OF` says `part 3`, not `bonus`.
- `isalpha`, `isdigit`, `isalnum`, `isascii`, `isprint` must return exactly 1 or exactly 0. glibc `isalpha` returns 1024 for a letter. A bool check used to treat any non-zero as true. That was wrong for these five. `_grade_ctype` requires the exact value. A return of 1024 fails with `subject: exactly 1 or 0`.
- Other bool checks (not these five) stay zero versus non-zero, because the subject only states the 1-or-0 rule for the character classes.
- `calloc`: if `nmemb` or `size` is 0, return a unique pointer that `free` accepts. On this machine glibc already does that for `(0,0)`, `(0,10)`, and `(10,0)`. The second `calloc(1,0)` can reuse an address after `free`, which is still a unique live pointer. A subject case calls `ft_calloc(0, 0)` because some catalog rows for that call have empty `args`.
- Functions must not crash, except on undefined behavior. A crash on a defined call is a Fail (`segfault`, `abort`, `timeout`, `bus error`, ...).
- Memory leaks are not tolerated by the subject. This tester does not hook `malloc`. `ft_lstdelone` checks that `del` was called. It does not prove the node itself was freed. Say that if someone asks for a leak grade.
- NULL arguments are skipped (`null argument`), except where a subject case defines them (`ft_lstnew(NULL)`, `ft_lstsize(NULL)`, `ft_lstlast(NULL)`). `strlen(NULL)` is undefined. Do not start failing those without a subject sentence that defines them.
- `ft_substr` start and length of `-1` are the unsigned conversions `(unsigned int)-1` and `(size_t)-1`, not a huge allocation. `_pad_mem` must not treat every negative size as "too large". It only pads when a `mem` role exists and `0 <= n <= 2_000_000`.

## What a call is

The `call` string is display text from the catalog, for example `ft_atoi("  123")`. Nothing evals that string. Arguments come from the `args` array as bytes, chars, and integers. The log and the detail pane show the call so a student can read it.

Known expressions that are real inputs:

- `INT_MAX` / `INT_MIN` as an int, or as the decimal string when the parameter is a C string. `ft_atoi(INT_MAX)` is the string `2147483647`.
- `EOF` as a C string is one byte `0xFF` then NUL. `(char)EOF` is `0xFF`.
- `'a' - 1` and `'z' + 1` are parsed. So is `'e' + 256`.
- Tripouille `(e + "1").c_str()` builds the five-byte string tab, newline, vertical tab, form feed, carriage return, then the quoted tail.

`ft_strncmp` and `ft_memcmp` against libc use the sign, not the magnitude. fsoares `same_sign`. A student may return -42 where libc returns -1.

fsoares `ft_putnbr_fd` stored stdout includes a newline because the original test then calls `ft_putendl_fd("")`. Strip one trailing newline only for that suite and function.

war-machine loops (`ft_isalpha(i) for i in 0..47`, and the same shape for the other `is*`, `toupper`, `tolower`, `putchar_fd`) are one catalog row for a whole inclusive range. ` exclusive` would exclude the end. The driver runs the range. For the five `is*` functions each return must be 0 or 1 and the captured bytes are the ASCII digits. `toupper` / `tolower` write the low 8 bits. `putchar_fd` writes to the fd in the case `body` (1 or 2). The stored `stream` matches that fd.

## Suites

- `subject`: calls this tester added from the PDF. Real buffers, list nodes, `strmapi` / `striteri` callbacks.
- `fsoares`: libc, or a stored string / split / written bytes. Buffer names are resolved in `buffers.py`.
- `Tripouille`: a direct call with an expected bool, number, byte, string, or NULL. List checks are often C++ (`l->content == (void*)1`) with empty args. Those stay skipped. The subject suite covers the list contract.
- `war-machine`: the bytes the old `main.c` printed. Comparison results are printed as -1, 0, or 1. A NULL pointer is the word `NULL`. If our reconstruction of that printer does not match the stored bytes, the case used to skip as `print wrapper is custom`. The named-buffer rows now replay the printer.
- `alelievr`: sandbox and speed. Empty args, the C is in `body`. Not run.
- `alelievr-hardcore`: one fuzzer per old function. Not run.

## Named buffers

The JSON stores the name `mem` or `dest` and `expected: null`. It does not store the bytes. `body` and `notes` are null. `source` is a path such as `francinette/tests/libft/fsoares/test_memset.c`.

Recovered fills:

- fsoares `reset(m1, m2, size)` is `memset(..., 0x11, size)`. `MEM_SIZE` is `0x100` (256).
- `reset_with` is that fill, then `strcpy` of the original string. `ft_strlcat` in the catalog lists the original string as an argument, but the C function only receives dest, src, and n. The original string is the initial contents. The compare window is `(n / 16 + 1) * 16` bytes, matching `same_mem` in `test_strlcat.c`. `strlcpy` compares the whole 256.
- fsoares `ft_memset(ptr, 143462, 4)` is an `int[256]` filled with `0x11`, the call starts one int in, and the compare is 16 bytes from the start of the array. The return must be that interior pointer.
- fsoares `ft_memmove` overlaps inside one buffer of `MEM_SIZE + 10`. The value `"123456"` is `strcpy`'d onto the source side after both sides are reset.
- fsoares `ft_memcpy(dest, src, 0)` does not depend on `rand_str`, because the count is 0. Both sides start as `0x11`. Any other memcpy count in that file is random and is not in the catalog as a single call.
- war-machine `ft_memset`: 15 bytes of `j`, then the call, and it prints 15 bytes. A wrong return pointer writes `mem's adress was not returned\n` first (the typo is in the original).
- war-machine `ft_bzero`: 5 bytes of `e`.
- war-machine `ft_memcpy`: 30 bytes of `j`.
- war-machine `ft_memmove`: `src` is `"lorem ipsum dolor sit amet"`, `dest` is `src + 1`, and 22 bytes are printed from `dest`. Cases 4 and 5 move the other way. The return check uses `dest's adress was not returned\n`.
- war-machine `ft_strlcpy` / `ft_strlcat`: 15-byte buffer, zeros, then 6 `r`s. The printer writes the size in decimal, a newline, then 15 bytes. Per-index mutations (`dest[11] = 'a'`, all `r`s, and so on) follow `ft_strlcat/main.c`.
- fsoares `memcmp` / `strncmp` / `strnstr` cases `s1` and `s2` are the arrays in `test_memcmp.c`, `test_strncmp.c`, and `test_strnstr.c`. The interesting ones are `"abc\xfdxx"` and the same buffers with index 3 set to NUL, so a function that does not stop at NUL reads `e` versus `x`. `empty` for `strnstr` is a 10-byte stack buffer with `[0] = 0` and `[1] = 'a'`. The original left the tail uninitialized. This tester zeros that tail. A correct `strnstr` never reads it. The length is `4294967295`.
- `ft_strmapi` / `ft_striteri` callbacks from fsoares: `add` is `(char)(i + c)`, `to_char_zero` writes `'0'`. The third catalog argument is the description string and is not passed to the function. war-machine `&mapi` / `&iter` swap case. The war-machine printer also checks that `strmapi` allocated a new string and that byte 11 is NUL.

`rand()` rows stay skipped. `utils.c` calls `srand((unsigned int)time(NULL))`. Those bytes were never saved. Do not invent a seed.

`sizeof(long)` is not a buffer. It is `ctypes.sizeof(ctypes.c_long)` (8 on this LP64 machine).

## What Skip still means

Skip is not a pass. The subject does not accept a wrong result. A skipped row has no input this process can run.

| Reason | Why it is still skipped |
| --- | --- |
| `not a direct input` | Fuzzer, speed, sandbox, generated loop, or a crash/guard helper with empty args. Crash rows are the inputs where libc itself crashes. That is undefined. The subject allows a crash only then. |
| `argument is a harness name` | The name is not one of the fills above. Often `rand()` or an old-function buffer. |
| `check is not a direct call` | Tripouille stored a C or C++ assertion, usually with empty args. |
| `not in libft.h` | The header does not declare it. A subject function is also one Fail. |
| `print wrapper is custom` | war-machine printed through a wrapper this tester did not rebuild. |
| `inputs are not separated` | The call was stored as one string and `args` is empty or the wrong length. |
| `no runner for this function yet` | An older function that is not in v19.2, such as `ft_putchar` or `ft_isblank`. |
| `null argument` | The call passes NULL and the subject does not define that case. |
| `fd is not 1 or 2` | The write goes somewhere other than stdout or stderr. |
| `count is too large to stage` | The size does not fit in a buffer this tester builds. |
| `no libc oracle` | Nothing stored and no libc twin for that function. |
| `oracle type is not handled` | The stored expected kind is not one `grade` compares. |

The guard helpers (`part2_guard_substr` and the rest) and `libc_crash_*` live in files that are not fully in this repo (`ub_match.c` is, the crash bodies are behind macros). They have empty `args`. Leaving them skipped matches the parse contract. Do not fake their inputs.

## Harness details that are easy to break

- Capture stdout and stderr with pipes around the call, then `dup2` back before the protocol `printf`. Otherwise the protocol bytes mix with the function's output.
- NULs are staged as a byte array plus a trailing NUL. Char arguments are the byte 0..255, not a sign-extended `char`.
- `emit_raw` writes a fixed length, so interior NULs survive. `emit_text` stops at the first NUL and is for C strings.
- `emit_pair` is `size:hex`. It is the strlcpy and strlcat return plus the buffer window.
- Children are a new session. On Python timeout the runner kills the process group.
- Prefer a completed result line over a later crash in `free`.
- The driver includes `libft.h` and is compiled as GNU C, not `-std=c99`. The subject forbids the student from putting `restrict` in their prototypes and from compiling their own code as C99. That constraint is on them, not on this driver.
- Large stack arrays (the 1024-byte `int[256]` memset) are fine.
- `subject_frees` and the subject callbacks are in every driver. The variable is marked unused. The compile line already passes `-Wno-unused-function`. A new unused static variable without that attribute fails `-Werror` on unrelated functions such as `ft_atoi`.

## Reference library

`/tmp/cc-holes-ref-libft` was extended so the new calls link. The header already declared the full subject. The C file originally implemented the string and stdio wrappers and not `memset`, `bzero`, `memcpy`, `memmove`, `strlcpy`, `strlcat`, `strmapi`, `striteri`, or the list functions. Those implementations were appended to `/tmp/cc-holes-ref-libft/ref.c`. They are a test double, not part of this repo. `strlcpy` and `strlcat` follow the OpenBSD rule: the return is the length they tried to create, and if no NUL is found inside `size` then `strlcat` returns `size + strlen(src)` and does not write.

`/tmp/cc-holes-bad` only breaks `ft_atoi`. It will not catch a bad `memset`.

## Problems already hit

- Textual was missing. Installed with `pip3 install --user textual`, which upgraded rich 14 to 15.
- Exa search wanted auth. GitHub code search returned 401. war-machine `main.c` URLs that were guessed 404'd. The files are in `../francinette-image` and now under `vendor/francinette/war-machine/`.
- The first TUI Enter did not open the path screen because the list was not focused and had no index.
- `Static.renderable` does not exist.
- The bad reference `return (0);` failed `make` with `-Werror=unused-parameter`. The fix there was `(void)str;`.
- A pipe into `awk` hid the tester's exit code. A make failure looked like a later success.
- The C parent did a blocking `read` after `poll` timed out and the suite hung. Read only when `poll` returns ready.
- `_pad_mem` treated `ft_substr(..., -1, -1)` as an enormous allocation. Only pad a `mem` buffer.
- `francinette-image` does not contain `utils.c`. Looking only at `test_memset.c` shows the name `mem` and not the fill. The fill is `0x11` in `reset()`.
- Building a C string with a real newline inside the generated quotes splits the literal. Escape `\n` in generated strings. Lengths that were hand-counted: `mem's adress was not returned\n` is 30, `dest's adress was not returned\n` is 31, the two `strmapi` diagnostics are 30. The apostrophe typo `adress` is in the original war-machine source. Keep it, or the stdout will not match.
- `ft_strlcpy` source arrays must include the terminating NUL. `memcpy` with an explicit count must not, or the count reads one byte too far.
- An empty-args crash row shares the function name `ft_memset`. `concretize` must ignore cases with no args or it indexes off the end.
- Passing a 256-byte expected buffer through the log is fine. `_show` truncates the displayed form at 48 characters. The comparison itself is exact.

## What is still open

- `ft_printf` and `get_next_line` have no runners. Do not start them until their tests are in scope. `get_next_line` has its own `lines` rules in `francinette-tests.md`, including `BUFFER_SIZE` and multi-fd groups.
- Sandbox, speed, fuzzer, generated, crash, and guard rows are still skipped. The subject cares about leaks and about crashes on defined inputs. The catalog rows for those do not contain the input.
- Tripouille list assertions are still skipped. The subject suite covers the basic contract, not every C++ check in that suite.
- `rand()` memory tests (`ft_memchr`, the memcpy repetition loop, `ft_strlen` random strings) have no saved bytes.
- There is no malloc interceptor, so a leak can still pass.
- The reference library is in `/tmp`. A future session should recreate it or vendor a small one if the numbers need to be reproduced.
- No git commit has been made for this work unless the user asks.
