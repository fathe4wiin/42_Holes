NAME = libft.a
CC = gcc
CFLAGS = -Wall -Wextra -Werror

all: $(NAME)

$(NAME): libft.o
	ar rcs $(NAME) libft.o

libft.o: libft.c libft.h
	$(CC) $(CFLAGS) -c libft.c -o libft.o

clean:
	rm -f libft.o

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re
