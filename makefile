CC      = gcc
CFLAGS  = -std=c11 -O2 -Wall
LDFLAGS = -lm

TARGETS = genetic

all: $(TARGETS)

genetic: genetic.o
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o $(TARGETS)