/*projet-cerp-structure.c*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
//#include <hpdf.h>


/*
 * Projet CERP Rouen - Optimisation des chemins de livraison
 * Structure globale du projet
 */

// Structure principale pour représenter les pharmacies
typedef struct {
    int id;
    double latitude;
    double longitude;
    int temps_livraison;  // en secondes (par défaut 180 secondes, soit 3 minutes)
} Pharmacie;

// Structure pour représenter une tournée
typedef struct {
    Pharmacie* pharmacies;
    double distance_totale;
    int duree_totale;      // en secondes
} Tournee;

// Structure pour représenter une Individu complète
typedef struct {
    Tournee* tournees;
    int nombre_tournees;
    double distance_totale;
    double cout_carburant;
} Individu;

// Fonctions principales du programme
int lire_csv(const char* fichier, Pharmacie** pharmacies);
int geocoder_pharmacies(Pharmacie* pharmacies, int nombre);
double calculer_distance(double lat1, double lon1, double lat2, double lon2);
Individu* optimiser_tournees(Pharmacie* pharmacies, int nombre_pharmacies, double lat_depot, double lon_depot);
void generer_pdf(Individu* Individu, const char* chemin_sortie);

// Programme principal
int main(int argc, char** argv) {
    if (argc < 3) {
        printf("Usage: %s <fichier_csv> <dossier_sortie>\n", argv[0]);
        return 1;
    }
    
    // Coordonnées de l'entrepôt CERP à Mareuil-lès-Meaux
    const double LAT_DEPOT = 48.9342;  // À ajuster avec les coordonnées réelles
    const double LON_DEPOT = 2.8867;   // À ajuster avec les coordonnées réelles
    
    // Lire les données d'entrée
    Pharmacie* pharmacies = NULL;
    int nombre_pharmacies = lire_csv(argv[1], &pharmacies);
    
    if (nombre_pharmacies <= 0) {
        printf("Erreur lors de la lecture du fichier CSV\n");
        return 1;
    }
    
    // Géocoder les adresses
    if (geocoder_pharmacies(pharmacies, nombre_pharmacies) != 0) {
        printf("Erreur lors du géocodage des adresses\n");
        return 1;
    }
    
    // Optimiser les tournées
    Individu* Individu = optimiser_tournees(pharmacies, nombre_pharmacies, LAT_DEPOT, LON_DEPOT);
    
    if (Individu == NULL) {
        printf("Erreur lors de l'optimisation des tournées\n");
        return 1;
    }
    
    // Générer les PDF
    generer_pdf(Individu, argv[2]);
    
    // Libération de la mémoire
    // TODO: Libérer la mémoire allouée
    
    return 0;
}
