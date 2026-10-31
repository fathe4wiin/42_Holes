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
    return groups
