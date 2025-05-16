#ifndef MOVE_H
#define MOVE_H


/**
 * @brief type qui représente un déplacmeet entre deux points
 * 
 * @param distance : la distances entre deux points
 * @param duree  : la durée du déplacement entre deux points
 * 
 */
typedef struct {
    //int depart;
    //int arrivee;
    float distance;
    float duree;
} Move;


/**
 * @brief structure représentant une matrice de move
 * 
 * @param size taille courante de la matrice
 * @param capacity capacité de la matrice (capacity >= size)
 * @param matrix matrice de move
 * 
 */
typedef struct {
    int size;
    int capacity;
    Move** matrix;
} MoveMatrix;

#endif