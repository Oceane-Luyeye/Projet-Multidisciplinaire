CC      = gcc
CFLAGS  = -std=c11 -O2 -Wall
LDFLAGS = -lm

SRCS    = genetic.c
OBJS    = $(SRCS:.c=.o)
TARGET  = genetic

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)
