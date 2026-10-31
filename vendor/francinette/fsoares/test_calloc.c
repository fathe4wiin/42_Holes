
#include "my_utils.h"

int test_single_calloc(int test_number, size_t count, size_t size)
{
	set_signature_tn(test_number, "ft_calloc(%zu, %zu)", count, size);

	reset_malloc_mock();
	void *res_calloc = ft_calloc(count, size);
	void *res_std = calloc(count, size);

	int result = check_mem_size(res_calloc, count * size);
	result = same_mem(res_std, res_calloc, count * size) && result;
	result = check_leaks(res_calloc) && result;

	null_check(ft_calloc(count, size), result);
	return result;
}

static int test_calloc_zero_rule(void)
{
	void *a;
	void *b;

	set_signature_tn(10, "ft_calloc(0, 0)");
	a = ft_calloc(0, 0);
	b = ft_calloc(0, 0);
	if (a == NULL || b == NULL)
	{
		free(a);
		if (b != a)
			free(b);
		return (error("if nmemb or size is 0, calloc must return a unique pointer free() accepts\n"));
	}
	if (a == b)
	{
		free(a);
		return (error("two live ft_calloc(0, 0) calls returned the same pointer\n"));
	}
	free(a);
	free(b);
	set_signature_tn(11, "ft_calloc(0, 4)");
	a = ft_calloc(0, 4);
	if (a == NULL)
		return (error("ft_calloc(0, 4) must return a freeable pointer\n"));
	free(a);
	set_signature_tn(12, "ft_calloc(4, 0)");
	a = ft_calloc(4, 0);
	if (a == NULL)
		return (error("ft_calloc(4, 0) must return a freeable pointer\n"));
	free(a);
	return (1);
}

int test_calloc()
{
	int res = 1;

	res = test_single_calloc(1, 0, 10) && res;
	res = test_single_calloc(2, 10, 0) && res;
	res = test_single_calloc(3, 10, sizeof(long)) && res;
	res = test_calloc_zero_rule() && res;
	res = libc_crash_calloc() && res;

	return res;
}

int	main()
{
	handle_signals_with_time();
	test(calloc);
}
