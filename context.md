# 42_Holes context

Handoff as of 19 Nov 2026. Repo: `git@github.com:fathe4wiin/42_Holes.git`, branch `main`.

## What this is

A Python TUI that grades 42 projects by circle.

| Circle | Projects | Subject |
| --- | --- | --- |
| 00 | libft | v19.2. Lists are mandatory part 3. |
| 01 | get_next_line, ft_printf, push_swap | v14.3, v12.1, v1.2 |
| 02 | py-module-00 through py-module-04 | v3.0, v3.2, v3.0, v3.1, v3.0 |

Subjects live in `subjects/`. Python subjects are `subjects/python_modules/en.subject_py-module-0N.pdf`. `subjects/checker_linux` is the school's push_swap checker and must stay executable. More Python modules will be added to `PY_MODULES` in `cc_holes/py_run.py`. Circle 02 is its own screen so that list can grow to about 12.

`francinette-tests.json` (schema `francinette-tests/1`) is the catalog for libft and ft_printf. The subject wins when a stored case disagrees with it. push_swap is not in the catalog. get_next_line's catalog rows have no file bytes, so they are not replayed.

Tagline, exact, under the logo:

`a TUI project to test your 42 project, made by student for students`

Do not invent an author name. The logo is a 5-row block font in `cc_holes/guide.py`. Theme is dark red on black. Dependency is `textual>=8.2`. Verify the TUI with `App.run_test`, not a browser.

## Run

```sh
curl -fsSL https://raw.githubusercontent.com/fathe4wiin/42_Holes/main/run.sh | bash
curl -fsSL https://raw.githubusercontent.com/fathe4wiin/42_Holes/main/run.sh | bash -s -- ~/libft
```

`python3 holes.py` opens the TUI. `python3 holes.py /path` grades that folder. Exit 1 if any call failed, 2 on a build or setup error. A warning does not fail the run.

On this machine the compiler wrapper on `PATH` cannot find `cc1`, and `sys.executable` points at a Cursor AppImage. Grade with `/usr/bin` first and the pyenv interpreter. The Python runner launches `prefix/bin/python3`, not `sys.executable`.

```sh
PATH="/usr/bin:/bin:$PATH" /opt/pyenv/versions/3.13.1/bin/python3 holes.py /path
```

Needs Python 3 with pip, git, gcc, and make. `strlcpy`, `strlcat`, and `strnstr` retry the link with `-lbsd`. Python modules also want `flake8` on that interpreter. A missing flake8 is one warning.

## Screens

Home keys, all `priority=True`: `a` available tests, `g` guide, `c` credits, `q` quit. The menu is a `ListView`. It needs `focus()` and an index or Enter does nothing.

`a` opens the circle list. Enter on circle 00 or 01 opens that circle's projects, each row showing the subject version. Enter on circle 02 opens the Python-module window. Escape goes back one screen. Enter on a project opens the path screen.

libft, ft_printf, and push_swap want a Makefile. get_next_line wants `get_next_line.c` and `get_next_line.h` at the folder root. A Python module wants the exercise files in `ex0/`, `ex1/`, and so on. A copy at the folder root is also accepted.

`Static.content` is the text. There is no `renderable`.

## Results

Pass, Fail, Warn. `42_holes.log` in the project folder lists FAIL and WARN only. Leaks are not graded. There is no malloc hook.

Last full run of `cc-holes-ref-libft`: 875 pass, 0 fail, 0 warn. That tree calls libc on part 1 and libbsd for `strlcpy`, `strlcat`, and `strnstr`. `is*` returns 0 or 1. On this machine `strnstr(NULL, "a", 0)` returns. `strnstr(NULL, "a", 1)` segfaults. A libft that reads the haystack when the length is 0 fails that call.

## libft

Part 1 must match libc, including a crash. Both crashing is a pass. libc crashed and the student returned: warn. Student crashed and libc did not: fail. `isalpha` must return 0 or 1, not glibc's 1024. `strncmp` and `memcmp` use the sign. Part 2 and list calls the subject does not define: a crash is a warning, a return is a pass.

Named `mem` bytes come from `cc_holes/buffers.py`. The fills are copied in that file.

## ft_printf, get_next_line, push_swap

ft_printf v12.1 compares stdout and the return value with `printf`. Mandatory is bare `cspdiuxX%`. Bonus is `-0.` with a width, then `#`, `+`, and space. Bonus fails are still reported when mandatory is not perfect.

get_next_line v14.3 is compiled at `BUFFER_SIZE` 1 and 42. The newline stays on the line. A pipe whose write end stays open must return at the newline. A missing bonus is a warning.

push_swap v1.2: `subjects/checker_linux` must print `OK`. No arguments prints nothing. Errors are `Error\n` on stderr. Three or fewer numbers must also be the shortest sequence. `--bench` needs the disorder percent, the strategy name, and the complexity. 100 numbers under 2000 operations. 500 under 12000. A missing student checker is a warning.

## Python modules

Each exercise is one row. `input()` does not echo through a pipe, so the typed text is not required on the prompt line. The prompts and the printed results are.

- py-module-00 Growing Code v3.0. Exact text for the eight exercises. Exercise 6 needs `range` in the iterative file and a local call in the recursive file. Exercise 7 needs the typed signature. 60 days is not ready. 2 days does not need water.
- py-module-01 Code Cultivation v3.2. The demo text is not matched word for word. `Plant`, `show`, `grow`, `age`, the setters, `Flower`, `Tree`, `Vegetable`, `Seed`, a static method, a class method, a nested class, and one free function are.
- py-module-02 Garden Guardian v3.0. `input_temperature` accepts 0 and 40. 100 must say hot and 40. -50 must say cold and 0. `garden_operations(0..4)` raises `ValueError`, `ZeroDivisionError`, `FileNotFoundError`, `TypeError`, then returns. `PlantError` and `WaterError` inherit `GardenError`.
- py-module-03 Data Quest v3.1. The printed examples are the expected text, including the score lines and the inventory percentages. `get_player_pos` returns `(1.0, 2.5, 3.0)` after a bad line. Distances are 4.0311 and 4.9244.
- py-module-04 Data Archivist v3.0. A missing file reports an open error. Exercise 1 adds `#` to each line. Exercise 2 puts `[STDERR]` on stderr and must not call `input()`. `secure_archive` uses `with` and returns `(False, ...)` or `(True, text)`.

`flake8` runs on the `*.py` files. A violation is a fail. The module is detected from `ex0/` plus its first exercise file.

## Files

| Path | Role |
| --- | --- |
| `holes.py` | Launcher. |
| `cc_holes/app.py` | Screens. Circle list, then the project list or the Python window. |
| `cc_holes/py_run.py` | Python-module registry, versions, and graders. |
| `cc_holes/gnl_run.py` | get_next_line. |
| `cc_holes/push_swap.py` | push_swap. Sort oracle is `subjects/checker_linux`. |
| `cc_holes/runner.py` | make, libft, ft_printf, and `run_project`. |
| `cc_holes/catalog.py` | Loads the catalog. |
| `subjects/python_modules/` | The five Python subjects. |

## Constraint

Leaks are not graded. There is no malloc hook.
