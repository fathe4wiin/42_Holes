"""Grade the Python modules in subjects/python_modules.

Each module is one circle-02 project. Files may live in exN/ or at the folder
root. Output that the subject prints as an example is compared after stripping
each line. Behavior the subject leaves open is checked on the objects instead.
"""

import ast
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cc_holes.model import Outcome, build_row

_MARKER = "__CC_HOLES_JSON__"


@dataclass(frozen=True)
class PyModule:
    name: str
    title: str
    version: str
    marker: str


PY_MODULES = (
    PyModule("py-module-00", "Growing Code", "3.0", "ft_hello_garden.py"),
    PyModule("py-module-01", "Code Cultivation", "3.2", "ft_garden_intro.py"),
    PyModule("py-module-02", "Garden Guardian", "3.0", "ft_first_exception.py"),
    PyModule("py-module-03", "Data Quest", "3.1", "ft_command_quest.py"),
    PyModule("py-module-04", "Data Archivist", "3.0", "ft_ancient_text.py"),
)


def module_by_name(name: str) -> PyModule | None:
    for item in PY_MODULES:
        if item.name == name:
            return item
    return None


def detect_module(folder: Path) -> str | None:
    """Return the module id when a signature exercise file is in the folder."""
    found: list[str] = []
    for item in PY_MODULES:
        if _find(folder, "ex0", item.marker) is not None:
            found.append(item.name)
    if len(found) == 1:
        return found[0]
    return None


def _find(folder: Path, directory: str, filename: str) -> Path | None:
    for candidate in (folder / directory / filename, folder / filename):
        if candidate.is_file():
            return candidate
    return None


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _exact(text: str, wanted: list[str]) -> str | None:
    got = _lines(text)
    if got == wanted:
        return None
    shown = " | ".join(got[:6]) or "(empty)"
    return f"got {shown}"


def _missing(text: str, wanted: list[str]) -> str | None:
    for line in wanted:
        if line not in text:
            return f"missing {line}"
    return None


def _outcome(name: str, call: str, status: str, detail: str, part: str) -> Outcome:
    return Outcome(f"{part}-{call}", name, "subject", call, part, status, detail)


def _interpreter() -> str:
    """The Python that is running this tester.

    Cursor rewrites sys.executable to an AppImage that cannot start a child.
    prefix/bin/python3 is the real interpreter on this machine and on pyenv.
    """
    candidate = Path(sys.prefix) / "bin" / "python3"
    if candidate.is_file():
        return str(candidate)
    return sys.executable


def _run(
    argv: list[str],
    stdin: str = "",
    timeout: float = 4,
    cwd: Path | None = None,
) -> tuple[str | None, str, str, int]:
    try:
        proc = subprocess.run(
            argv,
            input=stdin.encode(),
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "timed out", "", "", 124
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    if proc.returncode < 0:
        return f"signal {-proc.returncode}", out, err, proc.returncode
    return None, out, err, proc.returncode


def _call(
    path: Path,
    func: str,
    args: tuple = (),
    stdin: str = "",
    timeout: float = 4,
) -> tuple[str | None, str, str]:
    code = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('student_mod', {str(path)!r})\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        f"getattr(mod, {func!r})(*{args!r})\n"
    )
    problem, out, err, code_rc = _run([_interpreter(), "-c", code], stdin, timeout, path.parent)
    if problem:
        return problem, out, err
    if code_rc != 0:
        tail = (err or out).strip().splitlines()
        return (tail[-1] if tail else f"exited {code_rc}"), out, err
    return None, out, err


def _probe(
    path: Path,
    body: str,
    stdin: str = "",
    timeout: float = 4,
) -> tuple[str | None, object, str, str]:
    code = (
        "import importlib.util, json, sys\n"
        f"spec = importlib.util.spec_from_file_location('student_mod', {str(path)!r})\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        f"{body}\n"
        f"print({_MARKER!r} + json.dumps(result, default=str))\n"
    )
    problem, out, err, code_rc = _run([_interpreter(), "-c", code], stdin, timeout, path.parent)
    if problem:
        return problem, None, out, err
    if code_rc != 0:
        tail = (err or out).strip().splitlines()
        return (tail[-1] if tail else f"exited {code_rc}"), None, out, err
    payload = None
    visible_lines: list[str] = []
    for line in out.splitlines():
        index = line.find(_MARKER)
        if index == -1:
            visible_lines.append(line)
            continue
        try:
            payload = json.loads(line[index + len(_MARKER):])
        except json.JSONDecodeError as exc:
            return f"probe result is not json ({exc})", None, out, err
        if line[:index]:
            visible_lines.append(line[:index])
    if payload is None:
        return "the probe printed no result", None, out, err
    visible = "\n".join(visible_lines)
    return None, payload, visible, err


def _contains(text: str, wanted: list[str], forbidden: tuple[str, ...] = ()) -> str | None:
    for line in wanted:
        if line not in text:
            return f"missing {line}"
    for line in forbidden:
        if line in text:
            return f"unexpected {line}"
    return None


def _grade_call(
    name: str,
    part: str,
    path: Path | None,
    func: str,
    wanted: list[str],
    args: tuple = (),
    stdin: str = "",
    contains: bool = False,
    forbidden: tuple[str, ...] = (),
) -> Outcome:
    call = f"{func}({', '.join(repr(arg) for arg in args)})"
    if path is None:
        return _outcome(name, call, "fail", "file was not found", part)
    problem, out, _err = _call(path, func, args, stdin)
    if problem:
        return _outcome(name, call, "fail", problem, part)
    why = _contains(out, wanted, forbidden) if contains else _exact(out, wanted)
    if why:
        return _outcome(name, call, "fail", why, part)
    return _outcome(name, call, "pass", "matches the subject", part)


def _script(
    name: str,
    part: str,
    path: Path | None,
    argv: list[str],
    stdin: str,
    check,
    timeout: float = 4,
) -> Outcome:
    call = path.name if path else "script"
    if argv:
        call += " " + " ".join(argv)
    if path is None:
        return _outcome(name, call, "fail", "file was not found", part)
    problem, out, err, rc = _run([_interpreter(), str(path), *argv], stdin, timeout, path.parent)
    if problem:
        return _outcome(name, call, "fail", problem, part)
    if rc != 0:
        tail = (err or out).strip().splitlines()
        return _outcome(name, call, "fail", tail[-1] if tail else f"exited {rc}", part)
    why = check(out, err)
    if why:
        return _outcome(name, call, "fail", why, part)
    return _outcome(name, call, "pass", "matches the subject", part)


def _source(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _tree(path: Path | None) -> ast.AST | None:
    text = _source(path)
    if not text:
        return None
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def _calls_local(path: Path | None) -> bool:
    tree = _tree(path)
    if tree is None:
        return False
    names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in names:
                return True
    return False


def _has_with(path: Path | None) -> bool:
    tree = _tree(path)
    return any(isinstance(node, ast.With) for node in ast.walk(tree)) if tree else False


def _calls_name(path: Path | None, name: str) -> bool:
    tree = _tree(path)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == name:
                return True
    return False


def _comp_counts(path: Path | None) -> tuple[int, int]:
    tree = _tree(path)
    if tree is None:
        return 0, 0
    lists = sum(isinstance(node, ast.ListComp) for node in ast.walk(tree))
    dicts = sum(isinstance(node, ast.DictComp) for node in ast.walk(tree))
    return lists, dicts


def _grade_00(folder: Path) -> list[tuple[str, str, list[Outcome]]]:
    name = "ft_hello_garden"
    rows: list[tuple[str, str, list[Outcome]]] = []
    hello = _find(folder, "ex0", "ft_hello_garden.py")
    rows.append((name, "ex0", [
        _grade_call(name, "ex0", hello, name, ["Hello, Garden Community!"]),
    ]))
    garden = _find(folder, "ex1", "ft_garden_name.py")
    rows.append(("ft_garden_name", "ex1", [
        _grade_call(
            "ft_garden_name", "ex1", garden, "ft_garden_name",
            ["Enter garden name:", "Garden: Community Garden", "Status: Growing well!"],
            stdin="Community Garden\n",
            contains=True,
        ),
    ]))
    area = _find(folder, "ex2", "ft_plot_area.py")
    rows.append(("ft_plot_area", "ex2", [
        _grade_call(
            "ft_plot_area", "ex2", area, "ft_plot_area",
            ["Enter length:", "Enter width:", "Plot area: 15"],
            stdin="5\n3\n",
            contains=True,
        ),
    ]))
    harvest = _find(folder, "ex3", "ft_harvest_total.py")
    rows.append(("ft_harvest_total", "ex3", [
        _grade_call(
            "ft_harvest_total", "ex3", harvest, "ft_harvest_total",
            ["Day 1 harvest:", "Day 2 harvest:", "Day 3 harvest:", "Total harvest: 16"],
            stdin="5\n8\n3\n",
            contains=True,
        ),
    ]))
    age = _find(folder, "ex4", "ft_plant_age.py")
    rows.append(("ft_plant_age", "ex4", [
        _grade_call(
            "ft_plant_age", "ex4", age, "ft_plant_age",
            ["Enter plant age in days:", "Plant is ready to harvest!"],
            stdin="75\n",
            contains=True,
            forbidden=("Plant needs more time to grow.",),
        ),
        _grade_call(
            "ft_plant_age", "ex4", age, "ft_plant_age",
            ["Enter plant age in days:", "Plant needs more time to grow."],
            stdin="60\n",
            contains=True,
            forbidden=("Plant is ready to harvest!",),
        ),
    ]))
    water = _find(folder, "ex5", "ft_water_reminder.py")
    rows.append(("ft_water_reminder", "ex5", [
        _grade_call(
            "ft_water_reminder", "ex5", water, "ft_water_reminder",
            ["Days since last watering:", "Water the plants!"],
            stdin="3\n",
            contains=True,
            forbidden=("Plants are fine",),
        ),
        _grade_call(
            "ft_water_reminder", "ex5", water, "ft_water_reminder",
            ["Days since last watering:", "Plants are fine"],
            stdin="2\n",
            contains=True,
            forbidden=("Water the plants!",),
        ),
    ]))
    iterative = _find(folder, "ex6", "ft_count_harvest_iterative.py")
    recursive = _find(folder, "ex6", "ft_count_harvest_recursive.py")
    count_wanted = [
        "Days until harvest:", "Day 1", "Day 2", "Day 3", "Harvest time!",
    ]
    count_rows = [
        _grade_call(
            "ft_count_harvest", "ex6", iterative, "ft_count_harvest_iterative",
            count_wanted, stdin="3\n", contains=True, forbidden=("Day 4",),
        ),
        _grade_call(
            "ft_count_harvest", "ex6", recursive, "ft_count_harvest_recursive",
            count_wanted, stdin="3\n", contains=True, forbidden=("Day 4",),
        ),
    ]
    if iterative and "range" not in _source(iterative):
        count_rows.append(_outcome(
            "ft_count_harvest", "iterative uses range", "fail",
            "the iterative file does not use range", "ex6",
        ))
    elif iterative:
        count_rows.append(_outcome(
            "ft_count_harvest", "iterative uses range", "pass", "range is used", "ex6",
        ))
    if recursive and not _calls_local(recursive):
        count_rows.append(_outcome(
            "ft_count_harvest", "recursive call", "fail",
            "the recursive file does not call one of its functions", "ex6",
        ))
    elif recursive:
        count_rows.append(_outcome(
            "ft_count_harvest", "recursive call", "pass", "a local function is called", "ex6",
        ))
    rows.append(("ft_count_harvest", "ex6", count_rows))
    seed = _find(folder, "ex7", "ft_seed_inventory.py")
    seed_rows = [
        _grade_call(
            "ft_seed_inventory", "ex7", seed, "ft_seed_inventory",
            ["Tomato seeds: 15 packets available"],
            ("tomato", 15, "packets"),
        ),
        _grade_call(
            "ft_seed_inventory", "ex7", seed, "ft_seed_inventory",
            ["Carrot seeds: 8 grams total"],
            ("carrot", 8, "grams"),
        ),
        _grade_call(
            "ft_seed_inventory", "ex7", seed, "ft_seed_inventory",
            ["Lettuce seeds: covers 12 square meters"],
            ("lettuce", 12, "area"),
        ),
        _grade_call(
            "ft_seed_inventory", "ex7", seed, "ft_seed_inventory",
            ["Unknown unit type"],
            ("rose", 1, "bags"),
        ),
    ]
    if seed is None:
        seed_rows.append(_outcome(
            "ft_seed_inventory", "type hints", "fail", "file was not found", "ex7",
        ))
    else:
        problem, payload, _out, _err = _probe(
            seed,
            "import inspect\n"
            "fn = mod.ft_seed_inventory\n"
            "sig = inspect.signature(fn)\n"
            "result = {\n"
            "  'params': [(name, str(param.annotation)) for name, param in sig.parameters.items()],\n"
            "  'return': str(sig.return_annotation),\n"
            "}\n",
        )
        hints_ok = False
        if problem is None and isinstance(payload, dict):
            params = payload.get("params")
            ret = str(payload.get("return"))
            hints_ok = (
                params == [["seed_type", "<class 'str'>"], ["quantity", "<class 'int'>"], ["unit", "<class 'str'>"]]
                or params == [["seed_type", "str"], ["quantity", "int"], ["unit", "str"]]
            ) and ret in {"<class 'NoneType'>", "None", "NoneType"}
        seed_rows.append(_outcome(
            "ft_seed_inventory", "type hints",
            "pass" if hints_ok else "fail",
            "signature matches the subject" if hints_ok else (problem or "type hints do not match the subject"),
            "ex7",
        ))
    rows.append(("ft_seed_inventory", "ex7", seed_rows))
    return rows


def _grade_01(folder: Path) -> list[tuple[str, str, list[Outcome]]]:
    rows: list[tuple[str, str, list[Outcome]]] = []
    intro = _find(folder, "ex0", "ft_garden_intro.py")
    text = _source(intro)

    def intro_check(out: str, _err: str) -> str | None:
        if "__name__" not in text or "__main__" not in text:
            return 'the file does not use if __name__ == "__main__"'
        if not _lines(out):
            return "the program printed nothing"
        return None

    rows.append(("ft_garden_intro", "ex0", [
        _script("ft_garden_intro", "ex0", intro, [], "", intro_check),
    ]))
    data = _find(folder, "ex1", "ft_garden_data.py")

    def data_check(out: str, _err: str) -> str | None:
        problem, payload, _visible, _error = _probe(
            data,
            "result = {'plant': hasattr(mod, 'Plant'), 'show': hasattr(getattr(mod, 'Plant', object), 'show')}\n",
        )
        if problem:
            return problem
        if not isinstance(payload, dict) or not payload.get("plant") or not payload.get("show"):
            return "Plant.show is missing"
        if len(_lines(out)) < 3:
            return "the program should display at least 3 plants"
        return None

    rows.append(("ft_garden_data", "ex1", [
        _script("ft_garden_data", "ex1", data, [], "", data_check),
    ]))
    growth = _find(folder, "ex2", "ft_plant_growth.py")

    def growth_check(out: str, _err: str) -> str | None:
        problem, payload, _visible, _error = _probe(
            growth,
            "plant = getattr(mod, 'Plant', None)\n"
            "result = {\n"
            "  'grow': callable(getattr(plant, 'grow', None)),\n"
            "  'age': callable(getattr(plant, 'age', None)),\n"
            "}\n",
        )
        if problem:
            return problem
        if not isinstance(payload, dict) or not payload.get("grow") or not payload.get("age"):
            return "Plant.grow and Plant.age are required"
        if not _lines(out):
            return "the program printed nothing"
        return None

    rows.append(("ft_plant_growth", "ex2", [
        _script("ft_plant_growth", "ex2", growth, [], "", growth_check),
    ]))
    factory = _find(folder, "ex3", "ft_plant_factory.py")

    def factory_check(out: str, _err: str) -> str | None:
        if len(_lines(out)) < 5:
            return "the program should display at least 5 plants"
        return None

    rows.append(("ft_plant_factory", "ex3", [
        _script("ft_plant_factory", "ex3", factory, [], "", factory_check),
    ]))
    security = _find(folder, "ex4", "ft_garden_security.py")
    secured = _source(security)

    def security_check(_out: str, _err: str) -> str | None:
        if "self._" not in secured:
            return "plant data is not stored on a protected _attribute"
        problem, payload, visible, _error = _probe(
            security,
            "plant = mod.Plant('Rose', 15, 10)\n"
            "plant.set_height(25)\n"
            "plant.set_age(30)\n"
            "before = (plant.get_height(), plant.get_age())\n"
            "plant.set_height(-1)\n"
            "plant.set_age(-5)\n"
            "after = (plant.get_height(), plant.get_age())\n"
            "result = {'before': before, 'after': after}\n",
        )
        if problem:
            return problem
        if not isinstance(payload, dict):
            return "set_height and set_age could not be called"
        before = payload.get("before")
        after = payload.get("after")
        if before != [25, 30] and before != [25.0, 30]:
            return f"updates did not stick: {before}"
        if after != before:
            return "a negative update changed the plant"
        if "negative" not in visible.lower() and "error" not in visible.lower():
            return "a negative update did not print an error"
        return None

    rows.append(("ft_garden_security", "ex4", [
        _script("ft_garden_security", "ex4", security, [], "", security_check),
    ]))
    types = _find(folder, "ex5", "ft_plant_types.py")

    def types_check(_out: str, _err: str) -> str | None:
        if "super(" not in _source(types):
            return "specialized plants do not call super()"
        problem, payload, _visible, _error = _probe(
            types,
            "def ok(cls, names):\n"
            "    return all(callable(getattr(cls, name, None)) for name in names)\n"
            "plant = getattr(mod, 'Plant', None)\n"
            "flower = getattr(mod, 'Flower', None)\n"
            "tree = getattr(mod, 'Tree', None)\n"
            "veg = getattr(mod, 'Vegetable', None)\n"
            "def child(cls):\n"
            "    return isinstance(cls, type) and isinstance(plant, type) and issubclass(cls, plant)\n"
            "result = {\n"
            "  'flower': child(flower),\n"
            "  'tree': child(tree),\n"
            "  'veg': child(veg),\n"
            "  'bloom': ok(flower or object, ['bloom']),\n"
            "  'shade': ok(tree or object, ['produce_shade']),\n"
            "}\n",
        )
        if problem:
            return problem
        if not isinstance(payload, dict) or not all(payload.get(key) for key in ("flower", "tree", "veg", "bloom", "shade")):
            return "Flower, Tree, and Vegetable must inherit Plant and add their methods"
        return None

    rows.append(("ft_plant_types", "ex5", [
        _script("ft_plant_types", "ex5", types, [], "", types_check),
    ]))
    analytics = _find(folder, "ex6", "ft_garden_analytics.py")

    def analytics_check(_out: str, _err: str) -> str | None:
        problem, payload, _visible, _error = _probe(
            analytics,
            "import inspect\n"
            "plant = getattr(mod, 'Plant', object)\n"
            "flower = getattr(mod, 'Flower', object)\n"
            "seed = getattr(mod, 'Seed', object)\n"
            "statics = [name for name, value in vars(plant).items() if isinstance(value, staticmethod)]\n"
            "classes = [name for name, value in vars(plant).items() if isinstance(value, classmethod)]\n"
            "nested = [name for name, value in vars(plant).items() if isinstance(value, type)]\n"
            "functions = [name for name, value in vars(mod).items() if inspect.isfunction(value)]\n"
            "result = {\n"
            "  'static': bool(statics),\n"
            "  'klass': bool(classes),\n"
            "  'nested': bool(nested),\n"
            "  'seed': issubclass(seed, flower) if isinstance(seed, type) and isinstance(flower, type) else False,\n"
            "  'free': bool(functions),\n"
            "}\n",
        )
        if problem:
            return problem
        if not isinstance(payload, dict):
            return "the analytics classes could not be inspected"
        if not payload.get("static") or not payload.get("klass"):
            return "Plant needs a static method and a class method"
        if not payload.get("nested"):
            return "Plant needs a nested class for its statistics"
        if not payload.get("seed"):
            return "Seed must inherit Flower"
        if not payload.get("free"):
            return "a function outside the classes must display the statistics"
        return None

    rows.append(("ft_garden_analytics", "ex6", [
        _script("ft_garden_analytics", "ex6", analytics, [], "", analytics_check),
    ]))
    return rows


def _grade_02(folder: Path) -> list[tuple[str, str, list[Outcome]]]:
    rows: list[tuple[str, str, list[Outcome]]] = []
    first = _find(folder, "ex0", "ft_first_exception.py")

    def temperature(value: str) -> tuple[str | None, object]:
        if first is None:
            return "file was not found", None
        return _probe(first, f"result = mod.input_temperature({value!r})\n")[:2]

    outcomes: list[Outcome] = []
    problem, payload = temperature("25")
    outcomes.append(_outcome(
        "ft_first_exception", "input_temperature('25')",
        "fail" if problem or payload != 25 else "pass",
        problem or ("25" if payload == 25 else f"returned {payload}"),
        "ex0",
    ))
    problem, payload = _probe(
        first,
        "try:\n"
        "    mod.input_temperature('abc')\n"
        "    result = 'returned'\n"
        "except Exception as exc:\n"
        "    result = type(exc).__name__\n",
    )[:2] if first else ("file was not found", None)
    outcomes.append(_outcome(
        "ft_first_exception", "input_temperature('abc')",
        "pass" if payload not in {None, "returned"} else "fail",
        "raises" if payload not in {None, "returned"} else (problem or "did not raise"),
        "ex0",
    ))

    def first_script(out: str, _err: str) -> str | None:
        if "25" not in out or "abc" not in out:
            return "test_temperature did not show both inputs"
        return None

    outcomes.append(_script("ft_first_exception", "ex0", first, [], "", first_script))
    rows.append(("ft_first_exception", "ex0", outcomes))

    raised = _find(folder, "ex1", "ft_raise_exception.py")
    range_rows: list[Outcome] = []
    for value, ok in (("0", True), ("40", True), ("25", True), ("100", False), ("-50", False)):
        if raised is None:
            range_rows.append(_outcome("ft_raise_exception", f"input_temperature({value})", "fail", "file was not found", "ex1"))
            continue
        problem, payload, _out, _err = _probe(
            raised,
            "try:\n"
            f"    result = {{'ok': mod.input_temperature({value!r})}}\n"
            "except Exception as exc:\n"
            "    result = {'error': str(exc)}\n",
        )
        if problem:
            range_rows.append(_outcome("ft_raise_exception", f"input_temperature({value})", "fail", problem, "ex1"))
            continue
        if not isinstance(payload, dict):
            range_rows.append(_outcome("ft_raise_exception", f"input_temperature({value})", "fail", "no result", "ex1"))
            continue
        if ok:
            good = payload.get("ok") == int(value)
            range_rows.append(_outcome(
                "ft_raise_exception", f"input_temperature({value})",
                "pass" if good else "fail",
                "accepted" if good else f"returned {payload}",
                "ex1",
            ))
            continue
        message = str(payload.get("error", ""))
        if value == "100":
            good = "hot" in message.lower() and "40" in message
        else:
            good = "cold" in message.lower() and "0" in message
        range_rows.append(_outcome(
            "ft_raise_exception", f"input_temperature({value})",
            "pass" if good else "fail",
            message or "did not raise",
            "ex1",
        ))
    range_rows.append(_script(
        "ft_raise_exception", "ex1", raised, [], "",
        lambda out, _err: None if "100" in out and "-50" in out else "test_temperature skipped an extreme value",
    ))
    rows.append(("ft_raise_exception", "ex1", range_rows))

    different = _find(folder, "ex2", "ft_different_errors.py")
    expected = ["ValueError", "ZeroDivisionError", "FileNotFoundError", "TypeError", "ok"]
    if different is None:
        kind_result: object = None
        kind_problem = "file was not found"
    else:
        kind_problem, kind_result, _out, _err = _probe(
            different,
            "found = []\n"
            "for number in range(5):\n"
            "    try:\n"
            "        mod.garden_operations(number)\n"
            "        found.append('ok')\n"
            "    except Exception as exc:\n"
            "        found.append(type(exc).__name__)\n"
            "result = found\n",
        )
    kind_ok = kind_result == expected
    rows.append(("ft_different_errors", "ex2", [
        _outcome(
            "ft_different_errors", "garden_operations(0..4)",
            "pass" if kind_ok else "fail",
            "the five cases match" if kind_ok else (kind_problem or f"got {kind_result}"),
            "ex2",
        ),
        _script(
            "ft_different_errors", "ex2", different, [], "",
            lambda out, _err: None if "ValueError" in out and "TypeError" in out else "the demo did not show the error types",
        ),
    ]))

    custom = _find(folder, "ex3", "ft_custom_errors.py")
    if custom is None:
        custom_problem, custom_result = "file was not found", None
    else:
        custom_problem, custom_result, _out, _err = _probe(
            custom,
            "plant = mod.PlantError()\n"
            "water = mod.WaterError()\n"
            "caught = []\n"
            "for exc in (mod.PlantError('tomato'), mod.WaterError('tank')):\n"
            "    try:\n"
            "        raise exc\n"
            "    except mod.GardenError:\n"
            "        caught.append(True)\n"
            "result = {\n"
            "  'plant_base': issubclass(mod.PlantError, mod.GardenError),\n"
            "  'water_base': issubclass(mod.WaterError, mod.GardenError),\n"
            "  'garden_base': issubclass(mod.GardenError, Exception),\n"
            "  'plant_msg': str(plant),\n"
            "  'water_msg': str(water),\n"
            "  'caught': caught,\n"
            "}\n",
        )
    custom_ok = (
        isinstance(custom_result, dict)
        and custom_result.get("plant_base")
        and custom_result.get("water_base")
        and custom_result.get("garden_base")
        and custom_result.get("caught") == [True, True]
        and str(custom_result.get("plant_msg")) not in {"", "PlantError"}
        and str(custom_result.get("water_msg")) not in {"", "WaterError"}
    )
    rows.append(("ft_custom_errors", "ex3", [
        _outcome(
            "ft_custom_errors", "GardenError family",
            "pass" if custom_ok else "fail",
            "inheritance and default messages work" if custom_ok else (custom_problem or f"got {custom_result}"),
            "ex3",
        ),
    ]))

    final = _find(folder, "ex4", "ft_finally_block.py")

    def water_check(out: str, _err: str) -> str | None:
        if not _has_with(final) and "finally" not in _source(final):
            return "cleanup is not in a finally block"
        if final is None:
            return "file was not found"
        problem, payload, _visible, _error = _probe(
            final,
            "ok = None\n"
            "bad = None\n"
            "try:\n"
            "    mod.water_plant('Tomato')\n"
            "    ok = True\n"
            "except Exception as exc:\n"
            "    ok = type(exc).__name__\n"
            "try:\n"
            "    mod.water_plant('lettuce')\n"
            "    bad = 'returned'\n"
            "except Exception as exc:\n"
            "    bad = type(exc).__name__\n"
            "result = {'ok': ok, 'bad': bad}\n",
        )
        if problem:
            return problem
        if not isinstance(payload, dict) or payload.get("ok") is not True:
            return "water_plant('Tomato') should succeed"
        if payload.get("bad") not in {"PlantError", "GardenError"}:
            return "a lowercase plant name must raise PlantError"
        closing = sum(1 for line in _lines(out) if "clos" in line.lower())
        if closing < 2:
            return "the watering system was not closed on both the success and the error path"
        return None

    rows.append(("ft_finally_block", "ex4", [
        _script("ft_finally_block", "ex4", final, [], "", water_check),
    ]))
    return rows


def _grade_03(folder: Path) -> list[tuple[str, str, list[Outcome]]]:
    rows: list[tuple[str, str, list[Outcome]]] = []
    quest = _find(folder, "ex0", "ft_command_quest.py")

    def quest_lines(out: str, wanted_tail: list[str]) -> str | None:
        got = _lines(out)
        if len(got) < 2 or got[0] != "=== Command Quest ===":
            return "the header is missing"
        if not got[1].startswith("Program name:") or not got[1].endswith("ft_command_quest.py"):
            return got[1] if len(got) > 1 else "program name is missing"
        if got[2:] != wanted_tail:
            return "got " + " | ".join(got[2:8])
        return None

    rows.append(("ft_command_quest", "ex0", [
        _script("ft_command_quest", "ex0", quest, [], "", lambda out, err: quest_lines(out, ["No arguments provided!", "Total arguments: 1"])),
        _script(
            "ft_command_quest", "ex0", quest, ["hello", "world", "42"], "",
            lambda out, err: quest_lines(out, [
                "Arguments received: 3", "Argument 1: hello", "Argument 2: world",
                "Argument 3: 42", "Total arguments: 4",
            ]),
        ),
    ]))
    scores = _find(folder, "ex1", "ft_score_analytics.py")
    rows.append(("ft_score_analytics", "ex1", [
        _script(
            "ft_score_analytics", "ex1", scores,
            ["1500", "2300", "1800", "2100", "1950"], "",
            lambda out, err: _exact(out, [
                "=== Player Score Analytics ===",
                "Scores processed: [1500, 2300, 1800, 2100, 1950]",
                "Total players: 5", "Total score: 9650", "Average score: 1930.0",
                "High score: 2300", "Low score: 1500", "Score range: 800",
            ]),
        ),
        _script(
            "ft_score_analytics", "ex1", scores, [], "",
            lambda out, err: _missing(out, [
                "=== Player Score Analytics ===",
                "No scores provided. Usage: python3 ft_score_analytics.py <score1> <score2> ...",
            ]),
        ),
        _script(
            "ft_score_analytics", "ex1", scores, ["1500", "nope", "10"], "",
            lambda out, err: _missing(out, [
                "Invalid parameter: 'nope'",
                "Scores processed: [1500, 10]",
                "Total players: 2",
                "Average score: 755.0",
            ]),
        ),
    ]))
    coords = _find(folder, "ex2", "ft_coordinate_system.py")
    coord_in = "hello world\n1.0 , 2.5, 3.0\n4,abc,5\n4,5,6\n"
    if coords is None:
        pos_problem, pos_result = "file was not found", None
    else:
        pos_problem, pos_result, _out, _err = _probe(
            coords,
            "result = list(mod.get_player_pos())\n",
            "hello world\n1.0 , 2.5, 3.0\n",
        )
    pos_ok = pos_result == [1.0, 2.5, 3.0]
    rows.append(("ft_coordinate_system", "ex2", [
        _outcome(
            "ft_coordinate_system", "get_player_pos()",
            "pass" if pos_ok else "fail",
            "(1.0, 2.5, 3.0)" if pos_ok else (pos_problem or f"got {pos_result}"),
            "ex2",
        ),
        _script(
            "ft_coordinate_system", "ex2", coords, [], coord_in,
            lambda out, err: _missing(out, [
                "Invalid syntax",
                "Got a first tuple: (1.0, 2.5, 3.0)",
                "Distance to center: 4.0311",
                "Error on parameter 'abc': could not convert string to float: 'abc'",
                "Distance between the 2 sets of coordinates: 4.9244",
            ]),
            timeout=6,
        ),
    ]))
    achievements = _find(folder, "ex3", "ft_achievement_tracker.py")
    if achievements is None:
        set_problem, set_result = "file was not found", None
    else:
        set_problem, set_result, _out, _err = _probe(
            achievements,
            "value = mod.gen_player_achievements()\n"
            "result = {'type': type(value).__name__, 'ok': all(isinstance(item, str) for item in value)}\n",
        )
    set_ok = isinstance(set_result, dict) and set_result.get("type") == "set" and set_result.get("ok") is True
    rows.append(("ft_achievement_tracker", "ex3", [
        _outcome(
            "ft_achievement_tracker", "gen_player_achievements()",
            "pass" if set_ok else "fail",
            "returns a set of strings" if set_ok else (set_problem or f"got {set_result}"),
            "ex3",
        ),
        _script(
            "ft_achievement_tracker", "ex3", achievements, [], "",
            lambda out, err: None if "Achievement" in out else "the tracker printed no achievement report",
            timeout=6,
        ),
    ]))
    inventory = _find(folder, "ex4", "ft_inventory_system.py")
    rows.append(("ft_inventory_system", "ex4", [
        _script(
            "ft_inventory_system", "ex4", inventory,
            ["sword:1", "potion:5", "shield:2", "armor:3", "helmet:1", "sword:2", "hello", "key:value"],
            "",
            lambda out, err: _missing(out, [
                "Redundant item 'sword' - discarding",
                "Error - invalid parameter 'hello'",
                "Quantity error for 'key': invalid literal for int() with base 10: 'value'",
                "Got inventory: {'sword': 1, 'potion': 5, 'shield': 2, 'armor': 3, 'helmet': 1}",
                "Item list: ['sword', 'potion', 'shield', 'armor', 'helmet']",
                "Total quantity of the 5 items: 12",
                "Item sword represents 8.3%",
                "Item potion represents 41.7%",
                "Item shield represents 16.7%",
                "Item armor represents 25.0%",
                "Item helmet represents 8.3%",
                "Item most abundant: potion with quantity 5",
                "Item least abundant: sword with quantity 1",
                "Updated inventory: {'sword': 1, 'potion': 5, 'shield': 2, 'armor': 3, 'helmet': 1, 'magic_item': 1}",
            ]),
        ),
    ]))
    stream = _find(folder, "ex5", "ft_data_stream.py")
    if stream is None:
        gen_problem, gen_result = "file was not found", None
    else:
        gen_problem, gen_result, _out, _err = _probe(
            stream,
            "import inspect\n"
            "event = next(mod.gen_event())\n"
            "pool = [('a', 'run'), ('b', 'eat'), ('c', 'sleep')]\n"
            "consumed = list(mod.consume_event(pool))\n"
            "result = {\n"
            "  'gen': inspect.isgeneratorfunction(mod.gen_event),\n"
            "  'consume': inspect.isgeneratorfunction(mod.consume_event),\n"
            "  'event': list(event),\n"
            "  'left': pool,\n"
            "  'got': len(consumed),\n"
            "}\n",
        )
    gen_ok = (
        isinstance(gen_result, dict)
        and gen_result.get("gen")
        and gen_result.get("consume")
        and gen_result.get("left") == []
        and gen_result.get("got") == 3
        and isinstance(gen_result.get("event"), list)
        and len(gen_result.get("event")) == 2
    )
    rows.append(("ft_data_stream", "ex5", [
        _outcome(
            "ft_data_stream", "gen_event / consume_event",
            "pass" if gen_ok else "fail",
            "generators yield events and empty the list" if gen_ok else (gen_problem or f"got {gen_result}"),
            "ex5",
        ),
    ]))
    alchemy = _find(folder, "ex6", "ft_data_alchemist.py")
    lists, dicts = _comp_counts(alchemy)

    def alchemy_check(out: str, _err: str) -> str | None:
        if lists < 2 or dicts < 2:
            return f"need two list comprehensions and two dict comprehensions, found {lists} and {dicts}"
        if not _lines(out):
            return "the program printed nothing"
        return None

    rows.append(("ft_data_alchemist", "ex6", [
        _script("ft_data_alchemist", "ex6", alchemy, [], "", alchemy_check),
    ]))
    return rows


def _grade_04(folder: Path) -> list[tuple[str, str, list[Outcome]]]:
    rows: list[tuple[str, str, list[Outcome]]] = []
    ancient = _find(folder, "ex0", "ft_ancient_text.py")
    fragment = "alpha\nbeta\n"
    with tempfile.TemporaryDirectory(prefix="cc-holes-py04-") as temporary:
        work = Path(temporary)
        source = work / "ancient_fragment.txt"
        source.write_text(fragment, encoding="utf-8")
        locked = work / "locked.txt"
        locked.write_text("secret\n", encoding="utf-8")
        locked.chmod(0)
        readable = False
        try:
            locked.read_text(encoding="utf-8")
            readable = True
        except OSError:
            readable = False

        def usage(out: str, err: str) -> str | None:
            text = out + "\n" + err
            if "Usage:" not in text or "ft_ancient_text.py" not in text:
                return "usage line is missing"
            return None

        def missing_file(out: str, _err: str) -> str | None:
            if "Error opening file" not in out or "foo" not in out:
                return "a missing file did not report an open error"
            return None

        def denied(out: str, err: str) -> str | None:
            if readable:
                return None
            text = out + err
            if "Error opening file" not in text or "locked.txt" not in text:
                return "an unreadable file did not report an open error"
            return None

        def recovered(out: str, _err: str) -> str | None:
            if "alpha" not in out or "beta" not in out or "closed" not in out.lower():
                return "the file contents were not shown and closed"
            if "=== " not in out:
                return "the recovery header is missing"
            return None

        ancient_rows = [
            _script("ft_ancient_text", "ex0", ancient, [], "", usage),
            _script("ft_ancient_text", "ex0", ancient, ["foo"], "", missing_file),
            _script("ft_ancient_text", "ex0", ancient, [str(source)], "", recovered),
        ]
        if readable:
            ancient_rows.append(_outcome(
                "ft_ancient_text", "unreadable file", "warn",
                "this account can read a mode 000 file, so that case is not graded",
                "ex0",
            ))
        else:
            ancient_rows.append(_script(
                "ft_ancient_text", "ex0", ancient, [str(locked)], "", denied,
            ))
        rows.append(("ft_ancient_text", "ex0", ancient_rows))

        archive = _find(folder, "ex1", "ft_archive_creation.py")
        saved = work / "saved.txt"

        def transformed(out: str, _err: str) -> str | None:
            if "alpha#" not in out or "beta#" not in out:
                return "each line should gain a trailing #"
            if "Not saving" not in out:
                return "an empty file name should not save"
            if "Preservation" not in out:
                return "the preservation header is missing"
            return None

        def wrote(out: str, _err: str) -> str | None:
            if not saved.is_file():
                return "the new file was not created"
            body = saved.read_text(encoding="utf-8", errors="replace")
            if "alpha#" not in body or "beta#" not in body:
                return "the saved file does not contain the transformed lines"
            if "Saving data" not in out:
                return "the program did not say it was saving"
            return None

        rows.append(("ft_archive_creation", "ex1", [
            _script("ft_archive_creation", "ex1", archive, [str(source)], "\n", transformed),
            _script("ft_archive_creation", "ex1", archive, [str(source)], f"{saved}\n", wrote),
        ]))

        streams = _find(folder, "ex2", "ft_stream_management.py")

        def stream_error(out: str, err: str) -> str | None:
            if _calls_name(streams, "input"):
                return "this exercise reads the filename without input()"
            if "[STDERR]" not in err:
                return "errors go to stderr with a [STDERR] prefix"
            if "[STDERR]" in out or "No such file" in out:
                return "the open error was printed on stdout"
            return None

        def stream_save(out: str, err: str) -> str | None:
            if "[STDERR]" not in err or "locked.txt" not in err:
                return "a failed save must report the error on stderr"
            if "No such file" in out or "Permission" in out:
                return "the save error was printed on stdout"
            return None

        stream_rows = [
            _script("ft_stream_management", "ex2", streams, ["foo"], "", stream_error),
        ]
        if not readable:
            stream_rows.append(_script(
                "ft_stream_management", "ex2", streams, [str(source)], f"{locked}\n", stream_save,
            ))
        rows.append(("ft_stream_management", "ex2", stream_rows))
        locked.chmod(0o644)

    vault = _find(folder, "ex3", "ft_vault_security.py")
    if vault is None:
        vault_problem, vault_result = "file was not found", None
    else:
        with tempfile.TemporaryDirectory(prefix="cc-holes-vault-") as temporary:
            work = Path(temporary)
            good = work / "note.txt"
            good.write_text(fragment, encoding="utf-8")
            dest = work / "copy.txt"
            vault_problem, vault_result, _out, _err = _probe(
                vault,
                "read_bad = mod.secure_archive('/no/such/cc-holes-file')\n"
                f"read_ok = mod.secure_archive({str(good)!r})\n"
                "wrote = None\n"
                "for mode in ('w', 'write', 1):\n"
                "    try:\n"
                f"        wrote = mod.secure_archive({str(dest)!r}, mode, 'gamma\\n')\n"
                "        break\n"
                "    except TypeError:\n"
                "        continue\n"
                "result = {\n"
                "  'bad': list(read_bad) if isinstance(read_bad, tuple) else str(read_bad),\n"
                "  'ok': list(read_ok) if isinstance(read_ok, tuple) else str(read_ok),\n"
                "  'wrote': list(wrote) if isinstance(wrote, tuple) else str(wrote),\n"
                f"  'body': __import__('pathlib').Path({str(dest)!r}).read_text() if __import__('pathlib').Path({str(dest)!r}).is_file() else '',\n"
                f"  'with': {str(_has_with(vault))},\n"
                "}\n",
            )
    vault_ok = False
    vault_detail = vault_problem or f"got {vault_result}"
    if isinstance(vault_result, dict):
        bad = vault_result.get("bad")
        ok = vault_result.get("ok")
        wrote = vault_result.get("wrote")
        vault_ok = (
            vault_result.get("with") is True
            and isinstance(bad, list) and bad and bad[0] is False
            and isinstance(ok, list) and ok and ok[0] is True and "alpha" in str(ok[1])
            and isinstance(wrote, list) and wrote and wrote[0] is True
            and "gamma" in str(vault_result.get("body"))
        )
        if not vault_result.get("with"):
            vault_detail = "secure_archive must use a with statement"
        elif not vault_ok:
            vault_detail = f"got {vault_result}"
        else:
            vault_detail = "read and write go through the context manager"
    rows.append(("ft_vault_security", "ex3", [
        _outcome(
            "ft_vault_security", "secure_archive()",
            "pass" if vault_ok else "fail",
            vault_detail,
            "ex3",
        ),
    ]))
    return rows


_GRADERS = {
    "py-module-00": _grade_00,
    "py-module-01": _grade_01,
    "py-module-02": _grade_02,
    "py-module-03": _grade_03,
    "py-module-04": _grade_04,
}


def _style(folder: Path, name: str) -> list[Outcome]:
    files = sorted(path for path in folder.rglob("*.py") if "42_holes" not in path.name)
    if not files:
        return [_outcome(name, "flake8", "fail", "no Python files were found", "style")]
    problem, out, err, rc = _run(
        [_interpreter(), "-m", "flake8", *[str(path) for path in files]],
        timeout=20,
        cwd=folder,
    )
    if problem is None and rc != 0 and "No module named flake8" in (err + out):
        return [_outcome(name, "flake8", "warn", "flake8 is not installed, so style is not graded", "style")]
    if problem:
        return [_outcome(name, "flake8", "warn", problem, "style")]
    if rc == 0:
        return [_outcome(name, "flake8", "pass", "flake8 is clean", "style")]
    detail = "\n".join((out or err).splitlines()[:4]) or f"exited {rc}"
    return [_outcome(name, "flake8", "fail", detail, "style")]


def run_py_module(name: str, root: Path, control=None):
    """Yield the same events as the libft run."""
    from cc_holes.runner import Done, Log, RunControl, Update, _blank_done, _save_log

    control = control or RunControl()
    item = module_by_name(name)
    if item is None:
        yield _blank_done("This runner is not built yet.")
        return
    folder = root.expanduser()
    if not folder.is_absolute():
        folder = Path.cwd() / folder
    if not folder.is_dir():
        yield _blank_done("That path is not a folder.")
        return
    grader = _GRADERS.get(name)
    if grader is None:
        yield _blank_done("This runner is not built yet.")
        return
    yield Log(f"{item.title} · subject v{item.version}")
    passed = failed = warned = 0
    logged: list[tuple[str, list[Outcome]]] = []
    groups = grader(folder)
    groups.append(("flake8", "style", _style(folder, "flake8")))
    for function, part, outcomes in groups:
        if control.cancel.is_set():
            yield _blank_done("Stopped.")
            return
        row = build_row(function, outcomes, True, part=part)
        passed += row.passed
        failed += row.failed
        warned += row.warned
        logged.append((function, outcomes))
        yield Update(row)
    log_path, log_error = _save_log(folder, logged)
    if log_error:
        yield Log(f"Could not write 42_holes.log: {log_error}")
    yield Done(passed, failed, 0, 0, [], None, log_path, warned)
