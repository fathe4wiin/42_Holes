"""Fill harness names from the fsoares and war-machine sources.

`mem` and `dest` in the catalog are names. The bytes live in
vendor/francinette: fsoares `reset` writes 0x11 across 256 bytes
(utils/utils.c), and each war-machine main.c writes its own fill.
"""

import ctypes
from copy import deepcopy

MEM_SIZE = 0x100
FILL = 0x11


def concretize(case: dict) -> dict | None:
    """Return a case whose buffer args are real bytes, or None."""
    if case.get("snippet"):
        return None
    function = case.get("function")
    suite = case.get("suite")
    if function == "ft_calloc" and suite == "fsoares":
        return _sizeof_long(case)
    if function in {"ft_memcmp", "ft_strncmp", "ft_strnstr"} and suite == "fsoares":
        return _named_strings(case)
    built = _snippet_for(case)
    if built is None:
        return None
    ready = deepcopy(case)
    ready["snippet"] = built[0]
    if built[1] is not None:
        ready["kind"] = "expression"
        ready["expected"] = built[1]
    return ready


def _sizeof_long(case: dict) -> dict | None:
    args = case.get("args") or []
    if not any(arg.get("type") == "expr" and arg.get("value") == "sizeof(long)" for arg in args):
        return None
    ready = deepcopy(case)
    ready["args"] = [
        {"type": "int", "value": str(ctypes.sizeof(ctypes.c_long))}
        if arg.get("type") == "expr" and arg.get("value") == "sizeof(long)"
        else dict(arg)
        for arg in args
    ]
    return ready


def _c_array(name: str, data: bytes) -> str:
    body = ",".join(str(byte) for byte in data)
    return f"\tunsigned char {name}[{len(data)}] = {{{body}}};"


def _bytes_of(value: str) -> bytes:
    return value.encode("latin1")


def _fill(size: int, byte: int = FILL) -> bytearray:
    return bytearray([byte]) * size


def _strcpy(buf: bytearray, offset: int, text: bytes) -> None:
    for index, byte in enumerate(text + b"\x00"):
        buf[offset + index] = byte


def _reset(buf: bytearray, offset: int, size: int) -> None:
    for index in range(size):
        buf[offset + index] = FILL


def _memset(buf: bytearray, offset: int, char: int, count: int) -> None:
    char &= 0xFF
    for index in range(count):
        buf[offset + index] = char


def _memmove(buf: bytearray, dest: int, src: int, count: int) -> None:
    chunk = bytes(buf[src : src + count])
    buf[dest : dest + count] = chunk


def _strlcpy(buf: bytearray, src: bytes, size: int) -> int:
    if size > 0:
        copied = 0
        while copied + 1 < size and copied < len(src):
            buf[copied] = src[copied]
            copied += 1
        buf[copied] = 0
    return len(src)


def _strlcat(buf: bytearray, src: bytes, size: int) -> int:
    dlen = 0
    while dlen < size and dlen < len(buf) and buf[dlen] != 0:
        dlen += 1
    if dlen == size:
        return size + len(src)
    copied = 0
    while dlen + copied + 1 < size and copied < len(src):
        buf[dlen + copied] = src[copied]
        copied += 1
    buf[dlen + copied] = 0
    return dlen + len(src)


def _pair(number: int, data: bytes) -> dict:
    return {"type": "pair", "value": {"n": str(number), "bytes": data.decode("latin1")}}


def _text(data: bytes) -> dict:
    return {"type": "str", "value": data.decode("latin1")}


def _capture_buffer(setup: str, call: str, view: int, message: str | None) -> str:
    check = ""
    if message is not None:
        escaped = (
            message.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        )
        check = (
            "\tif (ret != (void *)buf)\n"
            f'\t\twrite(1, "{escaped}", sizeof "{escaped}" - 1);\n'
        )
    return f"""
{setup}
	char *oh = NULL;
	char *eh = NULL;
	void *ret;
	begin_cap();
	ret = {call};
{check}	write(1, buf, {view});
	end_cap(&oh, &eh);
	emit_void(id, oh, eh);
"""


def _capture_size(setup: str, call: str, view: int) -> str:
    return f"""
{setup}
	char *oh = NULL;
	char *eh = NULL;
	size_t n;
	char digit[24];
	int pos;
	begin_cap();
	n = {call};
	if (n == 0)
		write(1, "0", 1);
	else
	{{
		size_t copy;
		copy = n;
		pos = 0;
		while (copy)
		{{
			digit[pos++] = (char)('0' + (copy % 10));
			copy /= 10;
		}}
		while (pos)
			write(1, &digit[--pos], 1);
	}}
	write(1, "\\n", 1);
	write(1, buf, {view});
	end_cap(&oh, &eh);
	emit_void(id, oh, eh);
"""


def _emit_bytes(setup: str, call: str, view_off: int, view_len: int, pointer: str) -> str:
    guard = ""
    if pointer:
        guard = f"""
	if (ret != {pointer})
	{{
		printf("%s\\tok\\tbad\\treturn is not the buffer\\t%s\\t%s\\n",
			id, oh ? oh : "", eh ? eh : "");
		free(oh);
		free(eh);
		return;
	}}
"""
    return f"""
{setup}
	char *oh = NULL;
	char *eh = NULL;
	void *ret;
	begin_cap();
	ret = {call};
	end_cap(&oh, &eh);
{guard}	emit_raw(id, buf + {view_off}, {view_len}, oh, eh);
"""


def _emit_pair(setup: str, call: str, view_len: int) -> str:
    return f"""
{setup}
	char *oh = NULL;
	char *eh = NULL;
	size_t n;
	begin_cap();
	n = {call};
	end_cap(&oh, &eh);
	emit_pair(id, n, buf, {view_len}, oh, eh);
"""


def _arg(case: dict, index: int, kind: str) -> str:
    return case["args"][index]["value"] if case["args"][index]["type"] == kind else ""


def _int_arg(case: dict, index: int) -> int:
    return int(case["args"][index]["value"], 10)


def _char_arg(case: dict, index: int) -> int:
    arg = case["args"][index]
    if arg["type"] == "char":
        return arg["value"].encode("latin1")[0]
    return int(arg["value"], 10)


def _snippet_for(case: dict) -> tuple[str, dict | None] | None:
    if not case.get("args"):
        return None
    function = case["function"]
    suite = case["suite"]
    if suite == "fsoares" and function == "ft_memset":
        return _fsoares_memset(case)
    if suite == "fsoares" and function == "ft_bzero":
        return _fsoares_bzero(case)
    if suite == "fsoares" and function == "ft_memcpy":
        return _fsoares_memcpy(case)
    if suite == "fsoares" and function == "ft_memmove":
        return _fsoares_memmove(case)
    if suite == "fsoares" and function == "ft_strlcpy":
        return _fsoares_strlcpy(case)
    if suite == "fsoares" and function == "ft_strlcat":
        return _fsoares_strlcat(case)
    if suite == "fsoares" and function in {"ft_strmapi", "ft_striteri"}:
        return _fsoares_map(case)
    if suite == "war-machine" and function == "ft_memset":
        return _war_memset(case)
    if suite == "war-machine" and function == "ft_bzero":
        return _war_bzero(case)
    if suite == "war-machine" and function == "ft_memcpy":
        return _war_memcpy(case)
    if suite == "war-machine" and function == "ft_memmove":
        return _war_memmove(case)
    if suite == "war-machine" and function == "ft_strlcpy":
        return _war_strl(case, cat=False)
    if suite == "war-machine" and function == "ft_strlcat":
        return _war_strlcat(case)
    if suite == "war-machine" and function in {"ft_strmapi", "ft_striteri"}:
        return _war_map(case)
    return None


def _fsoares_memset(case: dict) -> tuple[str, dict] | None:
    name = case["args"][0]["value"]
    char = _char_arg(case, 1)
    count = _int_arg(case, 2)
    if name == "mem":
        buf = _fill(MEM_SIZE)
        setup = _c_array("buf", bytes(buf))
        _memset(buf, 0, char, count)
        call = f"ft_memset(buf, {char}, {count})"
        return _emit_bytes(setup, call, 0, MEM_SIZE, "(void *)buf"), _text(bytes(buf))
    if name == "ptr":
        raw = _fill(MEM_SIZE * 4)
        setup = _c_array("buf", bytes(raw))
        _memset(raw, 4, char, count)
        call = f"ft_memset(buf + 4, {char}, {count})"
        shown = bytes(raw[:16])
        return _emit_bytes(setup, call, 0, 16, "(void *)(buf + 4)"), _text(shown)
    return None


def _fsoares_bzero(case: dict) -> tuple[str, dict] | None:
    if case["args"][0]["value"] != "mem":
        return None
    count = _int_arg(case, 1)
    buf = _fill(MEM_SIZE)
    _memset(buf, 0, 0, count)
    setup = _c_array("buf", _fill(MEM_SIZE))
    call = f"ft_bzero(buf, {count})"
    snippet = f"""
{setup}
	char *oh = NULL;
	char *eh = NULL;
	begin_cap();
	{call};
	end_cap(&oh, &eh);
	emit_raw(id, buf, {MEM_SIZE}, oh, eh);
"""
    return snippet, _text(bytes(buf))


def _fsoares_memcpy(case: dict) -> tuple[str, dict] | None:
    if [arg["value"] for arg in case["args"][:2]] != ["dest", "src"]:
        return None
    count = _int_arg(case, 2)
    dest = _fill(MEM_SIZE)
    src = _fill(MEM_SIZE)
    _memmove(dest, 0, 0, 0)
    if count:
        return None
    setup = _c_array("buf", bytes(dest)) + "\n" + _c_array("src", bytes(src))
    call = f"ft_memcpy(buf, src, {count})"
    return _emit_bytes(setup, call, 0, MEM_SIZE, "(void *)buf"), _text(bytes(dest))


def _fsoares_memmove(case: dict) -> tuple[str, dict] | None:
    dest_name = case["args"][0]["value"]
    src_name = case["args"][1]["value"]
    text = _bytes_of(case["args"][2]["value"])
    count = _int_arg(case, 3)
    offsets = {"dest": 0, "dest + 2": 2}
    if dest_name not in offsets or src_name not in offsets:
        return None
    dest_off = offsets[dest_name]
    src_off = offsets[src_name]
    buf = _fill(MEM_SIZE + 10)
    _reset(buf, dest_off, MEM_SIZE)
    _reset(buf, src_off, MEM_SIZE)
    _strcpy(buf, src_off, text)
    initial = bytes(buf)
    _memmove(buf, dest_off, src_off, count)
    setup = _c_array("buf", initial)
    call = f"ft_memmove(buf + {dest_off}, buf + {src_off}, {count})"
    shown = bytes(buf[dest_off : dest_off + MEM_SIZE])
    return _emit_bytes(setup, call, dest_off, MEM_SIZE, f"(void *)(buf + {dest_off})"), _text(shown)


def _fsoares_strlcpy(case: dict) -> tuple[str, dict] | None:
    if case["args"][0]["value"] != "dest":
        return None
    src = _bytes_of(case["args"][1]["value"])
    size = _int_arg(case, 2)
    buf = _fill(MEM_SIZE)
    number = _strlcpy(buf, src, size)
    literal = ",".join(str(byte) for byte in src + b"\x00")
    setup = _c_array("buf", _fill(MEM_SIZE)) + f"\n\tunsigned char src[] = {{{literal}}};"
    call = f"ft_strlcpy((char *)buf, (char *)src, {size})"
    return _emit_pair(setup, call, MEM_SIZE), _pair(number, bytes(buf))


def _fsoares_strlcat(case: dict) -> tuple[str, dict] | None:
    if case["args"][0]["value"] != "dest":
        return None
    orig = _bytes_of(case["args"][1]["value"])
    src = _bytes_of(case["args"][2]["value"])
    size = _int_arg(case, 3)
    buf = _fill(MEM_SIZE)
    _strcpy(buf, 0, orig)
    number = _strlcat(buf, src, size)
    window = (size // 16 + 1) * 16
    literal = ",".join(str(byte) for byte in src + b"\x00")
    setup = _c_array("buf", _fill(MEM_SIZE))
    setup += "\n" + "\n".join(
        f"\tbuf[{index}] = {byte};" for index, byte in enumerate(orig + b"\x00")
    )
    setup += f"\n\tunsigned char src[] = {{{literal}}};"
    call = f"ft_strlcat((char *)buf, (char *)src, {size})"
    return _emit_pair(setup, call, window), _pair(number, bytes(buf[:window]))


def _callback(name: str, mapper: bool) -> str | None:
    table = {
        ("add", True): "subject_add_map",
        ("add", False): "subject_add_iter",
        ("to_char_zero", True): "subject_zero_map",
        ("to_char_zero", False): "subject_zero_iter",
        ("&mapi", True): "subject_swap_map",
        ("&iter", False): "subject_swap_iter",
    }
    return table.get((name, mapper))


def _fsoares_map(case: dict) -> tuple[str, dict] | None:
    mapper = case["function"] == "ft_strmapi"
    fn = _callback(case["args"][1]["value"], mapper)
    if fn is None:
        return None
    text = case["args"][0]["value"]
    literal = text.replace("\\", "\\\\").replace('"', '\\"')
    if mapper:
        snippet = f"""
	char *text;
	char *oh = NULL;
	char *eh = NULL;
	begin_cap();
	text = ft_strmapi("{literal}", {fn});
	end_cap(&oh, &eh);
	emit_text(id, text, 1, oh, eh);
"""
    else:
        snippet = f"""
	char text[] = "{literal}";
	char *oh = NULL;
	char *eh = NULL;
	begin_cap();
	ft_striteri(text, {fn});
	end_cap(&oh, &eh);
	emit_text(id, text, 0, oh, eh);
"""
    return snippet, None


def _war_memset(case: dict) -> tuple[str, None] | None:
    char = _char_arg(case, 1)
    count = _int_arg(case, 2)
    setup = _c_array("buf", b"j" * 15)
    call = f"ft_memset(buf, {char}, {count})"
    return _capture_buffer(setup, call, 15, "mem's adress was not returned\n"), None


def _war_bzero(case: dict) -> tuple[str, None] | None:
    count = _int_arg(case, 1)
    setup = _c_array("buf", b"e" * 5)
    snippet = f"""
{setup}
	char *oh = NULL;
	char *eh = NULL;
	begin_cap();
	ft_bzero(buf, {count});
	write(1, buf, 5);
	end_cap(&oh, &eh);
	emit_void(id, oh, eh);
"""
    return snippet, None


def _war_memcpy(case: dict) -> tuple[str, None] | None:
    src = _bytes_of(case["args"][1]["value"])
    count = _int_arg(case, 2)
    literal = ",".join(str(byte) for byte in src)
    setup = _c_array("buf", b"j" * 30) + f"\n\tunsigned char src[] = {{{literal}}};"
    call = f"ft_memcpy(buf, src, {count})"
    return _capture_buffer(setup, call, 30, "dest's adress was not returned\n"), None


def _war_memmove(case: dict) -> tuple[str, None] | None:
    index = int(case.get("index") or "0")
    base = _bytes_of("lorem ipsum dolor sit amet")
    setup = _c_array("block", base)
    if index == 1:
        src = _bytes_of("consectetur")
        call = "ft_memmove(block + 1, src, 5)"
        extra = _c_array("src", src)
    elif index == 2:
        src = _bytes_of("con\x00sec\x00\x00te\x00tur")
        call = "ft_memmove(block + 1, src, 10)"
        extra = _c_array("src", src)
    elif index == 3:
        call = "ft_memmove(block + 1, block, 8)"
        extra = ""
    elif index == 4:
        call = "ft_memmove(block, block + 1, 8)"
        extra = ""
    elif index == 5:
        call = "ft_memmove(block, block + 1, 0)"
        extra = ""
    else:
        return None
    # Cases 4 and 5 print dest, which is block + 1, and the return checked is src.
    if index in {4, 5}:
        check_ptr = "block"
        printed = "block + 1"
    else:
        check_ptr = "block + 1"
        printed = "block + 1"
    body = f"""
{setup}
{extra}
	char *oh = NULL;
	char *eh = NULL;
	void *ret;
	begin_cap();
	ret = {call};
	if (ret != (void *){check_ptr})
		write(1, "dest's adress was not returned\\n", 31);
	write(1, {printed}, 22);
	end_cap(&oh, &eh);
	emit_void(id, oh, eh);
"""
    return body, None


def _war_base() -> bytes:
    buf = bytearray(15)
    buf[:6] = b"rrrrrr"
    return bytes(buf)


def _war_strl(case: dict, cat: bool) -> tuple[str, None] | None:
    src = _bytes_of(case["args"][1]["value"])
    size = _int_arg(case, 2)
    literal = ",".join(str(byte) for byte in src + b"\x00")
    setup = _c_array("buf", _war_base()) + f"\n\tunsigned char src[] = {{{literal}}};"
    name = "ft_strlcat" if cat else "ft_strlcpy"
    call = f"{name}((char *)buf, (char *)src, {size})"
    return _capture_size(setup, call, 15), None


def _war_strlcat(case: dict) -> tuple[str, None] | None:
    index = int(case.get("index") or "0")
    src = _bytes_of(case["args"][1]["value"])
    size = _int_arg(case, 2)
    buf = bytearray(_war_base())
    if index == 1:
        buf[11] = ord("a")
    elif index == 3:
        buf[0] = 0
        buf[11] = ord("a")
    elif index == 4:
        buf[14] = ord("a")
    elif index in {5, 6, 8}:
        buf[10] = ord("a")
    elif index == 7:
        buf = bytearray(b"r" * 15)
    elif index == 9:
        buf = bytearray(b"r" * 14 + b"\x00")
    elif index != 2:
        return None
    literal = ",".join(str(byte) for byte in src + b"\x00")
    setup = _c_array("buf", bytes(buf)) + f"\n\tunsigned char src[] = {{{literal}}};"
    call = f"ft_strlcat((char *)buf, (char *)src, {size})"
    return _capture_size(setup, call, 15), None


def _war_map(case: dict) -> tuple[str, None] | None:
    mapper = case["function"] == "ft_strmapi"
    fn = "subject_swap_map" if mapper else "subject_swap_iter"
    if mapper:
        snippet = f"""
	char str[12];
	char *out;
	char *oh = NULL;
	char *eh = NULL;
	memcpy(str, "LoReM iPsUm", 12);
	begin_cap();
	out = ft_strmapi(str, {fn});
	if (out)
		write(1, out, 11);
	if (out == str)
		write(1, "\\nA new string was not returned", 30);
	if (out && out[11] != '\\0')
		write(1, "\\nString is not null terminated", 30);
	end_cap(&oh, &eh);
	free(out);
	emit_void(id, oh, eh);
"""
    else:
        snippet = f"""
	char str[12];
	char *oh = NULL;
	char *eh = NULL;
	memcpy(str, "LoReM iPsUm", 12);
	begin_cap();
	ft_striteri(str, {fn});
	write(1, str, 11);
	end_cap(&oh, &eh);
	emit_void(id, oh, eh);
"""
    return snippet, None


def _pad(text: bytes, size: int) -> str:
    raw = text + b"\x00" * size
    return raw[:size].decode("latin1")


def _named_strings(case: dict) -> dict | None:
    args = case.get("args") or []
    if len(args) < 3:
        return None
    values = [arg.get("value") for arg in args]
    function = case["function"]
    ready = deepcopy(case)
    if function == "ft_memcmp" and values[:2] in (["s1", "s2"], ["s2", "s1"]):
        count = int(values[2])
        if count == 10:
            left, right = _pad(b"teste", 20), _pad(b"test", 20)
        elif count == 5:
            left, right = _pad(b"abcdef", 20), _pad(b"abc\xfdxx", 20)
        elif count == 7:
            left, right = _pad(b"abc\x00ef", 20), _pad(b"abc\x00xx", 20)
        else:
            return None
        pair = (left, right) if values[0] == "s1" else (right, left)
        ready["args"] = [
            {"type": "str", "value": pair[0]},
            {"type": "str", "value": pair[1]},
            case["args"][2],
        ]
        return ready
    if function == "ft_strncmp" and values[0] == "(char *)s1":
        count = int(values[2])
        if count == 5:
            left, right = _pad(b"abcdef", 10), _pad(b"abc\xfdxx", 10)
        elif count == 7:
            left, right = _pad(b"abc\x00ef", 10), _pad(b"abc\x00xx", 10)
        else:
            return None
        ready["args"] = [
            {"type": "str", "value": left},
            {"type": "str", "value": right},
            case["args"][2],
        ]
        return ready
    if function == "ft_strnstr" and values[0] == "empty":
        ready["args"] = [
            {"type": "str", "value": _pad(b"\x00a", 10)},
            case["args"][1],
            case["args"][2],
        ]
        return ready
    if function == "ft_strnstr" and values[0] == "(char *)s1":
        count = int(values[2])
        if count in {3, 4, 5}:
            left, right = _pad(b"abcdef", 10), _pad(b"abc\xfdxx", 10)
        elif count == 7:
            left, right = _pad(b"abc\x00ef", 10), _pad(b"abc\x00xx", 10)
        else:
            return None
        ready["args"] = [
            {"type": "str", "value": left},
            {"type": "str", "value": right},
            case["args"][2],
        ]
        return ready
    return None
