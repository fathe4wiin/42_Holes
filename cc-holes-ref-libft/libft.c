#define _DEFAULT_SOURCE
#include "libft.h"

#include <bsd/string.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int	call_int(int (*fn)(int), int c)
{
	return (fn(c));
}

int	ft_isalpha(int c)
{
	return (call_int(isalpha, c) ? 1 : 0);
}

int	ft_isdigit(int c)
{
	return (call_int(isdigit, c) ? 1 : 0);
}

int	ft_isalnum(int c)
{
	return (call_int(isalnum, c) ? 1 : 0);
}

int	ft_isascii(int c)
{
	return (c >= 0 && c <= 127);
}

int	ft_isprint(int c)
{
	return (call_int(isprint, c) ? 1 : 0);
}

size_t	ft_strlen(const char *s)
{
	return (strlen(s));
}

void	*ft_memset(void *b, int c, size_t len)
{
	return (memset(b, c, len));
}

void	ft_bzero(void *s, size_t n)
{
	bzero(s, n);
}

void	*ft_memcpy(void *dst, const void *src, size_t n)
{
	return (memcpy(dst, src, n));
}

void	*ft_memmove(void *dst, const void *src, size_t len)
{
	return (memmove(dst, src, len));
}

size_t	ft_strlcpy(char *dst, const char *src, size_t dstsize)
{
	return (strlcpy(dst, src, dstsize));
}

size_t	ft_strlcat(char *dst, const char *src, size_t dstsize)
{
	return (strlcat(dst, src, dstsize));
}

int	ft_toupper(int c)
{
	return (call_int(toupper, c));
}

int	ft_tolower(int c)
{
	return (call_int(tolower, c));
}

char	*ft_strchr(const char *s, int c)
{
	return (strchr(s, c));
}

char	*ft_strrchr(const char *s, int c)
{
	return (strrchr(s, c));
}

int	ft_strncmp(const char *s1, const char *s2, size_t n)
{
	return (strncmp(s1, s2, n));
}

void	*ft_memchr(const void *s, int c, size_t n)
{
	return (memchr(s, c, n));
}

int	ft_memcmp(const void *s1, const void *s2, size_t n)
{
	return (memcmp(s1, s2, n));
}

char	*ft_strnstr(const char *haystack, const char *needle, size_t len)
{
	return (strnstr(haystack, needle, len));
}

int	ft_atoi(const char *str)
{
	return (atoi(str));
}

void	*ft_calloc(size_t count, size_t size)
{
	return (calloc(count, size));
}

char	*ft_strdup(const char *s1)
{
	return (strdup(s1));
}

char	*ft_substr(char const *s, unsigned int start, size_t len)
{
	size_t	have;
	size_t	take;
	char	*out;

	if (!s)
		return (NULL);
	have = strlen(s);
	if (start >= have)
		return (strdup(""));
	take = have - start;
	if (take > len)
		take = len;
	out = malloc(take + 1);
	if (!out)
		return (NULL);
	memcpy(out, s + start, take);
	out[take] = '\0';
	return (out);
}

char	*ft_strjoin(char const *s1, char const *s2)
{
	size_t	n1;
	size_t	n2;
	char	*out;

	if (!s1 || !s2)
		return (NULL);
	n1 = strlen(s1);
	n2 = strlen(s2);
	out = malloc(n1 + n2 + 1);
	if (!out)
		return (NULL);
	memcpy(out, s1, n1);
	memcpy(out + n1, s2, n2);
	out[n1 + n2] = '\0';
	return (out);
}

char	*ft_strtrim(char const *s1, char const *set)
{
	size_t	begin;
	size_t	end;

	if (!s1 || !set)
		return (NULL);
	begin = 0;
	end = strlen(s1);
	while (s1[begin] && strchr(set, s1[begin]))
		begin++;
	while (end > begin && strchr(set, s1[end - 1]))
		end--;
	return (ft_substr(s1, (unsigned int)begin, end - begin));
}

static size_t	word_count(char const *s, char c)
{
	size_t	count;
	size_t	i;

	count = 0;
	i = 0;
	while (s[i])
	{
		while (s[i] == c)
			i++;
		if (!s[i])
			break ;
		count++;
		while (s[i] && s[i] != c)
			i++;
	}
	return (count);
}

char	**ft_split(char const *s, char c)
{
	char	**out;
	size_t	count;
	size_t	i;
	size_t	word;

	if (!s)
		return (NULL);
	count = word_count(s, c);
	out = malloc((count + 1) * sizeof(char *));
	if (!out)
		return (NULL);
	i = 0;
	word = 0;
	while (s[i])
	{
		size_t	start;

		while (s[i] == c)
			i++;
		if (!s[i])
			break ;
		start = i;
		while (s[i] && s[i] != c)
			i++;
		out[word] = ft_substr(s, (unsigned int)start, i - start);
		if (!out[word])
		{
			while (word > 0)
				free(out[--word]);
			free(out);
			return (NULL);
		}
		word++;
	}
	out[word] = NULL;
	return (out);
}

static int	nbr_len(int n)
{
	int	len;

	len = (n <= 0);
	while (n)
	{
		n /= 10;
		len++;
	}
	return (len);
}

char	*ft_itoa(int n)
{
	char			*out;
	int				len;
	unsigned int	number;

	len = nbr_len(n);
	out = malloc((size_t)len + 1);
	if (!out)
		return (NULL);
	out[len] = '\0';
	if (n < 0)
		number = (unsigned int)(-(long)n);
	else
		number = (unsigned int)n;
	if (n < 0)
		out[0] = '-';
	else if (n == 0)
		out[0] = '0';
	while (number)
	{
		out[--len] = (char)('0' + number % 10);
		number /= 10;
	}
	return (out);
}

char	*ft_strmapi(char const *s, char (*f)(unsigned int, char))
{
	char			*out;
	unsigned int	i;

	if (!s || !f)
		return (NULL);
	out = malloc(strlen(s) + 1);
	if (!out)
		return (NULL);
	i = 0;
	while (s[i])
	{
		out[i] = f(i, s[i]);
		i++;
	}
	out[i] = '\0';
	return (out);
}

void	ft_striteri(char *s, void (*f)(unsigned int, char *))
{
	unsigned int	i;

	if (!s || !f)
		return ;
	i = 0;
	while (s[i])
	{
		f(i, s + i);
		i++;
	}
}

void	ft_putchar_fd(char c, int fd)
{
	write(fd, &c, 1);
}

void	ft_putstr_fd(char *s, int fd)
{
	if (!s)
		return ;
	write(fd, s, strlen(s));
}

void	ft_putendl_fd(char *s, int fd)
{
	if (!s)
		return ;
	ft_putstr_fd(s, fd);
	ft_putchar_fd('\n', fd);
}

void	ft_putnbr_fd(int n, int fd)
{
	char			buf[12];
	int				i;
	unsigned int	number;

	if (n < 0)
		number = (unsigned int)(-(long)n);
	else
		number = (unsigned int)n;
	i = 12;
	if (number == 0)
		buf[--i] = '0';
	while (number)
	{
		buf[--i] = (char)('0' + number % 10);
		number /= 10;
	}
	if (n < 0)
		buf[--i] = '-';
	write(fd, buf + i, (size_t)(12 - i));
}

t_list	*ft_lstnew(void *content)
{
	t_list	*node;

	node = malloc(sizeof(t_list));
	if (!node)
		return (NULL);
	node->content = content;
	node->next = NULL;
	return (node);
}

void	ft_lstadd_front(t_list **lst, t_list *new)
{
	if (!lst || !new)
		return ;
	new->next = *lst;
	*lst = new;
}

int	ft_lstsize(t_list *lst)
{
	int	size;

	size = 0;
	while (lst)
	{
		size++;
		lst = lst->next;
	}
	return (size);
}

t_list	*ft_lstlast(t_list *lst)
{
	if (!lst)
		return (NULL);
	while (lst->next)
		lst = lst->next;
	return (lst);
}

void	ft_lstadd_back(t_list **lst, t_list *new)
{
	t_list	*last;

	if (!lst || !new)
		return ;
	if (!*lst)
	{
		*lst = new;
		return ;
	}
	last = ft_lstlast(*lst);
	last->next = new;
}

void	ft_lstdelone(t_list *lst, void (*del)(void *))
{
	if (!lst)
		return ;
	if (del)
		del(lst->content);
	free(lst);
}

void	ft_lstclear(t_list **lst, void (*del)(void *))
{
	t_list	*node;
	t_list	*next;

	if (!lst)
		return ;
	node = *lst;
	while (node)
	{
		next = node->next;
		ft_lstdelone(node, del);
		node = next;
	}
	*lst = NULL;
}

void	ft_lstiter(t_list *lst, void (*f)(void *))
{
	if (!f)
		return ;
	while (lst)
	{
		f(lst->content);
		lst = lst->next;
	}
}

t_list	*ft_lstmap(t_list *lst, void *(*f)(void *), void (*del)(void *))
{
	t_list	*head;
	t_list	*tail;
	t_list	*node;
	void	*content;

	if (!lst || !f)
		return (NULL);
	head = NULL;
	tail = NULL;
	while (lst)
	{
		content = f(lst->content);
		node = ft_lstnew(content);
		if (!node)
		{
			if (del)
				del(content);
			ft_lstclear(&head, del);
			return (NULL);
		}
		if (!head)
			head = node;
		else
			tail->next = node;
		tail = node;
		lst = lst->next;
	}
	return (head);
}
