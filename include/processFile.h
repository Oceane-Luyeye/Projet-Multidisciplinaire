#ifndef PROCESSFILE_H
#define PROCESSFILE_H

#include "./Move.h"

int initMatrix(MoveMatrix* moveMat, int capacity);
MoveMatrix* initMovementMatrix(int capacity);
void freeMoveMat(MoveMatrix* moveMat);
void readFile(char* filename, MoveMatrix* moveMat);
int resizeMoveMatrix(MoveMatrix* moveMat, int newCapacity);
void printMatrix(MoveMatrix* moveMat);

#endif