#include <stdio.h>
#include <stdlib.h>
#include "../include/processFile.h"

#define SIZE 10

int main(int argc, char** argv) {
    float** matrix = initMatrix(SIZE);



    readFile("./data/preprocessing/distances/livraison10_matrix.csv", matrix);
    printMatrix(matrix, SIZE);

    


    
}