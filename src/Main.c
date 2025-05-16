#include <stdio.h>
#include <stdlib.h>
#include "../include/processFile.h"


int main(int argc, char** argv) {
    MoveMatrix* moveMat = initMovementMatrix(SIZE);

    readFile("data/depot_with_id/livraison30_matrix_and_time_with_ids.csv", moveMat);
    printMatrix(moveMat);

    freeMoveMat(moveMat);

    return 0;
}