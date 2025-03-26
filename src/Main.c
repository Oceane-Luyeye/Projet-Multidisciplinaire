#include <stdio.h>
#include <stdlib.h>
#include "../include/processFile.h"


int main(int argc, char** argv) {
    float** matrix = initMatrix(10);
    readFile("./data/preprocessing/distances/livraison10_matrix.csv", matrix);
    printMatrix(matrix, 10);

    


    
}