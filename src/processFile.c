#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "../include/processFile.h"

MoveMatrix* initMovementMatrix(int capacity) {
    MoveMatrix* moveMat = malloc(sizeof(MoveMatrix));
    if (!moveMat) return NULL;

    moveMat->size = 0;
    moveMat->capacity = capacity;
    moveMat->matrix = malloc(capacity*sizeof(Move*));
    if (!moveMat->matrix) {
        free(moveMat);
        return NULL;
    }

    if(initMatrix(moveMat, capacity) == 0) {
        free(moveMat);
        return NULL;
    }

    return moveMat;
}


int initMatrix(MoveMatrix* moveMat, int capacity) {
    if (!moveMat) return 0;

    for (int i = 1; i < capacity; i++) {
        moveMat->matrix[i] = malloc(capacity * sizeof(Move));
        if (!moveMat->matrix[i]) {
            for (int j = 1; j < i; j++) {
                free(moveMat->matrix[j]);
            }
            free(moveMat->matrix);
            moveMat->matrix = NULL;
            return 0;
        }

        for (int j = 1; j < capacity; j++) {
            moveMat->matrix[i][j].distance = 0.0f;
            moveMat->matrix[i][j].duree = 0.0f;
        }
    }

    moveMat->size = capacity;
    return 1;
}


void freeMoveMat(MoveMatrix* moveMat) {
    if (moveMat == NULL) return;

    for (int i = 0; i < moveMat->capacity; i++) {
        free(moveMat->matrix[i]);
    }

    free(moveMat->matrix); 
    free(moveMat);  
}


Move** resizeMatrix(Move** matrix, int oldSize, int newSize) {
    Move** newMatrix = realloc(matrix, newSize * sizeof(Move*));
    if (!newMatrix) return NULL;

    for(int i = oldSize; i < newSize; i++) {
        newMatrix[i] = malloc(newSize * sizeof(Move));
        if (!newMatrix[i]) {
            for (int j = oldSize; j < i; j++) free(newMatrix[j]);
            return NULL;
        }
    }

    for(int i = 0; i < oldSize; i++) {
        Move* row = realloc(newMatrix[i], newSize * sizeof(Move));
        if (!row) {
            return NULL;
        }
        newMatrix[i] = row;
    }

    return newMatrix;
}


void printMatrix(MoveMatrix* moveMat) {
    if (!moveMat) {
        fprintf(stderr, "error printMatrix : null");
        return;
    }
    printf("\t");
    /* for (int i = 0; i < moveMat->size; i++) {
        printf("%d\t", i);
    } */
    printf("\n");

    for (int i = 1; i < moveMat->size; i++) {
        //printf("%d\t", i);
        for (int j = 1; j < moveMat->size; j++) {
            printf("[%d, %d] - %3f\n", i, j, moveMat->matrix[i][j].distance);
        }
        printf("\n");
    }
}



void readFile(char* filename, MoveMatrix* moveMat) {
    if (moveMat == NULL) {
        fprintf(stderr, "error readFile 1\n");
        return;
    }

    FILE* f = fopen(filename, "r");
    if (!f) {
        fprintf(stderr, "error readFile 2");
        return;
    }

    int d, a;
    float dist, duree;
    char buffer[1024];

    while (fgets(buffer, sizeof(buffer), f) != NULL) {
        char* value = strtok(buffer, ",");
        if (!value) continue;
        d = atoi(value);

        value = strtok(NULL, ",");
        if (!value) continue;
        a = atoi(value);

        value = strtok(NULL, ",");
        if (!value) continue;
        dist = atof(value);

        value = strtok(NULL, ",");
        if (!value) continue;
        duree = atof(value);

        if (d <= 0 || a <= 0) continue;

        int maxIndex = d > a ? d : a;
        if (maxIndex >= moveMat->capacity) {
            if (resizeMoveMatrix(moveMat, maxIndex + 5) != 1) {
                fprintf(stderr, "error readfile -> resizeMoveMatrix\n");
                fclose(f);
                return;
            }
        }

        moveMat->matrix[d][a].distance = dist;
        moveMat->matrix[d][a].duree = duree;

        if (d >= moveMat->size) moveMat->size = d+1;
        if (a >= moveMat->size) moveMat->size = a+1;
    }

    fclose(f);
}


int resizeMoveMatrix(MoveMatrix* moveMat, int newCapacity) {
    if (moveMat == NULL || newCapacity <= moveMat->capacity) return 0;

    Move** newMatrix = realloc(moveMat->matrix, newCapacity*sizeof(Move*));
    if (!newMatrix) {
        fprintf(stderr, "error resizeMoveMat 1");
        return -1;
    }

    moveMat->matrix = newMatrix;

    for (int i = 0; i < moveMat->capacity; i++) {
        Move* newRow = realloc(moveMat->matrix[i], newCapacity*sizeof(Move));
        if (!newRow) {
            fprintf(stderr, "error resizeMoveMat 2");
            return -1;
        }

        for (int j = moveMat->capacity; j < newCapacity; j++) {
            newRow[j].distance = 0.0f;
            newRow[j].duree = 0.0f;
        }

        moveMat->matrix[i] = newRow;
    }

    for (int i = moveMat->capacity; i < newCapacity; i++) {
        moveMat->matrix[i] = malloc(newCapacity * sizeof(Move));
        if (!moveMat->matrix[i]) {
            fprintf(stderr, "error resizeMOveMat 3");
            return -1;
        }

        for (int j = 0; j < newCapacity; j++) {
            moveMat->matrix[i][j].distance = 0.0f;
            moveMat->matrix[i][j].duree = 0.0f;
        }
    }

    moveMat->capacity = newCapacity;
    return 1;
}
