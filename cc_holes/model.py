"""Decide which libft cases can run, and grade a function result."""

import ctypes
import re
from collections import Counter
from dataclasses import dataclass, field

from cc_holes.buffers import concretize

SUBJECT: tuple[str, ...] = (
    "ft_isalpha",
    "ft_isdigit",
    "ft_isalnum",
    "ft_isascii",
    "ft_isprint",
    "ft_strlen",
    "ft_memset",
    "ft_bzero",
    "ft_memcpy",
    "ft_memmove",
    "ft_strlcpy",
    "ft_strlcat",
    "ft_toupper",
    "ft_tolower",
    "ft_strchr",
    "ft_strrchr",
    "ft_strncmp",
    "ft_memchr",
    "ft_memcmp",
    "ft_strnstr",
    "ft_atoi",
    "ft_calloc",
    "ft_strdup",
    "ft_substr",
    "ft_strjoin",
    "ft_strtrim",
    "ft_split",
    "ft_itoa",
    "ft_strmapi",
    "ft_striteri",
    "ft_putchar_fd",
    "ft_putstr_fd",
    "ft_putendl_fd",
    "ft_putnbr_fd",
    "ft_lstnew",
    "ft_lstadd_front",
    "ft_lstsize",
    "ft_lstlast",
    "ft_lstadd_back",
    "ft_lstdelone",
    "ft_lstclear",
    "ft_lstiter",
    "ft_lstmap",
)

PART_OF: dict[str, str] = {}
for _name in SUBJECT[:23]:
    PART_OF[_name] = "part 1"
for _name in SUBJECT[23:34]:
    PART_OF[_name] = "part 2"
for _name in SUBJECT[34:]:
    PART_OF[_name] = "part 3"

RUN_KINDS = {"compare_libc", "expression", "stdout", "lines"}
DIRECT_EXPECTED = {"bool", "int", "char", "str", "null"}
_EXPR_ARI = re.compile(r"'((?:\\.|[^'\\])*)'\s*([+-])\s*(\d+)")
_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "v": "\v",
    "f": "\f",
    "0": "\0",
    "\\": "\\",
    "'": "'",
    '"': '"',
}
_SIGNALS = {
    11: "segfault",
    6: "abort",
    14: "timeout",
    8: "division by zero",
    4: "illegal instruction",
    7: "bus error",
    0: "no result",
}

_libc = ctypes.CDLL(None)
_libc.atoi.argtypes = [ctypes.c_char_p]
_libc.atoi.restype = ctypes.c_int
_libc.calloc.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
_libc.calloc.restype = ctypes.c_void_p
_libc.free.argtypes = [ctypes.c_void_p]
_libc.free.restype = None


class BindError(Exception):
    """This case cannot be turned into a call."""


@dataclass(frozen=True)
class Spec:
    name: str
    params: tuple[str, ...]
    observe: str
    stdout_style: str
    libc: str | None = None
    optional_fd: bool = False


def _spec(
    name: str,
    params: tuple[str, ...],
    observe: str,
    stdout_style: str,
    libc: str | None = None,
    optional_fd: bool = False,
) -> Spec:
    return Spec(name, params, observe, stdout_style, libc, optional_fd)


SPECS: dict[str, Spec] = {
    "ft_isalpha": _spec("ft_isalpha", ("int",), "int", "boolnum"),
    "ft_isdigit": _spec("ft_isdigit", ("int",), "int", "boolnum"),
    "ft_isalnum": _spec("ft_isalnum", ("int",), "int", "boolnum"),
    "ft_isascii": _spec("ft_isascii", ("int",), "int", "boolnum"),
    "ft_isprint": _spec("ft_isprint", ("int",), "int", "boolnum"),
    "ft_toupper": _spec("ft_toupper", ("int",), "int", "decimal"),
    "ft_tolower": _spec("ft_tolower", ("int",), "int", "decimal"),
    "ft_strlen": _spec("ft_strlen", ("cstr",), "size", "decimal", "exact"),
    "ft_atoi": _spec("ft_atoi", ("cstr",), "int", "decimal", "exact"),
    "ft_strncmp": _spec("ft_strncmp", ("cstr", "cstr", "size"), "int", "sign", "sign"),
    "ft_memcmp": _spec("ft_memcmp", ("mem", "mem", "size"), "int", "sign", "sign"),
    "ft_strchr": _spec("ft_strchr", ("cstr", "int"), "suffix", "nullstr", "suffix"),
    "ft_strrchr": _spec("ft_strrchr", ("cstr", "int"), "suffix", "nullstr", "suffix"),
    "ft_memchr": _spec("ft_memchr", ("mem", "int", "size"), "suffix", "nullstr", "suffix"),
    "ft_strnstr": _spec("ft_strnstr", ("cstr", "cstr", "size"), "suffix", "nullstr", "suffix"),
    "ft_strdup": _spec("ft_strdup", ("cstr",), "str", "nullstr", "bytes"),
    "ft_calloc": _spec("ft_calloc", ("size", "size"), "alloc", "mem", "alloc"),
    "ft_substr": _spec("ft_substr", ("cstr", "uint", "size"), "str", "nullstr"),
    "ft_strjoin": _spec("ft_strjoin", ("cstr", "cstr"), "str", "nullstr"),
    "ft_strtrim": _spec("ft_strtrim", ("cstr", "cstr"), "str", "nullstr"),
    "ft_split": _spec("ft_split", ("cstr", "char"), "lines", "lines"),
    "ft_itoa": _spec("ft_itoa", ("int",), "str", "nullstr"),
    "ft_putchar_fd": _spec("ft_putchar_fd", ("char", "fd"), "void", "stream", optional_fd=True),
    "ft_putstr_fd": _spec("ft_putstr_fd", ("cstr", "fd"), "void", "stream", optional_fd=True),
    "ft_putendl_fd": _spec("ft_putendl_fd", ("cstr", "fd"), "void", "stream", optional_fd=True),
    "ft_putnbr_fd": _spec("ft_putnbr_fd", ("int", "fd"), "void", "stream", optional_fd=True),
}


@dataclass
class BoundArg:
    role: str
    num: int = 0
    data: bytes | None = None
    buf: bytes | None = None
    is_null: bool = False


@dataclass
class Bound:
    case: dict
    spec: Spec
    args: list[BoundArg] = field(default_factory=list)
    error: str | None = None
    loop: tuple[int, int, bool] | None = None
    loop_mode: str = ""
    snippet: str = ""

    @property
    def fd(self) -> int:
        for arg in self.args:
            if arg.role == "fd":
                return arg.num
        return 1


@dataclass
class Action:
    status: str
    reason: str = ""
    bound: Bound | None = None


@dataclass
class Obs:
    kind: str
    intval: int = 0
    data: bytes = b""
    lines: tuple[bytes, ...] = ()
    out: bytes = b""
    err: bytes = b""


@dataclass
class Outcome:
    ident: str
    function: str
    suite: str
    call: str
    part: str
    status: str
    detail: str


def declared_functions(header: str) -> set[str]:
    """Function names that appear as calls or prototypes in libft.h."""
    text = re.sub(r"/\*.*?\*/", " ", header, flags=re.S)
    text = re.sub(r"//.*?$", " ", text, flags=re.M)
    return set(re.findall(r"\b(ft_[A-Za-z0-9_]+)\s*\(", text))


def _unescape_one(body: str) -> str | None:
    if len(body) == 1:
        return body
    if len(body) == 2 and body[0] == "\\" and body[1] in _ESCAPES:
        return _ESCAPES[body[1]]
    return None


def parse_expr(value: str) -> tuple[str, int] | None:
    """Known symbols and the small `'a' - 1` pattern from the catalog notes."""
    if value == "INT_MAX":
        return ("int", 2147483647)
    if value == "INT_MIN":
        return ("int", -2147483648)
    if value == "EOF":
        return ("eof", -1)
    match = _EXPR_ARI.fullmatch(value)
    if match is None:
        return None
    char = _unescape_one(match.group(1))
    if char is None:
        return None
    number = ord(char)
    delta = int(match.group(3))
    if match.group(2) == "+":
        number += delta
    else:
        number -= delta
    return ("int", number)


def _as_bytes(value: str) -> bytes:
    try:
        return value.encode("latin1")
    except UnicodeEncodeError as exc:
        raise BindError("argument is not a single-byte string") from exc


def _c_int_ok(number: int) -> bool:
    return -2147483648 <= number <= 2147483647


def _convert(role: str, arg: dict) -> BoundArg:
    kind = arg["type"]
    if kind == "null":
        if role not in {"cstr", "mem"}:
            raise BindError("null is not valid for this parameter")
        return BoundArg(role, is_null=True)
    if kind == "str":
        if role not in {"cstr", "mem"}:
            raise BindError("string is not valid for this parameter")
        data = _as_bytes(arg["value"])
        return BoundArg(role, data=data, buf=data + b"\x00")
    if kind == "char":
        raw = _as_bytes(arg["value"])
        if len(raw) != 1:
            raise BindError("char argument is not one byte")
        number = raw[0]
        if role == "char":
            return BoundArg(role, num=number)
        if role == "int":
            return BoundArg(role, num=number)
        raise BindError("char is not valid for this parameter")
    if kind == "int":
        number = int(arg["value"], 10)
        if role == "int" and not _c_int_ok(number):
            raise BindError("int out of range")
        if role in {"int", "uint", "size", "fd", "char"}:
            return BoundArg(role, num=number)
        raise BindError("int is not valid for this parameter")
    if kind == "expr":
        if arg["value"] in {"INT_MAX", "INT_MIN"} and role == "cstr":
            text = b"2147483647" if arg["value"] == "INT_MAX" else b"-2147483648"
            return BoundArg(role, data=text, buf=text + b"\x00")
        if arg["value"] == "EOF" and role == "cstr":
            # Catalog note: one byte, EOF, then NUL. (char)EOF is 0xFF.
            return BoundArg(role, data=bytes([0xFF]), buf=bytes([0xFF, 0]))
        e_text = _e_bytes(arg["value"]) if role == "cstr" else None
        if e_text is not None:
            return BoundArg(role, data=e_text, buf=e_text + b"\x00")
        parsed = parse_expr(arg["value"])
        if parsed is None or role == "cstr":
            raise BindError("argument is a harness name")
        number = parsed[1]
        if role == "int" and not _c_int_ok(number):
            raise BindError("int out of range")
        if role in {"int", "uint", "size", "char"}:
            return BoundArg(role, num=number)
        raise BindError("argument is a harness name")
    raise BindError("argument type is not supported")


def _pad_mem(args: list[BoundArg]) -> None:
    if not any(arg.role == "mem" for arg in args):
        return
    size = next((arg.num for arg in reversed(args) if arg.role == "size"), None)
    if size is None:
        return
    if size < 0 or size > 2_000_000:
        raise BindError("count is too large to stage")
    for arg in args:
        if arg.role != "mem" or arg.is_null or arg.data is None:
            continue
        buf = arg.data + b"\x00"
        if size > len(buf):
            buf = buf + bytes(size - len(buf))
        arg.buf = buf


def bind(spec: Spec, case: dict) -> Bound:
    params = spec.params
    raw_args = case["args"]
    if spec.optional_fd and len(raw_args) == len(params) - 1:
        roles = params[:-1]
        extra_fd = BoundArg("fd", num=1)
    elif len(raw_args) == len(params):
        roles = params
        extra_fd = None
    elif not raw_args:
        raise BindError("inputs are not separated")
    else:
        raise BindError("inputs are not separated")
    args: list[BoundArg] = []
    for role, arg in zip(roles, raw_args):
        args.append(_convert(role, arg))
    if extra_fd is not None:
        args.append(extra_fd)
    _pad_mem(args)
    if any(arg.is_null for arg in args):
        raise BindError("null argument")
    return Bound(case, spec, args)


def _cstr(data: bytes) -> bytes:
    return data.split(b"\x00", 1)[0]


def _sign(number: int) -> int:
    return (number > 0) - (number < 0)


def oracle(spec: Spec, bound: Bound) -> Obs:
    """Reference result for libc compares and for stdout print checks."""
    args = bound.args
    name = spec.name
    if name == "ft_atoi":
        return Obs("int", intval=_libc.atoi(args[0].buf))
    if name == "ft_strlen":
        return Obs("int", intval=len(_cstr(args[0].data or b"")))
    if name == "ft_strncmp":
        return Obs("int", intval=_strncmp(args[0].data or b"", args[1].data or b"", args[2].num))
    if name == "ft_memcmp":
        return Obs("int", intval=_memcmp(args[0].buf or b"", args[1].buf or b"", args[2].num))
    if name == "ft_strchr":
        return _suffix_obs(_strchr(args[0].data or b"", args[1].num))
    if name == "ft_strrchr":
        return _suffix_obs(_strrchr(args[0].data or b"", args[1].num))
    if name == "ft_memchr":
        return _suffix_obs(_memchr(args[0].buf or b"", args[1].num, args[2].num))
    if name == "ft_strnstr":
        return _suffix_obs(_strnstr(args[0].data or b"", args[1].data or b"", args[2].num))
    if name == "ft_strdup":
        return Obs("bytes", data=_cstr(args[0].data or b""))
    if name == "ft_calloc":
        return _calloc(args[0].num, args[1].num)
    if name == "ft_substr":
        return Obs("bytes", data=_substr(args[0].data or b"", args[1].num, args[2].num))
    if name == "ft_strjoin":
        left = _cstr(args[0].data or b"")
        right = _cstr(args[1].data or b"")
        return Obs("bytes", data=left + right)
    if name == "ft_strtrim":
        return Obs("bytes", data=_strtrim(args[0].data or b"", args[1].data or b""))
    if name == "ft_split":
        return Obs("lines", lines=tuple(_split(args[0].data or b"", args[1].num)))
    if name == "ft_itoa":
        return Obs("bytes", data=str(args[0].num).encode("ascii"))
    if name in {"ft_toupper", "ft_tolower"}:
        return Obs("int", intval=_casefold(name, args[0].num))
    if name in {"ft_isalpha", "ft_isdigit", "ft_isalnum", "ft_isascii", "ft_isprint"}:
        return Obs("int", intval=int(_ctype(name, args[0].num)))
    raise RuntimeError(f"no oracle for {name}")


def _suffix_obs(value: bytes | None) -> Obs:
    if value is None:
        return Obs("null")
    return Obs("bytes", data=value)


def _big_count(count: int, until_nul: int) -> int:
    """A negative count is a size_t wider than a signed int. Stop at the terminator."""
    if count < 0:
        return until_nul
    return count


def _strncmp(left: bytes, right: bytes, count: int) -> int:
    aa = _cstr(left)
    bb = _cstr(right)
    limit = _big_count(count, max(len(aa), len(bb)) + 1)
    for index in range(limit):
        byte_a = aa[index] if index < len(aa) else 0
        byte_b = bb[index] if index < len(bb) else 0
        if byte_a != byte_b:
            return byte_a - byte_b
        if byte_a == 0:
            return 0
    return 0


def _memcmp(left: bytes, right: bytes, count: int) -> int:
    limit = count if count >= 0 else 0
    for index in range(limit):
        byte_a = left[index] if index < len(left) else 0
        byte_b = right[index] if index < len(right) else 0
        if byte_a != byte_b:
            return byte_a - byte_b
    return 0


def _strchr(data: bytes, char: int) -> bytes | None:
    view = _cstr(data)
    char &= 0xFF
    if char == 0:
        return b""
    index = view.find(bytes([char]))
    if index < 0:
        return None
    return view[index:]


def _strrchr(data: bytes, char: int) -> bytes | None:
    view = _cstr(data)
    char &= 0xFF
    if char == 0:
        return b""
    index = view.rfind(bytes([char]))
    if index < 0:
        return None
    return view[index:]


def _memchr(buf: bytes, char: int, count: int) -> bytes | None:
    char &= 0xFF
    chunk = buf[: max(count, 0)]
    index = chunk.find(bytes([char]))
    if index < 0:
        return None
    return buf[index:].split(b"\x00", 1)[0]


def _strnstr(hay: bytes, needle: bytes, count: int) -> bytes | None:
    hay_c = _cstr(hay)
    needle_c = _cstr(needle)
    if needle_c == b"":
        return hay_c
    limit = _big_count(count, len(hay_c) + 1)
    index = 0
    while index < len(hay_c) and index < limit:
        step = 0
        while (
            step < len(needle_c)
            and index + step < limit
            and index + step < len(hay_c)
            and hay_c[index + step] == needle_c[step]
        ):
            step += 1
        if step == len(needle_c):
            return hay_c[index:]
        index += 1
    return None


def _calloc(count: int, size: int) -> Obs:
    if count < 0 or size < 0:
        return Obs("null")
    if count and size > (2**64 - 1) // count:
        return Obs("null")
    pointer = _libc.calloc(count, size)
    if not pointer:
        return Obs("null")
    total = count * size
    data = ctypes.string_at(pointer, total) if total else b""
    _libc.free(pointer)
    return Obs("mem", data=data)


def _substr(data: bytes, start: int, length: int) -> bytes:
    view = _cstr(data)
    start &= 0xFFFFFFFF
    if length < 0:
        length &= 2**64 - 1
    if start >= len(view):
        return b""
    return view[start : start + length]


def _strtrim(data: bytes, charset: bytes) -> bytes:
    view = _cstr(data)
    allowed = set(_cstr(charset))
    begin = 0
    end = len(view)
    while begin < end and view[begin] in allowed:
        begin += 1
    while end > begin and view[end - 1] in allowed:
        end -= 1
    return view[begin:end]


def _split(data: bytes, char: int) -> list[bytes]:
    view = _cstr(data)
    char &= 0xFF
    parts: list[bytes] = []
    index = 0
    size = len(view)
    while index < size:
        while index < size and view[index] == char:
            index += 1
        if index >= size:
            break
        end = index
        while end < size and view[end] != char:
            end += 1
        parts.append(view[index:end])
        index = end
    return parts


def _ctype(name: str, number: int) -> bool:
    if number < 0 or number > 255:
        return False
    if name == "ft_isalpha":
        return (65 <= number <= 90) or (97 <= number <= 122)
    if name == "ft_isdigit":
        return 48 <= number <= 57
    if name == "ft_isalnum":
        return _ctype("ft_isalpha", number) or _ctype("ft_isdigit", number)
    if name == "ft_isascii":
        return 0 <= number <= 127
    if name == "ft_isprint":
        return 32 <= number <= 126
    raise RuntimeError(name)


def _casefold(name: str, number: int) -> int:
    if number < 0 or number > 255:
        return number
    if name == "ft_toupper" and 97 <= number <= 122:
        return number - 32
    if name == "ft_tolower" and 65 <= number <= 90:
        return number + 32
    return number


def format_obs(style: str, obs: Obs) -> bytes | None:
    if style == "decimal":
        return str(obs.intval).encode("ascii")
    if style == "sign":
        return str(_sign(obs.intval)).encode("ascii")
    if style == "boolnum":
        return b"1" if obs.intval else b"0"
    if style == "nullstr":
        if obs.kind == "null":
            return b"NULL"
        return obs.data
    if style == "lines":
        if obs.kind == "null":
            return b"NULL"
        return b"".join(part + b"\n" for part in obs.lines)
    if style == "mem":
        if obs.kind == "null":
            return b"NULL"
        return obs.data
    return None


def expected_bytes(case: dict) -> bytes:
    """Bytes stored on the case.

    fsoares ft_putnbr_fd follows the call with ft_putendl_fd(""), so the
    stored stdout includes a newline the function itself does not write.
    """
    expected = case["expected"]
    value = expected["value"]
    if not isinstance(value, str):
        raise BindError("expected value is not bytes")
    raw = value.encode("latin1")
    if (
        case["suite"] == "fsoares"
        and case["function"] == "ft_putnbr_fd"
        and expected["type"] == "stdout"
        and raw.endswith(b"\n")
    ):
        return raw[:-1]
    return raw


def _stream_name(case: dict) -> str:
    stream = case.get("stream")
    if stream in {"stdout", "stderr"}:
        return stream
    expected = case.get("expected") or {}
    if expected.get("type") in {"stdout", "stderr"}:
        return expected["type"]
    return "stdout"


def _stdout_matches(spec: Spec, bound: Bound, case: dict) -> bool:
    try:
        printed = format_obs(spec.stdout_style, oracle(spec, bound))
        return printed is not None and printed == expected_bytes(case)
    except (BindError, OverflowError, OSError):
        return False


def _expr_ready(case: dict) -> bool:
    expected = case.get("expected")
    if not case["args"] or not isinstance(expected, dict):
        return False
    return expected.get("type") in DIRECT_EXPECTED


_CTYPE = {"ft_isalpha", "ft_isdigit", "ft_isalnum", "ft_isascii", "ft_isprint"}
_LOOP_CALL = re.compile(
    r"^ft_[A-Za-z0-9_]+\(i\) for i in (\d+|'.')\.\.(\d+|'.')( exclusive)?$"
)


def _loop_end(token: str) -> int | None:
    if re.fullmatch(r"-?\d+", token):
        return int(token)
    if len(token) == 3 and token[0] == "'" and token[2] == "'":
        return ord(token[1])
    return None


def _parse_loop(case: dict) -> tuple[int, int, bool] | None:
    match = _LOOP_CALL.fullmatch(case.get("call") or "")
    if match is None:
        return None
    start = _loop_end(match.group(1))
    end = _loop_end(match.group(2))
    if start is None or end is None:
        return None
    return start, end, match.group(3) is None


def _putchar_fd(case: dict) -> int | None:
    match = re.search(r"ft_putchar_fd\s*\(\s*i\s*,\s*(-?\d+)\s*\)", case.get("body") or "")
    if match is None:
        return None
    return int(match.group(1))


def classify(case: dict, declared: set[str] | None) -> Action:
    """Skip rules follow francinette-tests.md. A run action is safe to compile."""
    function = case["function"]
    if declared is not None and function not in declared:
        return Action("skip", "not in libft.h")
    concrete = concretize(case)
    if concrete is not None:
        case = concrete
        function = case["function"]
    snippet = case.get("snippet") or ""
    if snippet:
        spec = SPECS.get(function) or _spec(function, (), "void", "stream")
        return Action("run", bound=Bound(case, spec, snippet=snippet))
    loop = _parse_loop(case)
    if loop is not None and function in SPECS:
        if function in _CTYPE:
            return Action("run", bound=Bound(case, SPECS[function], loop=loop, loop_mode="digit"))
        if function in {"ft_toupper", "ft_tolower"}:
            return Action("run", bound=Bound(case, SPECS[function], loop=loop, loop_mode="byte"))
        if function == "ft_putchar_fd":
            fd = _putchar_fd(case)
            if fd not in {1, 2}:
                return Action("skip", "fd is not 1 or 2")
            return Action(
                "run",
                bound=Bound(case, SPECS[function], loop=loop, loop_mode=f"put:{fd}"),
            )
    kind = case["kind"]
    if kind == "crash":
        return Action("skip", "crash helper has no arguments")
    if kind == "guard":
        return Action("skip", "guard helper has no arguments")
    if kind not in RUN_KINDS:
        return Action("skip", "not a direct input")
    if any(
        arg["type"] == "expr" and parse_expr(arg["value"]) is None and not _expr_string(arg["value"])
        for arg in case["args"]
    ):
        return Action("skip", "argument is a harness name")
    if kind == "expression" and not _expr_ready(case):
        return Action("skip", "check is not a direct call")
    spec = SPECS.get(function)
    if spec is None:
        return Action("skip", "no runner for this function yet")
    try:
        bound = bind(spec, case)
    except BindError as exc:
        return Action("skip", str(exc))
    if kind == "stdout" and spec.stdout_style == "stream" and bound.fd not in {1, 2}:
        return Action("skip", "fd is not 1 or 2")
    if kind == "stdout" and spec.stdout_style != "stream" and not _stdout_matches(spec, bound, case):
        return Action("skip", "print wrapper is custom")
    if kind == "compare_libc" and case["expected"] is None and spec.libc is None:
        return Action("skip", "no libc oracle")
    expected = case.get("expected")
    if kind == "compare_libc" and isinstance(expected, dict):
        if expected["type"] not in {"str", "lines", "stdout", "stderr", "int", "bool", "char", "null"}:
            return Action("skip", "oracle type is not handled")
    return Action("run", bound=bound)


_E_CALL = re.compile(r'^\(e \+ "(.*)"\)\.c_str\(\)$')


def _expr_string(value: str) -> bool:
    """String-shaped expressions the catalog says are runnable."""
    if value in {"INT_MAX", "INT_MIN", "EOF"}:
        return True
    return _E_CALL.fullmatch(value) is not None


def _e_bytes(value: str) -> bytes | None:
    match = _E_CALL.fullmatch(value)
    if match is None:
        return None
    # The catalog note: e is tab, newline, vertical tab, form feed, carriage return.
    return "\t\n\v\f\r".encode("latin1") + match.group(1).encode("latin1")


def grade(case: dict, spec: Spec, student: Obs, bound: Bound | None = None) -> tuple[str, str]:
    expected = case.get("expected")
    if isinstance(expected, dict) and expected.get("type") == "ub":
        return _grade_ub(str(expected.get("value") or "crash"), student)
    if isinstance(expected, dict) and expected.get("type") == "guard":
        return _grade_guard(student)
    if student.kind == "crash":
        name = _SIGNALS.get(student.intval, f"signal {student.intval}")
        return "fail", name
    if student.kind == "bad":
        text = student.data.decode("ascii", "replace") or "bad result"
        return "fail", text
    kind = case["kind"]
    if kind == "stdout" and bound is not None and (bound.loop is not None or bound.snippet):
        return _grade_stream(case, student)
    if kind == "stdout":
        if spec.stdout_style == "stream":
            return _grade_stream(case, student)
        printed = format_obs(spec.stdout_style, student)
        wanted = expected_bytes(case)
        if printed == wanted:
            return "pass", f"yours {_show(printed or b'')}, supposed {_show(wanted)}"
        return "fail", f"yours {_show(printed or b'')}, supposed {_show(wanted)}"
    expected = case.get("expected")
    if kind == "compare_libc" and expected is None:
        ready = bound if bound is not None else bind(spec, case)
        return _grade_libc(spec, student, oracle(spec, ready))
    if kind in {"compare_libc", "expression"} and isinstance(expected, dict):
        if expected["type"] in {"stdout", "stderr"}:
            return _grade_stream(case, student)
        if case["function"] in _CTYPE and expected["type"] == "bool":
            return _grade_ctype(expected, student)
        return _grade_stored(expected, student)
    return "fail", "no oracle"


def _sig_name(sig: int) -> str:
    return _SIGNALS.get(sig, f"signal {sig}")


def _ub_parts(student: Obs) -> tuple[int, ...] | None:
    if student.kind != "ub":
        return None
    text = student.data.decode("ascii", "replace")
    if not text:
        return None
    try:
        return tuple(int(part) for part in text.split(","))
    except ValueError:
        return None


def _grade_ub(mode: str, student: Obs) -> tuple[str, str]:
    """Part 1 must follow libc, including a crash.

    libc crashed and the function returned: warning.
    The function crashed and libc did not: fail.
    Both crashed: pass.
    """
    parts = _ub_parts(student)
    if parts is None or len(parts) < 2:
        if student.kind == "crash":
            return "fail", _sig_name(student.intval)
        return "fail", "could not run the libc crash probe"
    libc_sig, ft_sig = parts[0], parts[1]
    if libc_sig < 0 or ft_sig < 0:
        return "fail", "could not run the libc crash probe"
    if libc_sig and ft_sig:
        return "pass", f"both crashed ({_sig_name(ft_sig)}), matches libc"
    if libc_sig and not ft_sig:
        return (
            "warn",
            f"your function returned, libc crashed ({_sig_name(libc_sig)}). "
            "Expected a crash. Undefined behavior has to match libc. "
            "This is a warning, not an error.",
        )
    if ft_sig and not libc_sig:
        return "fail", f"your function crashed ({_sig_name(ft_sig)}), libc did not"
    if mode == "crash":
        return "pass", "neither crashed"
    if len(parts) < 4:
        return "fail", "could not run the libc crash probe"
    libc_val, ft_val = parts[2], parts[3]
    if mode == "nullness":
        if libc_val == ft_val:
            shown = "NULL" if ft_val else "non-NULL"
            return "pass", f"overflow result matches libc ({shown})"
        libc_text = "NULL" if libc_val else "non-NULL"
        ft_text = "NULL" if ft_val else "non-NULL"
        return "fail", f"overflow result does not match libc (libc {libc_text}, yours {ft_text})"
    if mode == "ctype":
        if ft_val not in {0, 1}:
            return "fail", f"yours {ft_val}, supposed 0 or 1 (subject: exactly 1 or 0)"
        wanted = 1 if libc_val else 0
        if ft_val == wanted:
            return "pass", f"yours {ft_val}, supposed {wanted}"
        return (
            "warn",
            f"yours {ft_val}, libc {libc_val}. "
            "This argument is outside unsigned char and EOF. "
            "Your return is 0 or 1, which the subject asks for. "
            "This is a warning, not an error.",
        )
    if mode == "soft":
        if ft_val == libc_val:
            return "pass", f"yours {ft_val}, libc {libc_val}"
        return (
            "warn",
            f"yours {ft_val}, libc {libc_val}. "
            "This argument is outside unsigned char and EOF. "
            "This is a warning, not an error.",
        )
    return "fail", "oracle type is not handled"


def _grade_guard(student: Obs) -> tuple[str, str]:
    """Part 2 and the list helpers. The subject does not define these calls."""
    if student.kind == "crash":
        return "fail", _sig_name(student.intval)
    if student.kind != "guard":
        return "fail", "could not run the crash guard"
    if student.intval < 0:
        return "fail", "could not run the crash guard"
    if student.intval:
        return (
            "warn",
            f"your function crashed ({_sig_name(student.intval)}). "
            "The subject does not define this call, so a crash is undefined behavior. "
            "This is a warning, not an error.",
        )
    return "pass", "returned without crashing"


def _grade_stream(case: dict, student: Obs) -> tuple[str, str]:
    wanted = expected_bytes(case)
    got = student.err if _stream_name(case) == "stderr" else student.out
    shown = f"yours {_show(got)}, supposed {_show(wanted)}"
    if got == wanted:
        return "pass", shown
    return "fail", shown


def _grade_ctype(expected: dict, student: Obs) -> tuple[str, str]:
    """The subject says these five functions return 1 or 0, not any non-zero."""
    wanted = 1 if expected["value"] == "true" else 0
    shown = f"yours {student.intval}, supposed {wanted}"
    if student.intval == wanted:
        return "pass", shown
    return "fail", shown + " (subject: exactly 1 or 0)"


def _grade_stored(expected: dict, student: Obs) -> tuple[str, str]:
    kind = expected["type"]
    if kind == "pair":
        wanted_n = int(expected["value"]["n"])
        wanted = expected["value"]["bytes"].encode("latin1")
        shown = f"yours {student.intval} {_show(student.data)}, supposed {wanted_n} {_show(wanted)}"
        if student.kind == "pair" and student.intval == wanted_n and student.data == wanted:
            return "pass", shown
        return "fail", shown
    if kind == "null":
        if student.kind == "null":
            return "pass", "yours NULL, supposed NULL"
        return "fail", f"yours {_show_obs(student)}, supposed NULL"
    if kind == "bool":
        want_true = expected["value"] == "true"
        got_true = student.intval != 0
        supposed = "non-zero" if want_true else "0"
        if want_true == got_true:
            return "pass", f"yours {student.intval}, supposed {supposed}"
        return "fail", f"yours {student.intval}, supposed {supposed}"
    if kind == "int":
        wanted = int(expected["value"], 10)
        if student.intval == wanted:
            return "pass", f"yours {student.intval}, supposed {wanted}"
        return "fail", f"yours {student.intval}, supposed {wanted}"
    if kind == "char":
        raw = expected["value"].encode("latin1")
        wanted_byte = raw[0] if raw else "?"
        if len(raw) == 1 and student.intval == raw[0]:
            return "pass", f"yours {student.intval}, supposed {wanted_byte}"
        return "fail", f"yours {student.intval}, supposed {wanted_byte}"
    if kind == "str":
        wanted = expected["value"].encode("latin1")
        shown = f"yours {_show_obs(student)}, supposed {_show(wanted)}"
        if student.kind == "bytes" and student.data == wanted:
            return "pass", shown
        return "fail", shown
    if kind == "lines":
        wanted = tuple(part.encode("latin1") for part in expected["value"])
        shown = f"yours {_show_obs(student)}, supposed {_show_lines(wanted)}"
        if student.kind == "lines" and student.lines == wanted:
            return "pass", shown
        return "fail", shown
    return "fail", "oracle type is not handled"


def _grade_libc(spec: Spec, student: Obs, reference: Obs) -> tuple[str, str]:
    mode = spec.libc
    if mode == "exact":
        shown = f"yours {student.intval}, libc {reference.intval}"
        if student.intval == reference.intval:
            return "pass", shown
        return "fail", shown
    if mode == "sign":
        shown = f"yours {student.intval}, libc {reference.intval} (same sign is enough)"
        if _sign(student.intval) == _sign(reference.intval):
            return "pass", shown
        return "fail", f"yours {student.intval}, libc {reference.intval}"
    if mode in {"suffix", "bytes"}:
        shown = f"yours {_show_obs(student)}, libc {_show_obs(reference)}"
        if student.kind == "null" and reference.kind == "null":
            return "pass", shown
        if student.kind == "bytes" and reference.kind == "bytes" and student.data == reference.data:
            return "pass", shown
        return "fail", shown
    if mode == "alloc":
        shown = f"yours {_show_obs(student)}, libc {_show_obs(reference)}"
        if student.kind == "null" and reference.kind == "null":
            return "pass", shown
        if student.kind == "mem" and reference.kind == "mem" and student.data == reference.data:
            return "pass", shown
        return "fail", shown
    return "fail", "no libc oracle"


def _show(data: bytes, limit: int = 48) -> str:
    text = repr(data)
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def _show_lines(lines: tuple[bytes, ...]) -> str:
    return _show(b" | ".join(lines))


def _show_obs(obs: Obs) -> str:
    if obs.kind == "null":
        return "NULL"
    if obs.kind == "lines":
        return _show_lines(obs.lines)
    if obs.kind in {"bytes", "mem"}:
        return _show(obs.data)
    if obs.kind == "int":
        return str(obs.intval)
    return obs.kind


def parse_result_line(line: str) -> tuple[str, Obs] | None:
    if line.startswith("DONE\t"):
        return None
    parts = line.split("\t")
    if len(parts) != 6:
        raise ValueError(line[:120])
    ident, status, kind, payload, out_hex, err_hex = parts
    out = bytes.fromhex(out_hex) if out_hex else b""
    err = bytes.fromhex(err_hex) if err_hex else b""
    if status == "crash":
        return ident, Obs("crash", intval=int(payload or "0"), out=out, err=err)
    if kind in {"int", "size"}:
        return ident, Obs("int", intval=int(payload), out=out, err=err)
    if kind == "null":
        return ident, Obs("null", out=out, err=err)
    if kind == "bytes":
        return ident, Obs("bytes", data=bytes.fromhex(payload) if payload else b"", out=out, err=err)
    if kind == "pair":
        count_text, _, hex_part = payload.partition(":")
        data = bytes.fromhex(hex_part) if hex_part else b""
        return ident, Obs("pair", intval=int(count_text or "0"), data=data, out=out, err=err)
    if kind == "mem":
        return ident, Obs("mem", data=bytes.fromhex(payload) if payload else b"", out=out, err=err)
    if kind == "void":
        return ident, Obs("void", out=out, err=err)
    if kind == "bad":
        return ident, Obs("bad", data=payload.encode("ascii", "replace"), out=out, err=err)
    if kind == "ub":
        return ident, Obs("ub", data=payload.encode("ascii", "replace"), out=out, err=err)
    if kind == "guard":
        return ident, Obs("guard", intval=int(payload or "0"), out=out, err=err)
    if kind == "lines":
        count_text, _, rest = payload.partition(":")
        count = int(count_text or "0")
        if count == 0:
            lines: tuple[bytes, ...] = ()
        else:
            pieces = rest.split(",")
            if len(pieces) != count:
                return ident, Obs("bad", data=b"truncated split result", out=out, err=err)
            lines = tuple(bytes.fromhex(piece) if piece else b"" for piece in pieces)
        return ident, Obs("lines", lines=lines, out=out, err=err)
    return ident, Obs("bad", data=f"unknown result {kind}".encode(), out=out, err=err)


def _trim(text: str, limit: int = 96) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def outcome_from(case: dict, status: str, detail: str) -> Outcome:
    return Outcome(
        ident=case["id"],
        function=case["function"],
        suite=case["suite"],
        call=case["call"].replace("\n", " "),
        part=case.get("part") or PART_OF.get(case["function"], ""),
        status=status,
        detail=detail,
    )


@dataclass
class Row:
    function: str
    part: str
    passed: int
    failed: int
    skipped: int
    note: str
    declared: bool
    warned: int = 0
    fails: list[str] = field(default_factory=list)
    samples: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)


def build_row(function: str, outcomes: list[Outcome], declared: bool) -> Row:
    passed = sum(item.status == "pass" for item in outcomes)
    failed = sum(item.status == "fail" for item in outcomes)
    warned = sum(item.status == "warn" for item in outcomes)
    skipped = sum(item.status == "skip" for item in outcomes)
    fails = [
        f"{item.suite}  {_trim(item.call)}\n    {item.detail}"
        for item in outcomes
        if item.status == "fail"
    ][:12]
    warns = [
        f"WARN  {item.suite}  {_trim(item.call)}\n    {item.detail}"
        for item in outcomes
        if item.status == "warn"
    ][:12]
    samples = [
        f"{item.suite}  {_trim(item.call)}"
        for item in outcomes
        if item.status == "skip"
    ][:4]
    note = ""
    if not declared:
        note = "required, not in libft.h"
    elif warned and not failed:
        note = "warning"
    elif failed == 0 and passed == 0 and skipped:
        reasons = Counter(item.detail for item in outcomes if item.status == "skip")
        note = reasons.most_common(1)[0][0]
    return Row(
        function=function,
        part=PART_OF.get(function, "extra"),
        passed=passed,
        failed=failed,
        skipped=skipped,
        note=note,
        declared=declared,
        warned=warned,
        fails=fails,
        samples=samples,
        warns=warns,
    )
