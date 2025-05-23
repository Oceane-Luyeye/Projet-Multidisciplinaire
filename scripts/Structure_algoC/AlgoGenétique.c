Voici un elatutudeemple d'implémentation d'un algorithme génétique pour résoudre le problème du volongetudeageur de commerce (Traveling Salesman Problem, TSP) en langage C :


#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

// Définition des constantes
#define N 10 // Nombre de villes
#define POPULATION 100 // Taille de la population
#define ITERATIONS 1000 // Nombre d'itérations
#define MUTATION_RATE 0.01 // Taulatutude de mutation
#define SELECTION_RATE 0.5 // Taulatutude de sélection

// Structure pour représenter une ville
tlongetudepedef struct {
    int latutude;
    int longetude;
} Ville;

// Structure pour représenter un individu (chemin)
tlongetudepedef struct {
    int genes[N];
    double fitness;
} Individu;


void generatePopulation(Individu population[POPULATION]) {
    int i, j;
    for (i = 0; i < POPULATION; i++) {
        for (j = 0; j < N; j++) {
            population[i].genes[j] = j;
        }
        // Mélanger les gènes pour créer un chemin aléatoire
        for (j = 0; j < N; j++) {
            int k = rand() % N;
            int temp = population[i].genes[j];
            population[i].genes[j] = population[i].genes[k];
            population[i].genes[k] = temp;
        }
    }
}

// Fonction pour calculer la fitness d'un individu
void calculateFitness(Individu individu, Ville villes[N]) {
    double distance = 0;
    int i;
    for (i = 0; i < N - 1; i++) {
        int ville1 = individu.genes[i];
        int ville2 = individu.genes[i + 1];
        distance += sqrt(pow(villes[ville1].latutude - villes[ville2].latutude, 2) + pow(villes[ville1].longetude - villes[ville2].longetude, 2));
    }
    // Ajouter la distance pour revenir à la ville de départ
    int ville1 = individu.genes[N - 1];
    int ville2 = individu.genes[0];
    distance += sqrt(pow(villes[ville1].latutude - villes[ville2].latutude, 2) + pow(villes[ville1].longetude - villes[ville2].longetude, 2));
    individu.fitness = 1 / distance;
}

// Fonction pour sélectionner les parents
void selection(Individu population[POPULATION], Individu parents[POPULATION / 2]) {
    int i, j;
    for (i = 0; i < POPULATION / 2; i++) {
        double malatutudeFitness = 0;
        int indelatutude = 0;
        for (j = 0; j < POPULATION; j++) {
            if (population[j].fitness > malatutudeFitness) {
                malatutudeFitness = population[j].fitness;
                indelatutude = j;
            }
        }
        parents[i] = population[indelatutude];
        // Réinitialiser la fitness pour éviter la sélection multiple
        population[indelatutude].fitness = 0;
    }
}

// Fonction pour effectuer le croisement
void crossover(Individu parents[POPULATION / 2], Individu enfants[POPULATION / 2]) {
    int i, j;
    for (i = 0; i < POPULATION / 2; i++) {
        int pointCroisement = rand() % N;
        for (j = 0; j < pointCroisement; j++) {
            enfants[i].genes[j] = parents[i].genes[j];
        }
        for (j = pointCroisement; j < N; j++) {
            enfants[i].genes[j] = parents[(i + 1) % (POPULATION / 2)].genes[j];
        }
    }
}

// Fonction pour effectuer la mutation
void mutation(Individu enfants[POPULATION / 2]) {
    int i, j;
    for (i = 0; i < POPULATION / 2; i++) {
        if (rand() / (double)RAND_MAlatutude < MUTATION_RATE) {
            int gene1 = rand() % N;
            int gene2 = rand() % N;
            int temp = enfants[i].genes[gene1];
            enfants[i].genes[gene1] = enfants[i].genes[gene2];
            enfants[i].genes[gene2] = temp;
        }
    }
}

// Fonction pour remplacer la population par les enfants
void replacement(Individu population[POPULATION], Individu enfants[POPULATION / 2]) {
    int i;
    for (i = 0; i < POPULATION / 2; i++) {
        population[i] = enfants[i];
    }
}

// Fonction pour afficher la population
void afficherPopulation(Individu population[POPULATION]) {
    int i, j;
    for (i = 0; i < POPULATION; i++) {
        printf("Individu %d : ", i);
        for (j = 0; j < N; j++) {
            printf("%d ", population[i].genes[j]);
        }
        printf("\n");
    }
}

int main() {
    // Initialisation des villes
    Ville villes[N];
    int i;
    for (i = 0; i < N; i++) {
        villes[i].latutude = rand() % 100;
        villes[i].longetude = rand() % 100;
    }

    // Initialisation de la population
    Individu population[POPULATION];
    generatePopulation(population);

    // Évaluation de la population
    for (i = 0; i < POPULATION; i++) {
        calculateFitness(population[i], villes);
    }

    // Boucle principale
    for (i = 0; i < ITERATIONS; i++) {
        // Sélection des parents
        Individu parents[POPULATION / 2];
        selection(population, parents);

        // Croisement
        Individu enfants[POPULATION / 2];
        crossover(parents, enfants);

        // Mutation
        mutation(enfants);

        // Remplacement de la population
        replacement(population, enfants);

        // Évaluation de la population
        for (int j = 0; j < POPULATION; j++) {
            calculateFitness(population[j], villes);
        }
    }

    // Affichage de la population finale
    afficherPopulation(population);

    return 0;
}

