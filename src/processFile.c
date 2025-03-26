#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "../include/processFile.h"

#define SIZE_MAT 10


float** initMatrix(int size) {
    float** matrix = (float**)malloc((size+1) * sizeof(float*));
    if(matrix == NULL) {
        fprintf(stderr, "error initMatrix : allocate matrix\n");
    }


    for (int i = 0; i < (size+1); ++i){
        matrix[i] = (float*)malloc((size+1) * sizeof(float));
        if(matrix[i] == NULL) {
            fprintf(stderr, "error initMatrix : alocate matrix[i]\n");
        }
    }

    for(int i = 0; i < (size+1); i++) {
        for(int j = 0; j < (size+1); j++) {
            matrix[i][j] = 0;
        }
    }

    return matrix;
}

void printMatrix(float** matrix, int size) {
    if(matrix == NULL) {
        return;
    }

    for(int i = 1; i < (size+1); i++) {
        printf("%d\t", i);
    }
    printf("\n");

    for(int i = 1; i < (size+1); i++) {
        printf("%d ", i);
        for(int j = 1; j < (size+1); j++) {
            printf("%f ", matrix[i][j]);
        }
        printf("\n");
    }
}


void readFile(char* file, float** matrix) {
    if(matrix == NULL) {
        fprintf(stderr, "error readFile : matrix is null\n");
    }

    FILE* f = fopen(file, "r");

    if(f == NULL) {
        fprintf(stderr, "error readFile : opening file\n");
        return;
    }

    int d, a;
    float dist;
    char buffer[1024];

    while(fgets(buffer, 1024, f) != NULL) {
        char* value;
        
        value = strtok(buffer, ",");
        d = atoi(value);

        value = strtok(NULL, ",");
        a = atoi(value);

        value = strtok(NULL, ",");
        dist = atof(value);

        if(d != 0 && a != 0) {
            matrix[d][a] = dist;
        }
    }

   fclose(f);
}

