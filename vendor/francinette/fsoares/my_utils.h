/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   my_utils.h                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: fsoares- <fsoares-@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2022/01/14 13:40:02 by fsoares-          #+#    #+#             */
/*   Updated: 2022/02/24 18:29:31 by fsoares-         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef MY_UTILS_H
#define MY_UTILS_H

#include "utils/utils.h"
#include "libft.h"

#define UB_EXACT 0
#define UB_TRUTH 1
#define UB_CRASH_ONLY 2

extern int g_ub_warning;

#define create_test_ctype(fn) \
	int test_##fn(void) \
	{ \
		int c; \
		int res = 1; \
		for (c = 0; c <= 0xff && res; c++) \
		{ \
			int expected = fn(c) ? 1 : 0; \
			int yours = ft_##fn(c); \
			if (yours != expected) \
			{ \
				fprintf(errors_file, \
						CYN "ft_" #fn "(%i: %s)" NC ": expected %i (libc %i), yours: %i\n", \
						c, escape_chr((char)c), expected, fn(c), yours); \
				res = 0; \
			} \
		} \
		if (res) \
		{ \
			int expected = fn(EOF) ? 1 : 0; \
			int yours = ft_##fn(EOF); \
			if (yours != expected) \
			{ \
				fprintf(errors_file, \
						CYN "ft_" #fn "(EOF)" NC ": expected %i (libc %i), yours: %i\n", \
						expected, fn(EOF), yours); \
				res = 0; \
			} \
		} \
		if (res) \
			res = match_fn_int_extra(#fn, fn, ft_##fn, UB_CRASH_ONLY) && res; \
		return res; \
	}

#define create_test_val(fn) \
	int test_##fn(void) \
	{ \
		int c; \
		int res = 1; \
		for (c = 0; c <= 0xff && res; c++) \
		{ \
			if (fn(c) != ft_##fn(c)) \
			{ \
				fprintf(errors_file, \
						CYN "ft_" #fn "(%i: %s)" NC ": std: %i, yours: %i\n", \
						c, escape_chr((char)c), fn(c), ft_##fn(c)); \
				res = 0; \
			} \
		} \
		if (res && fn(EOF) != ft_##fn(EOF)) \
		{ \
			fprintf(errors_file, CYN "ft_" #fn "(EOF)" NC ": std: %i, yours: %i\n", \
					fn(EOF), ft_##fn(EOF)); \
			res = 0; \
		} \
		if (res) \
			res = match_fn_int_extra(#fn, fn, ft_##fn, UB_CRASH_ONLY) && res; \
		return res; \
	}

#define test(fn) \
	strcpy(function, #fn); \
	g_ub_warning = 0; \
	errors_file = fopen("errors_" #fn ".log", "w"); \
	if (!test_##fn()) \
		printf("ft_%-13s: " RED "KO" NC "\n", #fn); \
	else if (g_ub_warning) \
		printf("ft_%-13s: " YEL "WARN" NC "\n", #fn); \
	else \
		printf("ft_%-13s: " GRN "OK" NC "\n", #fn); \
	fclose(errors_file);

#define no_test(fn) \
	printf("ft_%-13s: " YEL "No test yet\n" NC, #fn)

/**
 * @brief given a function call that returns an allocated string and the
 * expected return value, this macro will check that the string returned
 * was the one expected as well as that there are no leaks and that it
 * correctly handles allocation errors
 */
#define check_alloc_str_return(fn_call, exp)                 \
	int result = 1;                                          \
	char *res = fn_call;                                     \
	result = same_string(exp, res);                          \
	result = check_mem_size(res, strlen(exp) + 1) && result; \
	result = check_leaks(res) && result;                     \
	null_check(fn_call, result);                             \
	return result;

void handle_signals_with_time();
int set_signature_tn(int test_number, const char *format, ...);

int compare_crash(const char *label, void (*std_fn)(void), void (*ft_fn)(void));
int expect_no_crash(const char *label, void (*fn)(void));
int match_fn_int_extra(const char *name, int (*std_fn)(int), int (*ft_fn)(int), int mode);

int libc_crash_strlen(void);
int libc_crash_memset(void);
int libc_crash_bzero(void);
int libc_crash_memcpy(void);
int libc_crash_memmove(void);
int libc_crash_strlcpy(void);
int libc_crash_strlcat(void);
int libc_crash_strchr(void);
int libc_crash_strrchr(void);
int libc_crash_strncmp(void);
int libc_crash_memchr(void);
int libc_crash_memcmp(void);
int libc_crash_strnstr(void);
int libc_crash_atoi(void);
int libc_crash_strdup(void);
int libc_crash_calloc(void);

int part2_guard_substr(void);
int part2_guard_strjoin(void);
int part2_guard_strtrim(void);
int part2_guard_split(void);
int part2_guard_strmapi(void);
int part2_guard_striteri(void);
int part2_guard_putstr_fd(void);
int part2_guard_putendl_fd(void);
int part2_guard_putchar_fd(void);
int part2_guard_putnbr_fd(void);


#endif
