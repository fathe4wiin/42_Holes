"""python -m cc_holes launches the UI. A path argument grades that project and prints the rows."""

import sys
from pathlib import Path

from cc_holes.app import HolesApp
from cc_holes.runner import Done, Log, Update, project_of, run_project


def cli(folder: str) -> int:
    root = Path(folder)
    name = project_of(root)
    header = {
        "ft_printf": "ft_printf.h",
        "get_next_line": "get_next_line.h",
        "push_swap": "push_swap",
    }.get(name, name if name.startswith("py-module-") else "libft.h")
    code = 0
    for event in run_project(name, root):
        if isinstance(event, Log):
            print(event.text)
        elif isinstance(event, Update):
            row = event.row
            print(
                f"{row.function:<18} pass {row.passed:<4} fail {row.failed:<4} "
                f"warn {row.warned:<4} {row.note}"
            )
        elif isinstance(event, Done):
            if event.error:
                print(event.error)
                return 2
            print(
                f"\npass {event.passed}  fail {event.failed}  warn {event.warned}"
            )
            if event.missing:
                print(f"missing from {header}: " + ", ".join(event.missing))
            if event.log_path:
                print(f"log: {event.log_path}")
            code = 1 if event.failed else 0
    return code


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        HolesApp().run()
        return 0
    if args[0] in {"-h", "--help"}:
        print("python3 holes.py")
        print("python3 holes.py /path/to/libft")
        print("python3 holes.py /path/to/ft_printf")
        print("python3 holes.py /path/to/get_next_line")
        print("python3 holes.py /path/to/push_swap")
        print("python3 holes.py /path/to/py-module-00")
        return 0
    return cli(args[0])


if __name__ == "__main__":
    raise SystemExit(main())
