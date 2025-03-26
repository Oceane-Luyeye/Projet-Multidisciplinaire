EXEC= voyageur       

CC= gcc
CFLAGS= -Wall -std=c17

INCLUDE_DIR= include
BIN_DIR= bin
SRC_DIR= src


SRC_FILES= $(wildcard $(SRC_DIR)/*.c)                
OBJ_FILES= $(SRC_FILES:$(SRC_DIR)/%.c=$(BIN_DIR)/%.o) 

all: $(EXEC)

$(EXEC): $(OBJ_FILES)
	$(CC) -o $@ $^
 
$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(BIN_DIR)/%.o: $(SRC_DIR)/%.c  | $(BIN_DIR)
	$(CC) -c -o $@ $< $(CFLAGS)


.PHONY: clean
clean:
	rm -f $(BIN_DIR)/*.o $(EXEC)
	rm -rf $(BIN_DIR)