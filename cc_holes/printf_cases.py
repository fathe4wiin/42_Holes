"""ft_printf calls. Subject v12.1 wins when the catalog still treats flags as mandatory."""

import json
from collections import Counter

from cc_holes.catalog import load_catalog, project_tests
from cc_holes.model import SPECS, Bound, BoundArg, parse_expr

# Bare cspdiuxX% is mandatory. Flags and a field width are the bonus.
ROW_PART: dict[str, str] = {
    "ft_printf text": "mandatory",
    "ft_printf %c": "mandatory",
    "ft_printf %s": "mandatory",
    "ft_printf %p": "mandatory",
    "ft_printf %d": "mandatory",
    "ft_printf %i": "mandatory",
    "ft_printf %u": "mandatory",
    "ft_printf %x": "mandatory",
    "ft_printf %X": "mandatory",
    "ft_printf %%": "mandatory",
    "ft_printf mix": "mandatory",
    "ft_printf -0.": "bonus",
    "ft_printf #+": "bonus",
}
ROW_ORDER = tuple(ROW_PART)

_MAX_FORMATS = 24
_MAX_EXTRA = 8
_SPEC = SPECS["ft_printf"]
_BAD = object()


class _Local:
    pass


LOCAL = _Local()

_SUBJECT: tuple[tuple[str, str, list], ...] = (
    ("text-empty", "", []),
    ("text-hello", "hello", []),
    ("text-nl", "a\nb", []),
    ("c-A", "%c", [65]),
    ("c-nul", "%c", [0]),
    ("c-127", "%c", [127]),
    ("c-128", "%c", [128]),
    ("c-255", "%c", [255]),
    ("c-256", "%c", [256]),
    ("c-neg", "%c", [-1]),
    ("s-hello", "%s", ["hello"]),
    ("s-empty", "%s", [""]),
    ("s-null", "%s", [None]),
    ("p-null", "%p", [None]),
    ("p-one", "%p", [1]),
    ("p-neg", "%p", [-1]),
    ("p-hex", "%p", [0xABC]),
    ("p-local", "%p", [LOCAL]),
    ("d-zero", "%d", [0]),
    ("d-neg", "%d", [-1]),
    ("d-one", "%d", [1]),
    ("d-42", "%d", [42]),
    ("d-m42", "%d", [-42]),
    ("d-max", "%d", [2147483647]),
    ("d-min", "%d", [-2147483648]),
    ("i-zero", "%i", [0]),
    ("i-neg", "%i", [-1]),
    ("i-max", "%i", [2147483647]),
    ("i-min", "%i", [-2147483648]),
    ("u-zero", "%u", [0]),
    ("u-one", "%u", [1]),
    ("u-42", "%u", [42]),
    ("u-max", "%u", [4294967295]),
    ("u-neg", "%u", [-1]),
    ("x-zero", "%x", [0]),
    ("x-ten", "%x", [10]),
    ("x-255", "%x", [255]),
    ("x-abc", "%x", [0x1234ABCD]),
    ("x-max", "%x", [4294967295]),
    ("x-neg", "%x", [-1]),
    ("X-zero", "%X", [0]),
    ("X-255", "%X", [255]),
    ("X-abc", "%X", [0x1234ABCD]),
    ("X-max", "%X", [4294967295]),
    ("X-neg", "%X", [-1]),
    ("pct", "%%", []),
    ("pct-two", "%%%%", []),
    ("pct-text", "a%%b%%c", []),
    ("mix-dsx", "%d %s %x", [42, "ok", 255]),
    ("mix-nul", "%c%s", [0, "Z"]),
    ("mix-spd", "%s %p %d", ["a", 1, -2]),
    ("mix-ic", "n=%i c=%c", [7, 65]),
    ("w-5d", "%5d", [42]),
    ("w-5d-neg", "%5d", [-42]),
    ("z-05d", "%05d", [42]),
    ("z-05d-neg", "%05d", [-42]),
    ("left-5d", "%-5d", [42]),
    ("left-5d-neg", "%-5d", [-42]),
    ("prec-5d", "%.5d", [42]),
    ("prec-0d-zero", "%.0d", [0]),
    ("prec-0d-one", "%.0d", [1]),
    ("w-prec-neg", "%10.5d", [-42]),
    ("z-min", "%08d", [-2147483648]),
    ("w-s", "%5s", ["ab"]),
    ("left-s", "%-5s", ["ab"]),
    ("prec-s", "%.2s", ["hello"]),
    ("prec-0s", "%.0s", ["hello"]),
    ("w-s-null", "%5s", [None]),
    ("w-c", "%5c", [65]),
    ("left-c", "%-5c", [65]),
    ("w-pct", "%5%", []),
    ("z-x", "%05x", [42]),
    ("w-p", "%10p", [0xABC]),
    ("left-p", "%-10p", [0xABC]),
    ("star-d", "%*d", [5, 42]),
    ("star-neg", "%*d", [-5, 42]),
    ("star-s", "%.*s", [2, "hello"]),
    ("star-both", "%*.*d", [8, 3, 42]),
    ("left-prec-s", "%-10.4s", ["hello"]),
    ("zero-left", "%0-5d", [42]),
    ("prec-empty", "%.s", ["hello"]),
    ("w-small", "%3d", [12345]),
    ("plus-pos", "%+d", [42]),
    ("plus-neg", "%+d", [-42]),
    ("plus-zero", "%+d", [0]),
    ("space-pos", "% d", [42]),
    ("space-neg", "% d", [-42]),
    ("space-zero", "% d", [0]),
    ("hash-x-zero", "%#x", [0]),
    ("hash-x", "%#x", [42]),
    ("hash-x-255", "%#x", [255]),
    ("hash-X-zero", "%#X", [0]),
    ("hash-X", "%#X", [42]),
    ("plus-width", "%+5d", [42]),
    ("plus-width-neg", "%+5d", [-42]),
    ("space-width", "% 5d", [42]),
    ("hash-pad", "%#08x", [42]),
    ("hash-plus", "%#+x", [42]),
    ("plus-space", "% +d", [42]),
    ("plus-space-neg", "% +d", [-1]),
    ("hash-width", "%#10x", [255]),
    ("plus-zero-pad", "%+08d", [42]),
    ("plus-zero-neg", "%+08d", [-42]),
    ("space-mix", "% d %d", [5, -3]),
)


def _bytes(text: str) -> bytes | None:
    if len(text) > 400 or "\x00" in text:
        return None
    try:
        return text.encode("latin1") + b"\x00"
    except UnicodeEncodeError:
        return None


def _c_int(number: int) -> bool:
    return -2147483648 <= number <= 2147483647


def _parse_specs(fmt: str) -> list[dict] | None:
    if "\x00" in fmt or len(fmt) > 180:
        return None
    specs: list[dict] = []
    index = 0
    size = len(fmt)
    while index < size:
        if fmt[index] != "%":
            index += 1
            continue
        index += 1
        if index >= size:
            return None
        if fmt[index] == "%":
            specs.append({"conv": "%", "flags": "", "width": None, "has_prec": False, "star_w": False, "star_p": False})
            index += 1
            continue
        flags: list[str] = []
        while index < size and fmt[index] in "-+ #0":
            flags.append(fmt[index])
            index += 1
        if index < size and fmt[index] == "$":
            return None
        star_w = False
        width = None
        if index < size and fmt[index] == "*":
            star_w = True
            index += 1
        elif index < size and fmt[index].isdigit():
            start = index
            while index < size and fmt[index].isdigit():
                index += 1
            width = int(fmt[start:index])
            if width > 200:
                return None
        if index < size and fmt[index] == "$":
            return None
        has_prec = False
        star_p = False
        if index < size and fmt[index] == ".":
            has_prec = True
            index += 1
            if index < size and fmt[index] == "*":
                star_p = True
                index += 1
            else:
                start = index
                while index < size and fmt[index].isdigit():
                    index += 1
                if int(fmt[start:index] or "0") > 200:
                    return None
        if index < size and fmt[index] in "hlLjzt":
            return None
        if index >= size or fmt[index] not in "cspdiuxX%":
            return None
        specs.append(
            {
                "conv": fmt[index],
                "flags": "".join(flags),
                "width": width,
                "has_prec": has_prec,
                "star_w": star_w,
                "star_p": star_p,
            }
        )
        index += 1
    if len(specs) > 12:
        return None
    return specs


def _bonus(spec: dict) -> bool:
    if spec["flags"] or spec["star_w"] or spec["has_prec"]:
        return True
    return spec["width"] is not None


def _row(specs: list[dict]) -> str:
    if any(_bonus(spec) for spec in specs):
        for spec in specs:
            if any(flag in spec["flags"] for flag in "#+ "):
                return "ft_printf #+"
        return "ft_printf -0."
    if not specs:
        return "ft_printf text"
    convs = [spec["conv"] for spec in specs if spec["conv"] != "%"]
    if not convs:
        return "ft_printf %%"
    kinds = set(convs)
    if len(kinds) != 1:
        return "ft_printf mix"
    return "ft_printf %" + kinds.pop()


def _token_int(number: int, conv: str) -> str:
    if conv == "c" and 32 <= number < 127:
        return "'" + chr(number) + "'"
    if conv == "p":
        return f"(void *){number}"
    return str(number)


def _value_arg(conv: str, value: object) -> tuple[BoundArg, str] | None:
    if value is LOCAL:
        if conv != "p":
            return None
        return BoundArg("local"), "(void *)&local"
    if value is None:
        if conv == "s":
            return BoundArg("snull", is_null=True), "NULL"
        if conv == "p":
            return BoundArg("pnull", is_null=True), "NULL"
        return None
    if isinstance(value, str):
        if conv != "s":
            return None
        buf = _bytes(value)
        if buf is None:
            return None
        return BoundArg("cstr", data=buf[:-1], buf=buf), json.dumps(value)
    if isinstance(value, int) and not isinstance(value, bool):
        if conv == "c" and _c_int(value):
            return BoundArg("int", num=value), _token_int(value, conv)
        if conv in "di" and _c_int(value):
            return BoundArg("int", num=value), str(value)
        if conv in "uxX" and -2147483648 <= value < 0:
            return BoundArg("uint", num=value), str(value)
        if conv in "uxX" and 0 <= value <= 4294967295:
            return BoundArg("uint", num=value), str(value)
        if conv == "p" and -9223372036854775808 <= value <= 18446744073709551615:
            return BoundArg("ptr", num=value), _token_int(value, conv)
    return None


def _bind_values(fmt: str, values: list) -> tuple[list[BoundArg], str, str, str] | None:
    specs = _parse_specs(fmt)
    if specs is None:
        return None
    row = _row(specs)
    if row not in ROW_PART:
        return None
    buf = _bytes(fmt)
    if buf is None:
        return None
    args = [BoundArg("fmt", buf=buf)]
    tokens: list[str] = []
    cursor = 0
    for spec in specs:
        for star in (spec["star_w"], spec["star_p"]):
            if not star:
                continue
            if cursor >= len(values):
                return None
            number = values[cursor]
            cursor += 1
            if not isinstance(number, int) or isinstance(number, bool) or not _c_int(number):
                return None
            if number > 200 or number < -200:
                return None
            args.append(BoundArg("int", num=number))
            tokens.append(str(number))
        if spec["conv"] == "%":
            continue
        if cursor >= len(values):
            return None
        parsed = _value_arg(spec["conv"], values[cursor])
        cursor += 1
        if parsed is None:
            return None
        arg, token = parsed
        args.append(arg)
        tokens.append(token)
    if cursor != len(values):
        return None
    shown = json.dumps(fmt)
    if tokens:
        call = "ft_printf(" + shown + ", " + ", ".join(tokens) + ")"
    else:
        call = f"ft_printf({shown})"
    return args, call, row, ROW_PART[row]


def _case(ident: str, suite: str, call: str, row: str, part: str) -> dict:
    return {
        "id": ident,
        "function": row,
        "kind": "compare_libc",
        "suite": suite,
        "call": call,
        "args": [],
        "expected": None,
        "part": part,
    }


def _bound(ident: str, suite: str, fmt: str, values: list, call: str | None) -> tuple[Bound, str] | None:
    built = _bind_values(fmt, values)
    if built is None:
        return None
    args, generated, row, part = built
    text = call or generated
    return Bound(_case(ident, suite, text, row, part), _SPEC, args), row


def _decode_arg(arg: dict) -> object:
    kind = arg.get("type")
    if kind == "null":
        return None
    if kind == "str":
        value = arg.get("value")
        if not isinstance(value, str):
            return _BAD
        return value
    if kind == "char":
        value = arg.get("value")
        if not isinstance(value, str):
            return _BAD
        try:
            raw = value.encode("latin1")
        except UnicodeEncodeError:
            return _BAD
        if len(raw) != 1:
            return _BAD
        return raw[0]
    if kind == "int":
        try:
            return int(arg["value"], 10)
        except (TypeError, ValueError):
            return _BAD
    if kind == "expr":
        text = arg.get("value")
        if text == "UINT_MAX":
            return 4294967295
        if not isinstance(text, str):
            return _BAD
        parsed = parse_expr(text)
        if parsed is None:
            return _BAD
        return parsed[1]
    return _BAD


def _interesting(values: tuple) -> bool:
    edges = {0, -1, 1, 127, 128, 255, 256, 2147483647, -2147483648, 4294967295}
    for value in values:
        if value is None or value == "" or value in edges:
            return True
    return False


def printf_groups() -> dict[str, list[Bound]]:
    """Subject breakers, then a spread of catalog formats. Dropped rows are absent."""
    groups: dict[str, list[Bound]] = {row: [] for row in ROW_ORDER}
    seen: set[str] = set()
    for name, fmt, values in _SUBJECT:
        built = _bound(f"subject/ft_printf/{name}", "subject", fmt, list(values), None)
        if built is None:
            raise RuntimeError(f"subject printf case {name} did not bind")
        bound, row = built
        groups[row].append(bound)
        seen.add(bound.case["call"])
    pending: dict[str, list[tuple]] = {row: [] for row in ROW_ORDER}
    for case in project_tests(load_catalog(), "ft_printf"):
        if case.get("kind") != "compare_libc":
            continue
        raw = case.get("args") or []
        if not raw or raw[0].get("type") != "str":
            continue
        fmt = raw[0].get("value")
        if not isinstance(fmt, str):
            continue
        if len(raw) - 1 > 8:
            continue
        values: list = []
        failed = False
        for arg in raw[1:]:
            value = _decode_arg(arg)
            if value is _BAD:
                failed = True
                break
            values.append(value)
        if failed:
            continue
        call = case.get("call") or ""
        if not call or call in seen:
            continue
        built = _bound(case["id"], case.get("suite") or "catalog", fmt, values, call)
        if built is None:
            continue
        bound, row = built
        key = tuple(values)
        pending[row].append((fmt, key, call, _interesting(key), bound))
    for row, items in pending.items():
        picked: list[tuple] = []
        formats: set[str] = set()
        for item in items:
            fmt = item[0]
            if fmt in formats:
                continue
            if len(formats) >= _MAX_FORMATS:
                continue
            formats.add(fmt)
            picked.append(item)
        per: Counter[str] = Counter(item[0] for item in picked)
        seen_sig = {(item[0], item[1]) for item in picked}
        for item in items:
            fmt, key, _call, interesting, _bound_item = item
            if fmt not in formats or not interesting:
                continue
            if per[fmt] >= 3 or (fmt, key) in seen_sig:
                continue
            if len(picked) >= _MAX_FORMATS + _MAX_EXTRA:
                break
            picked.append(item)
            per[fmt] += 1
            seen_sig.add((fmt, key))
        for item in picked:
            bound = item[4]
            if bound.case["call"] in seen:
                continue
            seen.add(bound.case["call"])
            groups[row].append(bound)
    return {row: bounds for row, bounds in groups.items() if bounds}
