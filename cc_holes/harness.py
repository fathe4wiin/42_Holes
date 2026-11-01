"""Compile a small C driver that calls one libft function and prints results."""

import os
import signal
import subprocess
from pathlib import Path

from cc_holes.model import Bound, Obs, parse_result_line

_RUNTIME = r"""
#define _POSIX_C_SOURCE 200809L
#include "libft.h"
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static char *to_hex(const unsigned char *bytes, size_t count)
{
	static const char hex[] = "0123456789abcdef";
	char *out;
	size_t i;

	out = malloc(count * 2 + 1);
	if (!out)
		return NULL;
	for (i = 0; i < count; i++)
	{
		out[i * 2] = hex[bytes[i] >> 4];
		out[i * 2 + 1] = hex[bytes[i] & 15];
	}
	out[count * 2] = '\0';
	return out;
}

static char *read_hex(int fd)
{
	unsigned char chunk[4096];
	unsigned char *data;
	size_t len;
	ssize_t got;
	char *hex;

	data = NULL;
	len = 0;
	while ((got = read(fd, chunk, sizeof chunk)) > 0)
	{
		unsigned char *grown;

		if (len + (size_t)got > 4000000)
			break;
		grown = realloc(data, len + (size_t)got);
		if (!grown)
			break;
		data = grown;
		memcpy(data + len, chunk, (size_t)got);
		len += (size_t)got;
	}
	hex = to_hex(data, len);
	free(data);
	return hex;
}

static int saved_out = -1;
static int saved_err = -1;
static int cap_out = -1;
static int cap_err = -1;

static void begin_cap(void)
{
	int out_pipe[2];
	int err_pipe[2];

	fflush(stdout);
	fflush(stderr);
	saved_out = dup(STDOUT_FILENO);
	saved_err = dup(STDERR_FILENO);
	if (pipe(out_pipe) < 0 || pipe(err_pipe) < 0)
		_exit(1);
	dup2(out_pipe[1], STDOUT_FILENO);
	dup2(err_pipe[1], STDERR_FILENO);
	close(out_pipe[1]);
	close(err_pipe[1]);
	cap_out = out_pipe[0];
	cap_err = err_pipe[0];
}

static void end_cap(char **out_hex, char **err_hex)
{
	fflush(stdout);
	fflush(stderr);
	dup2(saved_out, STDOUT_FILENO);
	dup2(saved_err, STDERR_FILENO);
	close(saved_out);
	close(saved_err);
	saved_out = -1;
	saved_err = -1;
	*out_hex = read_hex(cap_out);
	*err_hex = read_hex(cap_err);
	close(cap_out);
	close(cap_err);
	cap_out = -1;
	cap_err = -1;
	if (!*out_hex)
		*out_hex = to_hex(NULL, 0);
	if (!*err_hex)
		*err_hex = to_hex(NULL, 0);
}

static size_t bounded_len(const char *text)
{
	size_t i;

	if (!text)
		return 0;
	i = 0;
	while (i < 1000000 && text[i])
		i++;
	return i;
}

static void emit_int(const char *id, long long value, char *out_hex, char *err_hex)
{
	printf("%s\tok\tint\t%lld\t%s\t%s\n", id, value,
		out_hex ? out_hex : "", err_hex ? err_hex : "");
	free(out_hex);
	free(err_hex);
	fflush(stdout);
}

static void emit_size(const char *id, size_t value, char *out_hex, char *err_hex)
{
	printf("%s\tok\tsize\t%zu\t%s\t%s\n", id, value,
		out_hex ? out_hex : "", err_hex ? err_hex : "");
	free(out_hex);
	free(err_hex);
	fflush(stdout);
}

static void emit_void(const char *id, char *out_hex, char *err_hex)
{
	printf("%s\tok\tvoid\t\t%s\t%s\n", id,
		out_hex ? out_hex : "", err_hex ? err_hex : "");
	free(out_hex);
	free(err_hex);
	fflush(stdout);
}

static void emit_pf(const char *id, int got, int want, char *out_hex, char *libc_hex)
{
	printf("%s\tok\tpf\t%d:%d\t%s\t%s\n", id, got, want,
		out_hex ? out_hex : "", libc_hex ? libc_hex : "");
	free(out_hex);
	free(libc_hex);
	fflush(stdout);
}

static void emit_raw(const char *id, const unsigned char *bytes, size_t len,
	char *out_hex, char *err_hex)
{
	char *hex;

	hex = to_hex(bytes, len);
	printf("%s\tok\tbytes\t%s\t%s\t%s\n", id, hex ? hex : "",
		out_hex ? out_hex : "", err_hex ? err_hex : "");
	free(hex);
	free(out_hex);
	free(err_hex);
	fflush(stdout);
}

static void emit_pair(const char *id, size_t n, const unsigned char *bytes, size_t len,
	char *out_hex, char *err_hex)
{
	char *hex;

	hex = to_hex(bytes, len);
	printf("%s\tok\tpair\t%zu:%s\t%s\t%s\n", id, n, hex ? hex : "",
		out_hex ? out_hex : "", err_hex ? err_hex : "");
	free(hex);
	free(out_hex);
	free(err_hex);
	fflush(stdout);
}

static int subject_frees __attribute__((unused));

static char subject_upper(unsigned int index, char c)
{
	(void)index;
	if (c >= 'a' && c <= 'z')
		return (char)(c - 32);
	return c;
}

static void subject_star(unsigned int index, char *c)
{
	if (index % 2 == 0 && *c >= 'a' && *c <= 'z')
		*c = (char)(*c - 32);
}

static void subject_free(void *pointer)
{
	subject_frees++;
	free(pointer);
}

static void *subject_dup(void *pointer)
{
	const char *text;
	char *copy;
	size_t len;

	text = pointer;
	len = strlen(text);
	copy = malloc(len + 1);
	if (copy)
		memcpy(copy, text, len + 1);
	return copy;
}

static void subject_add(void *pointer)
{
	int *number;

	number = pointer;
	*number = *number + 1;
}

static char subject_add_map(unsigned int index, char c)
{
	return (char)(index + (unsigned char)c);
}

static void subject_add_iter(unsigned int index, char *c)
{
	*c = (char)(index + (unsigned char)*c);
}

static char subject_zero_map(unsigned int index, char c)
{
	(void)index;
	(void)c;
	return ('0');
}

static void subject_zero_iter(unsigned int index, char *c)
{
	(void)index;
	*c = '0';
}

static char subject_swap_map(unsigned int index, char c)
{
	(void)index;
	if (c >= 'a' && c <= 'z')
		return (char)(c - 32);
	if (c >= 'A' && c <= 'Z')
		return (char)(c + 32);
	return (c);
}

static void subject_swap_iter(unsigned int index, char *c)
{
	(void)index;
	if (*c >= 'a' && *c <= 'z')
		*c = (char)(*c - 32);
	else if (*c >= 'A' && *c <= 'Z')
		*c = (char)(*c + 32);
}

static void emit_text(const char *id, const char *text, int do_free, char *out_hex, char *err_hex)
{
	size_t len;
	char *hex;

	if (!text)
	{
		printf("%s\tok\tnull\t\t%s\t%s\n", id,
			out_hex ? out_hex : "", err_hex ? err_hex : "");
		free(out_hex);
		free(err_hex);
		fflush(stdout);
		return;
	}
	len = bounded_len(text);
	if (len == 1000000 && text[len])
	{
		printf("%s\tok\tbad\tunterminated\t%s\t%s\n", id,
			out_hex ? out_hex : "", err_hex ? err_hex : "");
		free(out_hex);
		free(err_hex);
		fflush(stdout);
		return;
	}
	hex = to_hex((const unsigned char *)text, len);
	printf("%s\tok\tbytes\t%s\t%s\t%s\n", id, hex ? hex : "",
		out_hex ? out_hex : "", err_hex ? err_hex : "");
	free(hex);
	if (do_free)
		free((void *)text);
	free(out_hex);
	free(err_hex);
	fflush(stdout);
}

static void emit_lines(const char *id, char **tab, char *out_hex, char *err_hex)
{
	size_t count;
	size_t i;
	size_t bytes;
	char *payload;
	size_t used;

	if (!tab)
	{
		printf("%s\tok\tnull\t\t%s\t%s\n", id,
			out_hex ? out_hex : "", err_hex ? err_hex : "");
		free(out_hex);
		free(err_hex);
		fflush(stdout);
		return;
	}
	count = 0;
	while (tab[count] && count < 100000)
		count++;
	bytes = 0;
	for (i = 0; i < count; i++)
		bytes += bounded_len(tab[i]) * 2 + 1;
	payload = malloc(bytes + 32);
	if (!payload)
		_exit(1);
	used = 0;
	used += (size_t)sprintf(payload + used, "%zu:", count);
	for (i = 0; i < count; i++)
	{
		size_t len;
		char *hex;

		len = bounded_len(tab[i]);
		hex = to_hex((const unsigned char *)tab[i], len);
		if (i && used + 1 < bytes + 32)
			payload[used++] = ',';
		if (hex)
		{
			size_t hlen;

			hlen = strlen(hex);
			memcpy(payload + used, hex, hlen);
			used += hlen;
			free(hex);
		}
	}
	payload[used] = '\0';
	printf("%s\tok\tlines\t%s\t%s\t%s\n", id, payload,
		out_hex ? out_hex : "", err_hex ? err_hex : "");
	free(payload);
	for (i = 0; i < count; i++)
		free(tab[i]);
	free(tab);
	free(out_hex);
	free(err_hex);
	fflush(stdout);
}

static void emit_alloc(const char *id, void *ptr, size_t count, size_t size,
	char *out_hex, char *err_hex)
{
	size_t bytes;
	char *hex;

	if (count && size > (size_t)-1 / count)
	{
		if (!ptr)
			printf("%s\tok\tnull\t\t%s\t%s\n", id,
				out_hex ? out_hex : "", err_hex ? err_hex : "");
		else
		{
			printf("%s\tok\tbad\toverflow\t%s\t%s\n", id,
				out_hex ? out_hex : "", err_hex ? err_hex : "");
			free(ptr);
		}
		free(out_hex);
		free(err_hex);
		fflush(stdout);
		return;
	}
	if (!ptr)
	{
		printf("%s\tok\tnull\t\t%s\t%s\n", id,
			out_hex ? out_hex : "", err_hex ? err_hex : "");
		free(out_hex);
		free(err_hex);
		fflush(stdout);
		return;
	}
	bytes = count * size;
	hex = to_hex((const unsigned char *)ptr, bytes);
	printf("%s\tok\tmem\t%s\t%s\t%s\n", id, hex ? hex : "",
		out_hex ? out_hex : "", err_hex ? err_hex : "");
	free(hex);
	free(ptr);
	free(out_hex);
	free(err_hex);
	fflush(stdout);
}

__attribute__((unused)) static void silence_child(void)
{
	int fd;

	alarm(0);
	signal(SIGSEGV, SIG_DFL);
	signal(SIGABRT, SIG_DFL);
	signal(SIGBUS, SIG_DFL);
	signal(SIGILL, SIG_DFL);
	signal(SIGFPE, SIG_DFL);
	signal(SIGALRM, SIG_DFL);
	signal(SIGPIPE, SIG_DFL);
	fd = open("/dev/null", O_WRONLY);
	if (fd >= 0)
	{
		dup2(fd, STDOUT_FILENO);
		dup2(fd, STDERR_FILENO);
		if (fd > STDERR_FILENO)
			close(fd);
	}
	alarm(1);
}

#define RUN_PROBE(out, body) \
	do { \
		pid_t _pid; \
		int _st; \
		_pid = fork(); \
		if (_pid < 0) \
			(out) = -1; \
		else if (_pid == 0) \
		{ \
			silence_child(); \
			body; \
			_exit(0); \
		} \
		else if (waitpid(_pid, &_st, 0) < 0) \
			(out) = -1; \
		else if (WIFSIGNALED(_st)) \
			(out) = WTERMSIG(_st); \
		else if (WIFEXITED(_st) && WEXITSTATUS(_st) == 0) \
			(out) = 0; \
		else \
			(out) = -1; \
	} while (0)

__attribute__((unused)) static void emit_ub(const char *id, int libc_sig, int ft_sig)
{
	printf("%s\tok\tub\t%d,%d\t\t\n", id, libc_sig, ft_sig);
	fflush(stdout);
}

__attribute__((unused)) static void emit_ub_vals(const char *id, int libc_sig, int ft_sig,
	int libc_val, int ft_val)
{
	printf("%s\tok\tub\t%d,%d,%d,%d\t\t\n", id, libc_sig, ft_sig, libc_val, ft_val);
	fflush(stdout);
}

__attribute__((unused)) static void emit_guard(const char *id, int sig)
{
	printf("%s\tok\tguard\t%d\t\t\n", id, sig);
	fflush(stdout);
}

__attribute__((unused)) static int probe_int(int (*fn)(int), int arg, int *value)
{
	int fds[2];
	pid_t pid;
	int status;
	int got;

	*value = 0;
	if (pipe(fds) < 0)
		return (-1);
	pid = fork();
	if (pid < 0)
	{
		close(fds[0]);
		close(fds[1]);
		return (-1);
	}
	if (pid == 0)
	{
		close(fds[0]);
		silence_child();
		got = fn(arg);
		if (write(fds[1], &got, sizeof(got)) != (ssize_t)sizeof(got))
			_exit(2);
		_exit(0);
	}
	close(fds[1]);
	if (waitpid(pid, &status, 0) < 0)
	{
		close(fds[0]);
		return (-1);
	}
	if (WIFSIGNALED(status))
	{
		close(fds[0]);
		return (WTERMSIG(status));
	}
	if (read(fds[0], value, sizeof(*value)) != (ssize_t)sizeof(*value))
	{
		close(fds[0]);
		return (-1);
	}
	close(fds[0]);
	if (WIFEXITED(status) && WEXITSTATUS(status) == 0)
		return (0);
	return (-1);
}

__attribute__((unused)) static int probe_calloc(void *(*fn)(size_t, size_t),
	size_t count, size_t size, int *is_null)
{
	int fds[2];
	pid_t pid;
	int status;
	unsigned char flag;

	*is_null = 1;
	if (pipe(fds) < 0)
		return (-1);
	pid = fork();
	if (pid < 0)
	{
		close(fds[0]);
		close(fds[1]);
		return (-1);
	}
	if (pid == 0)
	{
		void *pointer;

		close(fds[0]);
		silence_child();
		pointer = fn(count, size);
		flag = (pointer == 0);
		if (write(fds[1], &flag, 1) != 1)
			_exit(2);
		_exit(0);
	}
	close(fds[1]);
	if (waitpid(pid, &status, 0) < 0)
	{
		close(fds[0]);
		return (-1);
	}
	if (WIFSIGNALED(status))
	{
		close(fds[0]);
		return (WTERMSIG(status));
	}
	if (read(fds[0], &flag, 1) != 1)
	{
		close(fds[0]);
		return (-1);
	}
	close(fds[0]);
	*is_null = flag;
	if (WIFEXITED(status) && WEXITSTATUS(status) == 0)
		return (0);
	return (-1);
}

static int finish_child(int fd, pid_t pid, const char *id)
{
	char buf[1 << 20];
	size_t len;
	int spins;
	int reaped;
	int status;
	char *nl;

	len = 0;
	spins = 0;
	reaped = 0;
	status = 0;
	while (spins < 50)
	{
		struct pollfd pfd;
		ssize_t got;
		pid_t waited;
		int ready;

		pfd.fd = fd;
		pfd.events = POLLIN;
		ready = poll(&pfd, 1, 100);
		spins++;
		got = -1;
		if (ready > 0 && len + 1 < sizeof buf)
		{
			got = read(fd, buf + len, sizeof buf - 1 - len);
			if (got > 0)
				len += (size_t)got;
		}
		buf[len] = '\0';
		nl = memchr(buf, '\n', len);
		waited = waitpid(pid, &status, WNOHANG);
		if (waited == pid)
			reaped = 1;
		if (nl || reaped || got == 0)
			break;
	}
	nl = memchr(buf, '\n', len);
	if (nl)
	{
		fwrite(buf, 1, (size_t)(nl - buf) + 1, stdout);
		fflush(stdout);
		if (!reaped)
			waitpid(pid, &status, 0);
		return 0;
	}
	if (!reaped)
	{
		kill(pid, SIGKILL);
		waitpid(pid, &status, 0);
		printf("%s\tcrash\tsig\t14\t\t\n", id);
		fflush(stdout);
		return 0;
	}
	if (WIFSIGNALED(status))
		printf("%s\tcrash\tsig\t%d\t\t\n", id, WTERMSIG(status));
	else
		printf("%s\tcrash\tsig\t0\t\t\n", id);
	fflush(stdout);
	return 0;
}
"""

_MAIN = r"""
int main(void)
{
	int i;

	setvbuf(stdout, NULL, _IONBF, 0);
	for (i = 0; i < N; i++)
	{
		int fds[2];
		pid_t pid;

		if (pipe(fds) < 0)
			return 1;
		pid = fork();
		if (pid < 0)
			return 1;
		if (pid == 0)
		{
			close(fds[0]);
			if (dup2(fds[1], STDOUT_FILENO) < 0)
				_exit(1);
			close(fds[1]);
			setvbuf(stdout, NULL, _IONBF, 0);
			setvbuf(stderr, NULL, _IONBF, 0);
			alarm(3);
			fns[i]();
			_exit(0);
		}
		close(fds[1]);
		finish_child(fds[0], pid, ids[i]);
		close(fds[0]);
	}
	printf("%s\t%s\t%s\t%s\t%s\t%s\n", "DONE", "0", "ok", "", "", "");
	return 0;
}
"""


def _c_string(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _byte_list(buf: bytes) -> str:
    return ",".join(str(byte) for byte in buf)


def _arg_expr(index: int, arg) -> str:
    if arg.buf is not None:
        if arg.role == "mem":
            return f"(void *)b{index}"
        return f"(char *)b{index}"
    if arg.is_null:
        if arg.role == "mem":
            return "(void *)0"
        return "(char *)0"
    if arg.role == "int":
        if arg.num == -2147483648:
            return "(-2147483647 - 1)"
        return str(arg.num)
    if arg.role == "uint":
        if arg.num < 0:
            return f"(unsigned int)({arg.num})"
        return f"{arg.num}u"
    if arg.role == "size":
        if arg.num < 0:
            return f"(size_t)({arg.num})"
        return f"{arg.num}UL"
    if arg.role == "char":
        return f"(char){arg.num & 0xFF}"
    if arg.role == "fd":
        return str(arg.num)
    raise RuntimeError(f"unhandled argument {arg.role}")


def _render_loop(index: int, bound: Bound) -> str:
    ident = _c_string(bound.case["id"])
    start, end, inclusive = bound.loop or (0, 0, True)
    stop = "<=" if inclusive else "<"
    name = bound.spec.name
    lines = [
        f"static void t_{index}(void)",
        "{",
        "\tchar *oh = NULL;",
        "\tchar *eh = NULL;",
        "\tbegin_cap();",
    ]
    if bound.loop_mode == "digit":
        lines.extend(
            [
                f"\tfor (int i = {start}; i {stop} {end}; i++)",
                "\t{",
                f"\t\tint v = {name}(i);",
                "\t\tunsigned char ch;",
                "\t\tif (v != 0 && v != 1)",
                "\t\t{",
                "\t\t\tend_cap(&oh, &eh);",
                "\t\t\tprintf(\"%s\\tok\\tbad\\treturn %d, subject wants 0 or 1\\t%s\\t%s\\n\",",
                f"\t\t\t\t{ident}, v, oh ? oh : \"\", eh ? eh : \"\");",
                "\t\t\tfree(oh);",
                "\t\t\tfree(eh);",
                "\t\t\tfflush(stdout);",
                "\t\t\treturn;",
                "\t\t}",
                "\t\tch = (unsigned char)(v ? '1' : '0');",
                "\t\twrite(1, &ch, 1);",
                "\t}",
            ]
        )
    elif bound.loop_mode == "byte":
        lines.extend(
            [
                f"\tfor (int i = {start}; i {stop} {end}; i++)",
                "\t{",
                "\t\tunsigned char ch;",
                f"\t\tch = (unsigned char){name}(i);",
                "\t\twrite(1, &ch, 1);",
                "\t}",
            ]
        )
    else:
        fd = int(bound.loop_mode.split(":", 1)[1])
        lines.extend(
            [
                f"\tfor (int i = {start}; i {stop} {end}; i++)",
                f"\t\t{name}((char)i, {fd});",
            ]
        )
    lines.extend(
        [
            "\tend_cap(&oh, &eh);",
            f"\temit_void({ident}, oh, eh);",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def _render_snippet(index: int, bound: Bound) -> str:
    ident = _c_string(bound.case["id"])
    body = bound.snippet.rstrip()
    return f"static void t_{index}(void)\n{{\n\tconst char *id = {ident};\n{body}\n}}\n"


def _printf_expr(index: int, arg) -> str:
    if arg.role == "int":
        if arg.num == -2147483648:
            return "(-2147483647 - 1)"
        return str(arg.num)
    if arg.role == "uint":
        if arg.num == -2147483648:
            return "(unsigned int)(int)(-2147483647 - 1)"
        if arg.num < 0:
            return f"(unsigned int)(int)({arg.num})"
        return f"{arg.num}u"
    if arg.role == "cstr":
        return f"(char *)b{index}"
    if arg.role == "snull":
        return "(char *)0"
    if arg.role == "pnull":
        return "(void *)0"
    if arg.role == "ptr":
        if arg.num == -2147483648:
            return "(void *)(intptr_t)(-2147483647 - 1)"
        if arg.num < 0:
            return f"(void *)(intptr_t)({arg.num})"
        if arg.num > 4294967295:
            return f"(void *)(uintptr_t){arg.num}ull"
        return f"(void *)(uintptr_t){arg.num}u"
    if arg.role == "local":
        return "(void *)&hole_local"
    raise RuntimeError(f"unhandled printf argument {arg.role}")


def _render_printf(index: int, bound: Bound) -> str:
    ident = _c_string(bound.case["id"])
    lines = [f"static void t_{index}(void)", "{"]
    exprs: list[str] = []
    local = False
    for arg_index, arg in enumerate(bound.args):
        if arg.role == "fmt":
            lines.append(
                f"\tstatic const unsigned char fmt[] = {{{_byte_list(arg.buf or b'\x00')}}};"
            )
            continue
        if arg.buf is not None:
            lines.append(
                f"\tstatic const unsigned char b{arg_index}[] = {{{_byte_list(arg.buf)}}};"
            )
        if arg.role == "local":
            local = True
        exprs.append(_printf_expr(arg_index, arg))
    if local:
        lines.append("\tint hole_local;")
        lines.append("\thole_local = 42;")
    joined = ", ".join(exprs)
    extra = f", {joined}" if joined else ""
    lines.extend(
        [
            "\tchar *oh = NULL;",
            "\tchar *eh = NULL;",
            "\tchar *lh = NULL;",
            "\tchar *le = NULL;",
            "\tint got;",
            "\tint want;",
            "\tbegin_cap();",
            f"\tgot = ft_printf((const char *)fmt{extra});",
            "\tend_cap(&oh, &eh);",
            "\tbegin_cap();",
            f"\twant = printf((const char *)fmt{extra});",
            "\tend_cap(&lh, &le);",
            '\tif (strcmp(eh ? eh : "", le ? le : "") != 0)',
            "\t{",
            '\t\tprintf("%s\\tok\\tbad\\tstderr differs\\t%s\\t%s\\n",',
            f'\t\t\t{ident}, eh ? eh : "", le ? le : "");',
            "\t\tfree(oh);",
            "\t\tfree(eh);",
            "\t\tfree(lh);",
            "\t\tfree(le);",
            "\t\tfflush(stdout);",
            "\t\treturn;",
            "\t}",
            f"\temit_pf({ident}, got, want, oh, lh);",
            "\tfree(eh);",
            "\tfree(le);",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def _render_case(index: int, bound: Bound) -> str:
    if bound.snippet:
        return _render_snippet(index, bound)
    if bound.loop is not None:
        return _render_loop(index, bound)
    if bound.spec.observe == "printf":
        return _render_printf(index, bound)
    ident = _c_string(bound.case["id"])
    lines = [f"static void t_{index}(void)", "{"]
    exprs: list[str] = []
    for arg_index, arg in enumerate(bound.args):
        if arg.buf is not None:
            lines.append(
                f"\tstatic const unsigned char b{arg_index}[] = {{{_byte_list(arg.buf)}}};"
            )
        exprs.append(_arg_expr(arg_index, arg))
    call = ", ".join(exprs)
    name = bound.spec.name
    lines.append("\tchar *oh = NULL;")
    lines.append("\tchar *eh = NULL;")
    lines.append("\tbegin_cap();")
    observe = bound.spec.observe
    if observe == "void":
        lines.append(f"\t{name}({call});")
        lines.append("\tend_cap(&oh, &eh);")
        lines.append(f"\temit_void({ident}, oh, eh);")
    elif observe == "int":
        lines.append(f"\tlong long value = {name}({call});")
        lines.append("\tend_cap(&oh, &eh);")
        lines.append(f"\temit_int({ident}, value, oh, eh);")
    elif observe == "size":
        lines.append(f"\tsize_t value = {name}({call});")
        lines.append("\tend_cap(&oh, &eh);")
        lines.append(f"\temit_size({ident}, value, oh, eh);")
    elif observe == "suffix":
        cast = "(char *)" if name == "ft_memchr" else ""
        lines.append(f"\tchar *value = {cast}{name}({call});")
        lines.append("\tend_cap(&oh, &eh);")
        lines.append(f"\temit_text({ident}, value, 0, oh, eh);")
    elif observe == "str":
        lines.append(f"\tchar *value = {name}({call});")
        lines.append("\tend_cap(&oh, &eh);")
        lines.append(f"\temit_text({ident}, value, 1, oh, eh);")
    elif observe == "lines":
        lines.append(f"\tchar **value = {name}({call});")
        lines.append("\tend_cap(&oh, &eh);")
        lines.append(f"\temit_lines({ident}, value, oh, eh);")
    elif observe == "alloc":
        count = bound.args[0].num
        size = bound.args[1].num
        count_text = f"{count}UL" if count >= 0 else f"(size_t)({count})"
        size_text = f"{size}UL" if size >= 0 else f"(size_t)({size})"
        lines.append(f"\tvoid *value = {name}({call});")
        lines.append("\tend_cap(&oh, &eh);")
        lines.append(f"\temit_alloc({ident}, value, {count_text}, {size_text}, oh, eh);")
    else:
        raise RuntimeError(f"unhandled observe {observe}")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def render_driver(bounds: list[Bound], header: str = "libft.h") -> str:
    bodies = [_render_case(index, bound) for index, bound in enumerate(bounds)]
    names = ", ".join(f"t_{index}" for index in range(len(bounds))) or "0"
    ids = ", ".join(_c_string(bound.case["id"]) for bound in bounds)
    table = (
        f"static void (*const fns[])(void) = {{{names}}};\n"
        f"static const char *const ids[] = {{{ids}}};\n"
        f"#define N {len(bounds)}\n"
    )
    if not bounds:
        table = (
            "static void (*const fns[])(void) = {0};\n"
            'static const char *const ids[] = {""};\n'
            "#define N 0\n"
        )
    include = f'#include "{header}"'
    if header == "ft_printf.h":
        include += "\n#undef printf"
    runtime = _RUNTIME.replace('#include "libft.h"', include)
    return runtime + "\n" + "\n".join(bodies) + "\n" + table + "\n" + _MAIN


def compile_driver(
    source: Path,
    binary: Path,
    include: Path,
    archive: Path,
    includes: list[Path] | None = None,
    archives: list[Path] | None = None,
) -> tuple[bool, str]:
    incs: list[Path] = []
    for path in [include, *(includes or [])]:
        if path not in incs:
            incs.append(path)
    libs: list[Path] = []
    for path in [archive, *(archives or [])]:
        if path.is_file() and path not in libs:
            libs.append(path)
    command = [
        "gcc",
        "-Wall",
        "-Wextra",
        "-Wno-unused-function",
        *[f"-I{path}" for path in incs],
        str(source),
        *[str(path) for path in libs],
        "-o",
        str(binary),
        "-Wl,--allow-multiple-definition",
    ]
    first = subprocess.run(command, capture_output=True, text=True)
    if first.returncode == 0:
        return True, ""
    second = subprocess.run(command + ["-lbsd"], capture_output=True, text=True)
    if second.returncode == 0:
        return True, ""
    log = (second.stderr or first.stderr or first.stdout or "").strip()
    lines = [line for line in log.splitlines() if "error:" in line]
    summary = lines[0] if lines else (log.splitlines()[-1] if log else "compile failed")
    return False, summary


def run_driver(binary: Path, bounds: list[Bound], timeout: float) -> dict[str, Obs]:
    proc = subprocess.Popen(
        [str(binary)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, _stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, _stderr = proc.communicate()
        stdout = stdout or ""
    found: dict[str, Obs] = {}
    for line in stdout.splitlines():
        parsed = parse_result_line(line)
        if parsed is None:
            continue
        ident, obs = parsed
        found[ident] = obs
    for bound in bounds:
        ident = bound.case["id"]
        if ident not in found:
            found[ident] = Obs("crash", intval=0)
    return found
