#ifndef PROCESSFILE_H
#define PROCESSFILE_H

#include "./Move.h"

#define SIZE 10

/**
 * @brief fonction d'initialisation d'une matrice de movement, mettant toutes les case à 0
 * 
 * @param moveMat 
 * @param capacity 
 * @return 1 si la matrice est correctement initialisée, 0 sinon
 */
int initMatrix(MoveMatrix* moveMat, int capacity);


/**
 * @brief fonction d'initialisation d'une structure MoveMatrix
 * 
 * @param capacity capacité de base de la matrice
 * @return une structure initialisé MoveMatrix* si succès sinon NULL 
 */
MoveMatrix* initMovementMatrix(int capacity);


/**
 * @brief fonction de liberation d'une structure MoveMatrix
 * 
 * @param moveMat pointeur de structure à libéré
 */
void freeMoveMat(MoveMatrix* moveMat);


/**
 * @brief fonction de reallocation de la matrice
 * 
 * @param moveMat structure contenant la matrice à agrandir
 * @param newCapacity capacité à additionner
 * @return 1 si tout s'est bien passé, -1 sinon
 */
int resizeMoveMatrix(MoveMatrix* moveMat, int newCapacity);


/**
 * @brief fonction de remplissage de la matrice en fonction du fichier de données
 * 
 * @param filename chemin relatif du fichier de donnée
 * @param moveMat structure contenant la matrice à remplir
 */
void readFile(char* filename, MoveMatrix* moveMat);


/**
 * @brief FOnction d'affichage de la matrice
 * 
 * @param moveMat structure contentant la matrice à afficher
 */
void printMatrix(MoveMatrix* moveMat);

#endif