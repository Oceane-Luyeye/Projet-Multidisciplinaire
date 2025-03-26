#ifndef PROCESSFILE_H
#define PROCESSFILE_H

void readFile(char* file, float** matrix);
void printMatrix(float** matrix, int size);
float** initMatrix(int size);

#endif