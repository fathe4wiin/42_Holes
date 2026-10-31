"""Calls taken from the libft subject when the catalog has no literal input."""


def _case(function: str, name: str, call: str, expected: dict, snippet: str) -> dict:
    return {
        "id": f"subject/{function}/{name}",
        "function": function,
        "kind": "expression",
        "suite": "subject",
        "call": call,
        "args": [],
        "expected": expected,
        "part": "",
        "snippet": snippet,
    }


def subject_cases() -> dict[str, list[dict]]:
    """One list of subject calls per function."""
    groups: dict[str, list[dict]] = {
        "ft_calloc": [
            {
                "id": "subject/ft_calloc/both-zero",
                "function": "ft_calloc",
                "kind": "compare_libc",
                "suite": "subject",
                "call": "ft_calloc(0, 0)",
                "args": [{"type": "int", "value": "0"}, {"type": "int", "value": "0"}],
                "expected": None,
                "part": "part 1",
            }
        ],
        "ft_memset": [
            _case(
                "ft_memset",
                "fill",
                "ft_memset(buf, 'A', 4) on 8 bytes of 0xA5",
                {"type": "str", "value": "AAAA\xa5\xa5\xa5\xa5"},
                """
	unsigned char buf[8];
	void *ret;
	char *oh = NULL;
	char *eh = NULL;
	memset(buf, 0xA5, sizeof buf);
	begin_cap();
	ret = ft_memset(buf, 'A', 4);
	end_cap(&oh, &eh);
	if (ret != (void *)buf)
	{
		printf("%s\\tok\\tbad\\treturn is not the buffer\\t%s\\t%s\\n",
			id, oh ? oh : "", eh ? eh : "");
		free(oh);
		free(eh);
		return;
	}
	emit_raw(id, buf, sizeof buf, oh, eh);
""",
            ),
            _case(
                "ft_memset",
                "zero-count",
                "ft_memset(buf, 'A', 0) leaves the buffer alone",
                {"type": "str", "value": "\xa5\xa5\xa5\xa5"},
                """
	unsigned char buf[4];
	void *ret;
	char *oh = NULL;
	char *eh = NULL;
	memset(buf, 0xA5, sizeof buf);
	begin_cap();
	ret = ft_memset(buf, 'A', 0);
	end_cap(&oh, &eh);
	if (ret != (void *)buf)
	{
		printf("%s\\tok\\tbad\\treturn is not the buffer\\t%s\\t%s\\n",
			id, oh ? oh : "", eh ? eh : "");
		free(oh);
		free(eh);
		return;
	}
	emit_raw(id, buf, sizeof buf, oh, eh);
""",
            ),
        ],
        "ft_bzero": [
            _case(
                "ft_bzero",
                "three",
                "ft_bzero(buf, 3) on 8 bytes of 0xA5",
                {"type": "str", "value": "\x00\x00\x00\xa5\xa5\xa5\xa5\xa5"},
                """
	unsigned char buf[8];
	char *oh = NULL;
	char *eh = NULL;
	memset(buf, 0xA5, sizeof buf);
	begin_cap();
	ft_bzero(buf, 3);
	end_cap(&oh, &eh);
	emit_raw(id, buf, sizeof buf, oh, eh);
""",
            )
        ],
        "ft_memcpy": [
            _case(
                "ft_memcpy",
                "four",
                "ft_memcpy(dst, \"abcd...\", 4)",
                {"type": "str", "value": "abcd\xa5\xa5\xa5\xa5"},
                """
	unsigned char dst[8];
	unsigned char src[8] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'};
	void *ret;
	char *oh = NULL;
	char *eh = NULL;
	memset(dst, 0xA5, sizeof dst);
	begin_cap();
	ret = ft_memcpy(dst, src, 4);
	end_cap(&oh, &eh);
	if (ret != (void *)dst)
	{
		printf("%s\\tok\\tbad\\treturn is not the destination\\t%s\\t%s\\n",
			id, oh ? oh : "", eh ? eh : "");
		free(oh);
		free(eh);
		return;
	}
	emit_raw(id, dst, sizeof dst, oh, eh);
""",
            )
        ],
        "ft_memmove": [
            _case(
                "ft_memmove",
                "overlap-forward",
                "ft_memmove(buf + 2, buf, 4) on \"12345678\"",
                {"type": "str", "value": "12123478"},
                """
	unsigned char buf[8] = {'1', '2', '3', '4', '5', '6', '7', '8'};
	void *ret;
	char *oh = NULL;
	char *eh = NULL;
	begin_cap();
	ret = ft_memmove(buf + 2, buf, 4);
	end_cap(&oh, &eh);
	if (ret != (void *)(buf + 2))
	{
		printf("%s\\tok\\tbad\\treturn is not the destination\\t%s\\t%s\\n",
			id, oh ? oh : "", eh ? eh : "");
		free(oh);
		free(eh);
		return;
	}
	emit_raw(id, buf, sizeof buf, oh, eh);
""",
            ),
            _case(
                "ft_memmove",
                "overlap-back",
                "ft_memmove(buf, buf + 2, 4) on \"12345678\"",
                {"type": "str", "value": "34565678"},
                """
	unsigned char buf[8] = {'1', '2', '3', '4', '5', '6', '7', '8'};
	void *ret;
	char *oh = NULL;
	char *eh = NULL;
	begin_cap();
	ret = ft_memmove(buf, buf + 2, 4);
	end_cap(&oh, &eh);
	if (ret != (void *)buf)
	{
		printf("%s\\tok\\tbad\\treturn is not the destination\\t%s\\t%s\\n",
			id, oh ? oh : "", eh ? eh : "");
		free(oh);
		free(eh);
		return;
	}
	emit_raw(id, buf, sizeof buf, oh, eh);
""",
            ),
        ],
        "ft_strlcpy": [
            _case(
                "ft_strlcpy",
                "fits",
                "ft_strlcpy(dst, \"hi\", 8)",
                {"type": "pair", "value": {"n": "2", "bytes": "hi\x00xxxxx"}},
                """
	unsigned char dst[8];
	size_t n;
	char *oh = NULL;
	char *eh = NULL;
	memset(dst, 'x', sizeof dst);
	begin_cap();
	n = ft_strlcpy((char *)dst, "hi", 8);
	end_cap(&oh, &eh);
	emit_pair(id, n, dst, sizeof dst, oh, eh);
""",
            ),
            _case(
                "ft_strlcpy",
                "size-one",
                "ft_strlcpy(dst, \"hi\", 1) writes only the terminator",
                {"type": "pair", "value": {"n": "2", "bytes": "\x00xxxxxxx"}},
                """
	unsigned char dst[8];
	size_t n;
	char *oh = NULL;
	char *eh = NULL;
	memset(dst, 'x', sizeof dst);
	begin_cap();
	n = ft_strlcpy((char *)dst, "hi", 1);
	end_cap(&oh, &eh);
	emit_pair(id, n, dst, sizeof dst, oh, eh);
""",
            ),
        ],
        "ft_strlcat": [
            _case(
                "ft_strlcat",
                "append",
                "ft_strlcat(dst, \"cd\", 8) with dst \"ab\"",
                {"type": "pair", "value": {"n": "4", "bytes": "abcd\x00xxx"}},
                """
	unsigned char dst[8];
	size_t n;
	char *oh = NULL;
	char *eh = NULL;
	memset(dst, 'x', sizeof dst);
	dst[0] = 'a';
	dst[1] = 'b';
	dst[2] = '\\0';
	begin_cap();
	n = ft_strlcat((char *)dst, "cd", 8);
	end_cap(&oh, &eh);
	emit_pair(id, n, dst, sizeof dst, oh, eh);
""",
            ),
            _case(
                "ft_strlcat",
                "no-room",
                "ft_strlcat(dst, \"cd\", 3) with dst \"ab\" does not write",
                {"type": "pair", "value": {"n": "4", "bytes": "ab\x00xxxxx"}},
                """
	unsigned char dst[8];
	size_t n;
	char *oh = NULL;
	char *eh = NULL;
	memset(dst, 'x', sizeof dst);
	dst[0] = 'a';
	dst[1] = 'b';
	dst[2] = '\\0';
	begin_cap();
	n = ft_strlcat((char *)dst, "cd", 3);
	end_cap(&oh, &eh);
	emit_pair(id, n, dst, sizeof dst, oh, eh);
""",
            ),
        ],
        "ft_strmapi": [
            _case(
                "ft_strmapi",
                "upper",
                "ft_strmapi(\"abC\", upper)",
                {"type": "str", "value": "ABC"},
                """
	char *text;
	char *oh = NULL;
	char *eh = NULL;
	begin_cap();
	text = ft_strmapi("abC", subject_upper);
	end_cap(&oh, &eh);
	emit_text(id, text, 1, oh, eh);
""",
            ),
            _case(
                "ft_strmapi",
                "empty",
                "ft_strmapi(\"\", upper)",
                {"type": "str", "value": ""},
                """
	char *text;
	char *oh = NULL;
	char *eh = NULL;
	begin_cap();
	text = ft_strmapi("", subject_upper);
	end_cap(&oh, &eh);
	emit_text(id, text, 1, oh, eh);
""",
            ),
        ],
        "ft_striteri": [
            _case(
                "ft_striteri",
                "even",
                "ft_striteri(\"abcd\", upper on even indexes)",
                {"type": "str", "value": "AbCd"},
                """
	char text[] = "abcd";
	char *oh = NULL;
	char *eh = NULL;
	begin_cap();
	ft_striteri(text, subject_star);
	end_cap(&oh, &eh);
	emit_text(id, text, 0, oh, eh);
""",
            )
        ],
        "ft_lstnew": [
            _case(
                "ft_lstnew",
                "string",
                "ft_lstnew(text) keeps that pointer and next is NULL",
                {"type": "int", "value": "1"},
                """
	char text[] = "hi";
	t_list *node;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	begin_cap();
	node = ft_lstnew(text);
	end_cap(&oh, &eh);
	ok = node && node->content == (void *)text && node->next == NULL;
	free(node);
	emit_int(id, ok, oh, eh);
""",
            ),
            _case(
                "ft_lstnew",
                "null",
                "ft_lstnew(NULL) stores NULL and next is NULL",
                {"type": "int", "value": "1"},
                """
	t_list *node;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	begin_cap();
	node = ft_lstnew(NULL);
	end_cap(&oh, &eh);
	ok = node && node->content == NULL && node->next == NULL;
	free(node);
	emit_int(id, ok, oh, eh);
""",
            ),
        ],
        "ft_lstadd_front": [
            _case(
                "ft_lstadd_front",
                "front",
                "ft_lstadd_front puts the new node first",
                {"type": "int", "value": "1"},
                """
	t_list second;
	t_list first;
	t_list *list;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	second.content = (void *)2;
	second.next = NULL;
	first.content = (void *)1;
	first.next = NULL;
	list = &second;
	begin_cap();
	ft_lstadd_front(&list, &first);
	end_cap(&oh, &eh);
	ok = list == &first && first.next == &second && second.next == NULL;
	emit_int(id, ok, oh, eh);
""",
            )
        ],
        "ft_lstsize": [
            _case(
                "ft_lstsize",
                "empty",
                "ft_lstsize(NULL)",
                {"type": "int", "value": "0"},
                """
	char *oh = NULL;
	char *eh = NULL;
	int n;
	begin_cap();
	n = ft_lstsize(NULL);
	end_cap(&oh, &eh);
	emit_int(id, n, oh, eh);
""",
            ),
            _case(
                "ft_lstsize",
                "two",
                "ft_lstsize of two nodes",
                {"type": "int", "value": "2"},
                """
	t_list second;
	t_list first;
	char *oh = NULL;
	char *eh = NULL;
	int n;
	second.content = (void *)2;
	second.next = NULL;
	first.content = (void *)1;
	first.next = &second;
	begin_cap();
	n = ft_lstsize(&first);
	end_cap(&oh, &eh);
	emit_int(id, n, oh, eh);
""",
            ),
        ],
        "ft_lstlast": [
            _case(
                "ft_lstlast",
                "empty",
                "ft_lstlast(NULL)",
                {"type": "int", "value": "1"},
                """
	t_list *node;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	begin_cap();
	node = ft_lstlast(NULL);
	end_cap(&oh, &eh);
	ok = node == NULL;
	emit_int(id, ok, oh, eh);
""",
            ),
            _case(
                "ft_lstlast",
                "second",
                "ft_lstlast returns the second node",
                {"type": "int", "value": "1"},
                """
	t_list second;
	t_list first;
	t_list *node;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	second.content = (void *)2;
	second.next = NULL;
	first.content = (void *)1;
	first.next = &second;
	begin_cap();
	node = ft_lstlast(&first);
	end_cap(&oh, &eh);
	ok = node == &second;
	emit_int(id, ok, oh, eh);
""",
            ),
        ],
        "ft_lstadd_back": [
            _case(
                "ft_lstadd_back",
                "empty",
                "ft_lstadd_back on an empty list",
                {"type": "int", "value": "1"},
                """
	t_list node;
	t_list *list;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	node.content = (void *)1;
	node.next = NULL;
	list = NULL;
	begin_cap();
	ft_lstadd_back(&list, &node);
	end_cap(&oh, &eh);
	ok = list == &node && node.next == NULL;
	emit_int(id, ok, oh, eh);
""",
            ),
            _case(
                "ft_lstadd_back",
                "end",
                "ft_lstadd_back appends after the first node",
                {"type": "int", "value": "1"},
                """
	t_list second;
	t_list first;
	t_list *list;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	second.content = (void *)2;
	second.next = NULL;
	first.content = (void *)1;
	first.next = NULL;
	list = &first;
	begin_cap();
	ft_lstadd_back(&list, &second);
	end_cap(&oh, &eh);
	ok = list == &first && first.next == &second && second.next == NULL;
	emit_int(id, ok, oh, eh);
""",
            ),
        ],
        "ft_lstdelone": [
            _case(
                "ft_lstdelone",
                "one",
                "ft_lstdelone frees the content with del, then the node",
                {"type": "int", "value": "1"},
                """
	int *number;
	t_list *node;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	number = malloc(sizeof(int));
	*number = 7;
	node = malloc(sizeof(t_list));
	node->content = number;
	node->next = NULL;
	subject_frees = 0;
	begin_cap();
	ft_lstdelone(node, subject_free);
	end_cap(&oh, &eh);
	ok = subject_frees == 1;
	emit_int(id, ok, oh, eh);
""",
            )
        ],
        "ft_lstclear": [
            _case(
                "ft_lstclear",
                "two",
                "ft_lstclear frees both nodes and sets the pointer to NULL",
                {"type": "int", "value": "1"},
                """
	t_list *list;
	t_list *second;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	list = malloc(sizeof(t_list));
	second = malloc(sizeof(t_list));
	list->content = malloc(1);
	second->content = malloc(1);
	list->next = second;
	second->next = NULL;
	subject_frees = 0;
	begin_cap();
	ft_lstclear(&list, subject_free);
	end_cap(&oh, &eh);
	ok = list == NULL && subject_frees == 2;
	emit_int(id, ok, oh, eh);
""",
            )
        ],
        "ft_lstiter": [
            _case(
                "ft_lstiter",
                "add",
                "ft_lstiter adds 1 to each int",
                {"type": "int", "value": "1"},
                """
	int first_n;
	int second_n;
	t_list second;
	t_list first;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	first_n = 1;
	second_n = 2;
	second.content = &second_n;
	second.next = NULL;
	first.content = &first_n;
	first.next = &second;
	begin_cap();
	ft_lstiter(&first, subject_add);
	end_cap(&oh, &eh);
	ok = first_n == 2 && second_n == 3;
	emit_int(id, ok, oh, eh);
""",
            )
        ],
        "ft_lstmap": [
            _case(
                "ft_lstmap",
                "copy",
                "ft_lstmap builds a new list and leaves the old one",
                {"type": "int", "value": "1"},
                """
	t_list *old;
	t_list *copy;
	char *oh = NULL;
	char *eh = NULL;
	int ok;
	old = ft_lstnew(strdup("ab"));
	old->next = ft_lstnew(strdup("cd"));
	begin_cap();
	copy = ft_lstmap(old, subject_dup, subject_free);
	end_cap(&oh, &eh);
	ok = copy && copy->content && strcmp((char *)copy->content, "ab") == 0
		&& copy->next && strcmp((char *)copy->next->content, "cd") == 0
		&& copy->next->next == NULL
		&& strcmp((char *)old->content, "ab") == 0
		&& copy->content != old->content;
	ft_lstclear(&copy, subject_free);
	ft_lstclear(&old, subject_free);
	emit_int(id, ok, oh, eh);
""",
            )
        ],
    }
    for function, extra in _edge_cases().items():
        groups.setdefault(function, []).extend(extra)
    for function, extra in _breaker_cases().items():
        groups.setdefault(function, []).extend(extra)
    return groups


def _ub_case(function: str, name: str, call: str, snippet: str, mode: str) -> dict:
    return {
        "id": f"subject/{function}/{name}",
        "function": function,
        "kind": "expression",
        "suite": "subject",
        "call": call,
        "args": [],
        "expected": {"type": "ub", "value": mode},
        "part": "",
        "snippet": snippet,
    }


def _guard_case(function: str, name: str, call: str, statement: str) -> dict:
    snippet = (
        "\tint ft_sig;\n"
        f"\tRUN_PROBE(ft_sig, {{ {statement} }});\n"
        "\temit_guard(id, ft_sig);\n"
    )
    return {
        "id": f"subject/{function}/{name}",
        "function": function,
        "kind": "expression",
        "suite": "subject",
        "call": call,
        "args": [],
        "expected": {"type": "guard", "value": "defined-by-probe"},
        "part": "",
        "snippet": snippet,
    }


def _crash_case(function: str, name: str, call: str, libc: str, ft: str) -> dict:
    snippet = (
        "\tint libc_sig;\n"
        "\tint ft_sig;\n"
        f"\tRUN_PROBE(libc_sig, {{ {libc} }});\n"
        f"\tRUN_PROBE(ft_sig, {{ {ft} }});\n"
        "\temit_ub(id, libc_sig, ft_sig);\n"
    )
    return _ub_case(function, name, call, snippet, "crash")


def _value_case(function: str, name: str, call: str, number: str, expected: str) -> dict:
    return {
        "id": f"subject/{function}/{name}",
        "function": function,
        "kind": "expression",
        "suite": "subject",
        "call": call,
        "args": [{"type": "int", "value": number}],
        "expected": {"type": "int", "value": expected},
        "part": "",
    }


_EXTRAS = (
    (-2, "-2"),
    (-128, "-128"),
    (-129, "-129"),
    (-255, "-255"),
    (-256, "-256"),
    (256, "256"),
    (512, "512"),
    (1024, "1024"),
    (4096, "4096"),
    (2147483647, "2147483647"),
    (-2147483648, "(-2147483647 - 1)"),
)


def _int_probe(function: str, number: int, literal: str, mode: str) -> dict:
    libc = function[3:]
    snippet = (
        "\tint libc_sig;\n"
        "\tint ft_sig;\n"
        "\tint libc_val;\n"
        "\tint ft_val;\n"
        "\tint (*std_fn)(int);\n"
        "\tint (*ft_fn)(int);\n"
        "\tlibc_val = 0;\n"
        "\tft_val = 0;\n"
        f"\tstd_fn = {libc};\n"
        f"\tft_fn = {function};\n"
        f"\tlibc_sig = probe_int(std_fn, {literal}, &libc_val);\n"
        f"\tft_sig = probe_int(ft_fn, {literal}, &ft_val);\n"
        "\temit_ub_vals(id, libc_sig, ft_sig, libc_val, ft_val);\n"
    )
    slug = str(number) if number >= 0 else f"m{-number}"
    return _ub_case(function, f"extra-{slug}", f"{function}({number})", snippet, mode)


def _edge_cases() -> dict[str, list[dict]]:
    """Subject rules first, then libc crash probes and undefined edges.

    A part 1 crash probe compares the signal with libc.
    libc crashed and the function returned is a warning.
    The function crashed and libc did not is a failure.
    """
    groups: dict[str, list[dict]] = {
        "ft_strlen": [
            _crash_case(
                "ft_strlen",
                "null",
                "ft_strlen(NULL)",
                "const char *s = 0; size_t (*p)(const char *) = (strlen); volatile size_t n = p(s); (void)n;",
                "const char *s = 0; size_t (*p)(const char *) = ft_strlen; volatile size_t n = p(s); (void)n;",
            )
        ],
        "ft_memset": [
            _crash_case(
                "ft_memset",
                "null-zero",
                "ft_memset(NULL, 0, 0)",
                "char *s = 0; volatile size_t n = 0; void *(*p)(void *, int, size_t) = (memset); volatile void *r = p(s, 0, n); (void)r;",
                "char *s = 0; volatile size_t n = 0; void *(*p)(void *, int, size_t) = ft_memset; volatile void *r = p(s, 0, n); (void)r;",
            ),
            _crash_case(
                "ft_memset",
                "null-one",
                "ft_memset(NULL, 'a', 1)",
                "char *s = 0; void *(*p)(void *, int, size_t) = (memset); volatile void *r = p(s, 'a', 1); (void)r;",
                "char *s = 0; void *(*p)(void *, int, size_t) = ft_memset; volatile void *r = p(s, 'a', 1); (void)r;",
            ),
        ],
        "ft_bzero": [
            _crash_case(
                "ft_bzero",
                "null-zero",
                "ft_bzero(NULL, 0)",
                "void bzero(void *, size_t); char *s = 0; volatile size_t n = 0; void (*p)(void *, size_t) = bzero; p(s, n);",
                "char *s = 0; volatile size_t n = 0; void (*p)(void *, size_t) = ft_bzero; p(s, n);",
            ),
            _crash_case(
                "ft_bzero",
                "null-one",
                "ft_bzero(NULL, 1)",
                "void bzero(void *, size_t); char *s = 0; void (*p)(void *, size_t) = bzero; p(s, 1);",
                "char *s = 0; void (*p)(void *, size_t) = ft_bzero; p(s, 1);",
            ),
        ],
        "ft_memcpy": [
            _crash_case(
                "ft_memcpy",
                "null-zero",
                "ft_memcpy(NULL, NULL, 0)",
                "char *s = 0; volatile size_t n = 0; void *(*p)(void *, const void *, size_t) = (memcpy); volatile void *r = p(s, s, n); (void)r;",
                "char *s = 0; volatile size_t n = 0; void *(*p)(void *, const void *, size_t) = ft_memcpy; volatile void *r = p(s, s, n); (void)r;",
            ),
            _crash_case(
                "ft_memcpy",
                "null-two",
                'ft_memcpy(NULL, "ab", 2)',
                'char *s = 0; void *(*p)(void *, const void *, size_t) = (memcpy); volatile void *r = p(s, "ab", 2); (void)r;',
                'char *s = 0; void *(*p)(void *, const void *, size_t) = ft_memcpy; volatile void *r = p(s, "ab", 2); (void)r;',
            ),
        ],
        "ft_memmove": [
            _crash_case(
                "ft_memmove",
                "null-zero",
                "ft_memmove(NULL, NULL, 0)",
                "char *s = 0; volatile size_t n = 0; void *(*p)(void *, const void *, size_t) = (memmove); volatile void *r = p(s, s, n); (void)r;",
                "char *s = 0; volatile size_t n = 0; void *(*p)(void *, const void *, size_t) = ft_memmove; volatile void *r = p(s, s, n); (void)r;",
            ),
            _crash_case(
                "ft_memmove",
                "null-two",
                'ft_memmove(NULL, "ab", 2)',
                'char *s = 0; void *(*p)(void *, const void *, size_t) = (memmove); volatile void *r = p(s, "ab", 2); (void)r;',
                'char *s = 0; void *(*p)(void *, const void *, size_t) = ft_memmove; volatile void *r = p(s, "ab", 2); (void)r;',
            ),
        ],
        "ft_strlcpy": [
            _crash_case(
                "ft_strlcpy",
                "both-null",
                "ft_strlcpy(NULL, NULL, 0)",
                "size_t strlcpy(char *, const char *, size_t); char *d = 0; const char *s = 0; volatile size_t n = 0; size_t (*p)(char *, const char *, size_t) = strlcpy; volatile size_t r = p(d, s, n); (void)r;",
                "char *d = 0; const char *s = 0; volatile size_t n = 0; size_t (*p)(char *, const char *, size_t) = ft_strlcpy; volatile size_t r = p(d, s, n); (void)r;",
            ),
            _crash_case(
                "ft_strlcpy",
                "dest-null",
                'ft_strlcpy(NULL, "abc", 4)',
                'size_t strlcpy(char *, const char *, size_t); char *d = 0; size_t (*p)(char *, const char *, size_t) = strlcpy; volatile size_t r = p(d, "abc", 4); (void)r;',
                'char *d = 0; size_t (*p)(char *, const char *, size_t) = ft_strlcpy; volatile size_t r = p(d, "abc", 4); (void)r;',
            ),
            _crash_case(
                "ft_strlcpy",
                "src-null",
                "ft_strlcpy(dst, NULL, 4)",
                "size_t strlcpy(char *, const char *, size_t); char d[8]; const char *s = 0; d[0] = 'h'; d[1] = 'i'; d[2] = 0; size_t (*p)(char *, const char *, size_t) = strlcpy; volatile size_t r = p(d, s, 4); (void)r;",
                "char d[8]; const char *s = 0; d[0] = 'h'; d[1] = 'i'; d[2] = 0; size_t (*p)(char *, const char *, size_t) = ft_strlcpy; volatile size_t r = p(d, s, 4); (void)r;",
            ),
        ],
        "ft_strlcat": [
            _crash_case(
                "ft_strlcat",
                "both-null",
                "ft_strlcat(NULL, NULL, 0)",
                "size_t strlcat(char *, const char *, size_t); char *d = 0; const char *s = 0; volatile size_t n = 0; size_t (*p)(char *, const char *, size_t) = strlcat; volatile size_t r = p(d, s, n); (void)r;",
                "char *d = 0; const char *s = 0; volatile size_t n = 0; size_t (*p)(char *, const char *, size_t) = ft_strlcat; volatile size_t r = p(d, s, n); (void)r;",
            ),
            _crash_case(
                "ft_strlcat",
                "dest-null",
                'ft_strlcat(NULL, "abc", 5)',
                'size_t strlcat(char *, const char *, size_t); char *d = 0; size_t (*p)(char *, const char *, size_t) = strlcat; volatile size_t r = p(d, "abc", 5); (void)r;',
                'char *d = 0; size_t (*p)(char *, const char *, size_t) = ft_strlcat; volatile size_t r = p(d, "abc", 5); (void)r;',
            ),
            _crash_case(
                "ft_strlcat",
                "src-null",
                "ft_strlcat(dst, NULL, 8)",
                "size_t strlcat(char *, const char *, size_t); char d[16]; const char *s = 0; d[0] = 'h'; d[1] = 'i'; d[2] = 0; size_t (*p)(char *, const char *, size_t) = strlcat; volatile size_t r = p(d, s, 8); (void)r;",
                "char d[16]; const char *s = 0; d[0] = 'h'; d[1] = 'i'; d[2] = 0; size_t (*p)(char *, const char *, size_t) = ft_strlcat; volatile size_t r = p(d, s, 8); (void)r;",
            ),
        ],
        "ft_strchr": [
            _crash_case(
                "ft_strchr",
                "null-a",
                "ft_strchr(NULL, 'a')",
                "const char *s = 0; char *(*p)(const char *, int) = (strchr); volatile void *r = p(s, 'a'); (void)r;",
                "const char *s = 0; char *(*p)(const char *, int) = ft_strchr; volatile void *r = p(s, 'a'); (void)r;",
            ),
            _crash_case(
                "ft_strchr",
                "null-zero",
                "ft_strchr(NULL, 0)",
                "const char *s = 0; char *(*p)(const char *, int) = (strchr); volatile void *r = p(s, 0); (void)r;",
                "const char *s = 0; char *(*p)(const char *, int) = ft_strchr; volatile void *r = p(s, 0); (void)r;",
            ),
        ],
        "ft_strrchr": [
            _crash_case(
                "ft_strrchr",
                "null-a",
                "ft_strrchr(NULL, 'a')",
                "const char *s = 0; char *(*p)(const char *, int) = (strrchr); volatile void *r = p(s, 'a'); (void)r;",
                "const char *s = 0; char *(*p)(const char *, int) = ft_strrchr; volatile void *r = p(s, 'a'); (void)r;",
            )
        ],
        "ft_strncmp": [
            _crash_case(
                "ft_strncmp",
                "both-null",
                "ft_strncmp(NULL, NULL, 0)",
                "const char *s = 0; volatile size_t n = 0; int (*p)(const char *, const char *, size_t) = (strncmp); volatile int r = p(s, s, n); (void)r;",
                "const char *s = 0; volatile size_t n = 0; int (*p)(const char *, const char *, size_t) = ft_strncmp; volatile int r = p(s, s, n); (void)r;",
            ),
            _crash_case(
                "ft_strncmp",
                "left-null",
                'ft_strncmp(NULL, "a", 1)',
                'const char *s = 0; int (*p)(const char *, const char *, size_t) = (strncmp); volatile int r = p(s, "a", 1); (void)r;',
                'const char *s = 0; int (*p)(const char *, const char *, size_t) = ft_strncmp; volatile int r = p(s, "a", 1); (void)r;',
            ),
            _crash_case(
                "ft_strncmp",
                "right-null",
                'ft_strncmp("a", NULL, 1)',
                'const char *s = 0; int (*p)(const char *, const char *, size_t) = (strncmp); volatile int r = p("a", s, 1); (void)r;',
                'const char *s = 0; int (*p)(const char *, const char *, size_t) = ft_strncmp; volatile int r = p("a", s, 1); (void)r;',
            ),
        ],
        "ft_memchr": [
            _crash_case(
                "ft_memchr",
                "null-zero",
                "ft_memchr(NULL, 'a', 0)",
                "char *s = 0; volatile size_t n = 0; void *(*p)(const void *, int, size_t) = (memchr); volatile void *r = p(s, 'a', n); (void)r;",
                "char *s = 0; volatile size_t n = 0; void *(*p)(const void *, int, size_t) = ft_memchr; volatile void *r = p(s, 'a', n); (void)r;",
            ),
            _crash_case(
                "ft_memchr",
                "null-one",
                "ft_memchr(NULL, 'a', 1)",
                "char *s = 0; void *(*p)(const void *, int, size_t) = (memchr); volatile void *r = p(s, 'a', 1); (void)r;",
                "char *s = 0; void *(*p)(const void *, int, size_t) = ft_memchr; volatile void *r = p(s, 'a', 1); (void)r;",
            ),
        ],
        "ft_memcmp": [
            _crash_case(
                "ft_memcmp",
                "null-zero",
                "ft_memcmp(NULL, NULL, 0)",
                "char *s = 0; volatile size_t n = 0; int (*p)(const void *, const void *, size_t) = (memcmp); volatile int r = p(s, s, n); (void)r;",
                "char *s = 0; volatile size_t n = 0; int (*p)(const void *, const void *, size_t) = ft_memcmp; volatile int r = p(s, s, n); (void)r;",
            ),
            _crash_case(
                "ft_memcmp",
                "null-one",
                'ft_memcmp(NULL, "a", 1)',
                'char *s = 0; int (*p)(const void *, const void *, size_t) = (memcmp); volatile int r = p(s, "a", 1); (void)r;',
                'char *s = 0; int (*p)(const void *, const void *, size_t) = ft_memcmp; volatile int r = p(s, "a", 1); (void)r;',
            ),
        ],
        "ft_strnstr": [
            _crash_case(
                "ft_strnstr",
                "null-zero",
                'ft_strnstr(NULL, "a", 0)',
                'char *strnstr(const char *, const char *, size_t); const char *s = 0; volatile size_t n = 0; char *(*p)(const char *, const char *, size_t) = strnstr; volatile void *r = p(s, "a", n); (void)r;',
                'const char *s = 0; volatile size_t n = 0; char *(*p)(const char *, const char *, size_t) = ft_strnstr; volatile void *r = p(s, "a", n); (void)r;',
            ),
            _crash_case(
                "ft_strnstr",
                "null-one",
                'ft_strnstr(NULL, "a", 1)',
                'char *strnstr(const char *, const char *, size_t); const char *s = 0; char *(*p)(const char *, const char *, size_t) = strnstr; volatile void *r = p(s, "a", 1); (void)r;',
                'const char *s = 0; char *(*p)(const char *, const char *, size_t) = ft_strnstr; volatile void *r = p(s, "a", 1); (void)r;',
            ),
            _crash_case(
                "ft_strnstr",
                "needle-null",
                'ft_strnstr("abc", NULL, 3)',
                'char *strnstr(const char *, const char *, size_t); const char *s = 0; char *(*p)(const char *, const char *, size_t) = strnstr; volatile void *r = p("abc", s, 3); (void)r;',
                'const char *s = 0; char *(*p)(const char *, const char *, size_t) = ft_strnstr; volatile void *r = p("abc", s, 3); (void)r;',
            ),
        ],
        "ft_atoi": [
            _crash_case(
                "ft_atoi",
                "null",
                "ft_atoi(NULL)",
                "const char *s = 0; int (*p)(const char *) = (atoi); volatile int r = p(s); (void)r;",
                "const char *s = 0; int (*p)(const char *) = ft_atoi; volatile int r = p(s); (void)r;",
            )
        ],
        "ft_strdup": [
            _crash_case(
                "ft_strdup",
                "null",
                "ft_strdup(NULL)",
                "const char *s = 0; char *(*p)(const char *) = (strdup); volatile void *r = p(s); (void)r;",
                "const char *s = 0; char *(*p)(const char *) = ft_strdup; volatile void *r = p(s); (void)r;",
            )
        ],
        "ft_calloc": [
            _ub_case(
                "ft_calloc",
                "overflow",
                "ft_calloc((size_t)-1, (size_t)-1)",
                """
	int libc_sig;
	int ft_sig;
	int libc_null;
	int ft_null;
	void *(*std_fn)(size_t, size_t);
	void *(*ft_fn)(size_t, size_t);
	libc_null = 1;
	ft_null = 1;
	std_fn = calloc;
	ft_fn = ft_calloc;
	libc_sig = probe_calloc(std_fn, (size_t)-1, (size_t)-1, &libc_null);
	ft_sig = probe_calloc(ft_fn, (size_t)-1, (size_t)-1, &ft_null);
	emit_ub_vals(id, libc_sig, ft_sig, libc_null, ft_null);
""",
                "nullness",
            )
        ],
        "ft_itoa": [
            {
                "id": "subject/ft_itoa/int-min",
                "function": "ft_itoa",
                "kind": "expression",
                "suite": "subject",
                "call": "ft_itoa(-2147483648)",
                "args": [{"type": "int", "value": "-2147483648"}],
                "expected": {"type": "str", "value": "-2147483648"},
                "part": "part 2",
            }
        ],
        "ft_substr": [
            _guard_case("ft_substr", "null-zero", "ft_substr(NULL, 0, 0)", "const char *s = 0; free(ft_substr(s, 0, 0));"),
            _guard_case("ft_substr", "null-len", "ft_substr(NULL, 0, 5)", "const char *s = 0; free(ft_substr(s, 0, 5));"),
            _guard_case("ft_substr", "null-start", "ft_substr(NULL, 3, 1)", "const char *s = 0; free(ft_substr(s, 3, 1));"),
        ],
        "ft_strjoin": [
            _guard_case("ft_strjoin", "both-null", "ft_strjoin(NULL, NULL)", "const char *a = 0; const char *b = 0; free(ft_strjoin(a, b));"),
            _guard_case("ft_strjoin", "left-null", 'ft_strjoin(NULL, "abc")', 'const char *a = 0; free(ft_strjoin(a, "abc"));'),
            _guard_case("ft_strjoin", "right-null", 'ft_strjoin("abc", NULL)', 'const char *b = 0; free(ft_strjoin("abc", b));'),
        ],
        "ft_strtrim": [
            _guard_case("ft_strtrim", "both-null", "ft_strtrim(NULL, NULL)", "const char *a = 0; const char *b = 0; free(ft_strtrim(a, b));"),
            _guard_case("ft_strtrim", "string-null", 'ft_strtrim(NULL, " .")', 'const char *a = 0; free(ft_strtrim(a, " ."));'),
            _guard_case("ft_strtrim", "set-null", 'ft_strtrim("  abc  ", NULL)', 'const char *b = 0; free(ft_strtrim("  abc  ", b));'),
        ],
        "ft_split": [
            _guard_case("ft_split", "null-space", "ft_split(NULL, ' ')", "const char *s = 0; free(ft_split(s, ' '));"),
            _guard_case("ft_split", "null-zero", "ft_split(NULL, 0)", "const char *s = 0; free(ft_split(s, '\\0'));"),
        ],
        "ft_strmapi": [
            _guard_case(
                "ft_strmapi",
                "string-null",
                "ft_strmapi(NULL, f)",
                "const char *s = 0; free(ft_strmapi(s, subject_upper));",
            ),
            _guard_case(
                "ft_strmapi",
                "function-null",
                'ft_strmapi("abc", NULL)',
                "char (*f)(unsigned int, char) = 0; free(ft_strmapi(\"abc\", f));",
            ),
        ],
        "ft_striteri": [
            _guard_case(
                "ft_striteri",
                "string-null",
                "ft_striteri(NULL, f)",
                "char *s = 0; ft_striteri(s, subject_star);",
            ),
            _guard_case(
                "ft_striteri",
                "function-null",
                'ft_striteri("abc", NULL)',
                "void (*f)(unsigned int, char *) = 0; char buf[] = \"abc\"; ft_striteri(buf, f);",
            ),
        ],
        "ft_putchar_fd": [
            _guard_case("ft_putchar_fd", "bad-fd", "ft_putchar_fd('a', -1)", "ft_putchar_fd('a', -1);"),
        ],
        "ft_putstr_fd": [
            _guard_case("ft_putstr_fd", "null", "ft_putstr_fd(NULL, 1)", "char *s = 0; ft_putstr_fd(s, 1);"),
            _guard_case("ft_putstr_fd", "bad-fd", 'ft_putstr_fd("abc", -1)', 'ft_putstr_fd("abc", -1);'),
        ],
        "ft_putendl_fd": [
            _guard_case("ft_putendl_fd", "null", "ft_putendl_fd(NULL, 1)", "char *s = 0; ft_putendl_fd(s, 1);"),
            _guard_case("ft_putendl_fd", "bad-fd", 'ft_putendl_fd("abc", -1)', 'ft_putendl_fd("abc", -1);'),
        ],
        "ft_putnbr_fd": [
            _guard_case(
                "ft_putnbr_fd",
                "bad-fd",
                "ft_putnbr_fd(INT_MIN, -1)",
                "ft_putnbr_fd((-2147483647 - 1), -1);",
            )
        ],
    }
    for function in ("ft_isalpha", "ft_isdigit", "ft_isalnum", "ft_isascii", "ft_isprint"):
        groups[function] = [_value_case(function, "eof", f"{function}(EOF)", "-1", "0")]
        if function == "ft_isascii":
            # glibc exposes isascii as a macro, not a callable, under POSIX.
            # The man page is 1 for 0..127 and 0 otherwise, and that macro does not crash.
            groups[function].extend(
                _value_case(
                    function,
                    f"extra-{number if number >= 0 else 'm' + str(-number)}",
                    f"{function}({number})",
                    str(number),
                    "0",
                )
                for number, _literal in _EXTRAS
            )
            continue
        groups[function].extend(
            _int_probe(function, number, literal, "ctype") for number, literal in _EXTRAS
        )
    for function in ("ft_toupper", "ft_tolower"):
        groups[function] = [_value_case(function, "eof", f"{function}(EOF)", "-1", "-1")]
        groups[function].extend(
            _int_probe(function, number, literal, "soft") for number, literal in _EXTRAS
        )
    return groups


def _libc(function: str, name: str, call: str, args: list[dict]) -> dict:
    return {
        "id": f"subject/{function}/{name}",
        "function": function,
        "kind": "compare_libc",
        "suite": "subject",
        "call": call,
        "args": args,
        "expected": None,
        "part": "",
    }


def _breaker_cases() -> dict[str, list[dict]]:
    """Inputs that break the usual wrong implementation. libc is the oracle."""
    return {
        "ft_strncmp": [
            _libc(
                "ft_strncmp",
                "size-max",
                'ft_strncmp("1234", "1235", (size_t)-1)',
                [
                    {"type": "str", "value": "1234"},
                    {"type": "str", "value": "1235"},
                    {"type": "int", "value": "-1"},
                ],
            )
        ],
        "ft_strrchr": [
            _libc(
                "ft_strrchr",
                "high-bit",
                'ft_strrchr("teste", \'e\' + 256)',
                [
                    {"type": "str", "value": "teste"},
                    {"type": "int", "value": str(ord("e") + 256)},
                ],
            ),
            _libc(
                "ft_strrchr",
                "nul",
                'ft_strrchr("teste", \'\\0\')',
                [
                    {"type": "str", "value": "teste"},
                    {"type": "int", "value": "0"},
                ],
            ),
        ],
        "ft_memchr": [
            _libc(
                "ft_memchr",
                "zero-count",
                'ft_memchr("bonjour", \'b\', 0)',
                [
                    {"type": "str", "value": "bonjour"},
                    {"type": "int", "value": str(ord("b"))},
                    {"type": "int", "value": "0"},
                ],
            ),
            _libc(
                "ft_memchr",
                "past-nul",
                'ft_memchr("a\\\\0b", \'b\', 3)',
                [
                    {"type": "str", "value": "a\x00b"},
                    {"type": "int", "value": str(ord("b"))},
                    {"type": "int", "value": "3"},
                ],
            ),
            _libc(
                "ft_memchr",
                "high-bit",
                'ft_memchr("ab", \'b\' + 256, 2)',
                [
                    {"type": "str", "value": "ab"},
                    {"type": "int", "value": str(ord("b") + 256)},
                    {"type": "int", "value": "2"},
                ],
            ),
            _libc(
                "ft_memchr",
                "byte-255",
                "ft_memchr(0xFF, -1, 1)",
                [
                    {"type": "str", "value": "\xff"},
                    {"type": "int", "value": "-1"},
                    {"type": "int", "value": "1"},
                ],
            ),
        ],
        "ft_strnstr": [
            _libc(
                "ft_strnstr",
                "size-max",
                'ft_strnstr("aaabc", "abc", (size_t)-1)',
                [
                    {"type": "str", "value": "aaabc"},
                    {"type": "str", "value": "abc"},
                    {"type": "int", "value": "-1"},
                ],
            )
        ],
        "ft_strlcpy": [
            _case(
                "ft_strlcpy",
                "size-max",
                'ft_strlcpy(dst, "hi", (size_t)-1) stops at the terminator',
                {"type": "pair", "value": {"n": "2", "bytes": "hi\x00xxxxx"}},
                """
	unsigned char dst[8];
	size_t n;
	char *oh = NULL;
	char *eh = NULL;
	memset(dst, 'x', sizeof dst);
	begin_cap();
	n = ft_strlcpy((char *)dst, "hi", (size_t)-1);
	end_cap(&oh, &eh);
	emit_pair(id, n, dst, sizeof dst, oh, eh);
""",
            )
        ],
        "ft_strlcat": [
            _case(
                "ft_strlcat",
                "no-terminator",
                'ft_strlcat(dst, "z", 4) with no NUL inside the size',
                {"type": "pair", "value": {"n": "5", "bytes": "aaaaaaaa"}},
                """
	unsigned char dst[8];
	size_t n;
	char *oh = NULL;
	char *eh = NULL;
	memset(dst, 'a', sizeof dst);
	begin_cap();
	n = ft_strlcat((char *)dst, "z", 4);
	end_cap(&oh, &eh);
	emit_pair(id, n, dst, sizeof dst, oh, eh);
""",
            )
        ],
    }
