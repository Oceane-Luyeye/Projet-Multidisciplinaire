import csv
from datetime import datetime, timedelta
import pprint
import subprocess
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os
import random  
"""
Lit un fichier CSV de matrice distance/temps et crée deux matrices (distances et durées)
  Parameters:
    - file_matrix_csv (str) : chemin vers le fichier CSV.
  Returns:
    - tuple (dist_matrice, dur_matrice) : matrices 2D
"""
def getMatrix(file_matrix_csv):
    max_id = 0
    data = []

    with open(file_matrix_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            o = int(row['origin_id'])
            d = int(row['destination_id'])
            dist = float(row['distance_km'])
            dur = float(row['time_min'])
            data.append((o, d, dist, dur))
            max_id = max(max_id, o, d)

    dist_matrice = [[0]*(max_id+1) for _ in range(max_id+1)]
    dur_matrice = [[0]*(max_id+1) for _ in range(max_id+1)]

    for o, d, dist, dur in data:
        dist_matrice[o][d] = dist
        dur_matrice[o][d] = dur

    return dist_matrice, dur_matrice


def get_adresses_pharmacie(file_coordinate_csv):
    adresses = {}
    
    with open(file_coordinate_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_pharma = int(row['id'])
            nom = row['name']
            adresses[id_pharma] = nom
 
    return adresses

""" 
Analyse un texte contenant des routes au format 'chemin: id1 -> id2 -> id3 | ...' et extrait la liste des itinéraires
  Parameters:
    - text (str) : texte à parser.
  Returns
    - list of list of int 
  Exemple:
    texte = 1: 0 -> 1 -> 12 -> 9 -> 3 -> 14 -> 0 | Distance: 98.80 | Time: 135.54
            2: 0 -> 6 -> 13 -> 5 -> 10 -> 4 -> 0 | Distance: 88.19 | Time: 121.29
            3: 0 -> 11 -> 2 -> 8 -> 7 -> 0 | Distance: 81.99 | Time: 120.77

    retour : [[0, 1, 12, 9, 3, 14, 0],[0, 6, 13, 5, 10, 4, 0],[0, 11, 2, 8, 7, 0]]
"""
def parse_routes_from_text(text):
    routes = []
    lines = text.strip().split('\n')

    for line in lines:
        if line.strip():  # Éviter les lignes vides
            chemin = line.split('|')[0]
            parts = chemin.split(':', 1)
            if len(parts) == 2:
                _, route_str = parts
                ids = [int(x.strip()) for x in route_str.strip().split('->')]
                routes.append(ids)
    return routes

"""
Construit un objet JSON détaillant les trajets, durées, distances et coûts à partir des routes et de la matrice
  Parameters:
    - file_matrix_csv (str) : chemin vers le fichier CSV de matrice
    - tab (list of list of int) : routes extraites 
  Returns:
    - dict : objet avec informations sur chaque camion (trajet, durée, distance, coût carburant)
"""
def createJsonObject(file_matrix_csv, file_coordinate_csv, tab):
    matrix_dist, matrix_time = getMatrix(file_matrix_csv)
    adresses = get_adresses_pharmacie(file_coordinate_csv)
    result = {}

    for i, item in enumerate(tab):
        in_matin = 1
        in_aprem = 0
        
        trajet_dict = {}
        distance_totale = 0
        duree_totale = 0

        current_time = datetime.strptime("09:00", "%H:%M")
        fin_matin = datetime.strptime("12:00", "%H:%M")
        debut_aprem = datetime.strptime("15:00", "%H:%M")

        duree_tournee = 0

        for j in range(len(item) - 1):
            depart = item[j]
            arrivee = item[j + 1]
            duree = matrix_time[depart][arrivee]
            distance = matrix_dist[depart][arrivee]

            # Temps d'arrêt de 3 minutes pour les livraisons (sauf premier trajet)
            if j > 0:
                current_time += timedelta(minutes=3)

            # Gestion de la pause déjeuner
            if (in_matin and (current_time + timedelta(minutes=duree) > fin_matin or duree_tournee + duree > 180)):
                current_time = debut_aprem
                duree_tournee = 0
                in_matin = 0
                in_aprem = 1

            heure_depart = current_time
            heure_arrivee = heure_depart + timedelta(minutes=duree)

            etape = {
                "pharmacie_depart":{
                    "pharmacie_depart_id": depart,
                    "nom_pharmacie": adresses[depart]
                },
                "pharmacie_arrivee": {
                    "pharmacie_arrivee_id": arrivee,
                    "nom_pharmacie": adresses[arrivee]
                },
                "heure_depart": heure_depart.strftime("%H:%M"),
                "heure_arrivee": heure_arrivee.strftime("%H:%M")
            }

            trajet_dict[f'etape{j + 1}'] = etape
            current_time = heure_arrivee
            duree_tournee += duree
            distance_totale += distance
            duree_totale += duree

        result[f'camion{i + 1}'] = {
            'trajet': trajet_dict,
            'duree_totale_min': round(duree_totale, 2),
            'distance_total_km': round(distance_totale, 2),
            'cout_carburant_eur': round(((distance_totale * 8.5) / 100) * 1.72, 2),
            'total_carburant_litre': round((distance_totale * 8.5) / 100, 2)
        }
    return result

"""
Compile et exécute un programme externe 'genetic' (via make), avec les paramètres donnés.
  Parameters:
    - file_matrix_csv (str) : chemin fichier matrice.
    - min_truck (int) : nombre minimum de camions.
    - max_truck (int) : nombre maximum de camions.
"""
def execute(file_matrix_csv, *_): 
    try:
        compile_result = subprocess.run(["make"], capture_output=True, text=True)
        if compile_result.returncode != 0:
            print("Erreur de compilation :", compile_result.stderr)
            return "execute() error :" + compile_result.stderr

        result = subprocess.run(["./genetic", file_matrix_csv], capture_output=True, text=True)
        if result.returncode != 0:
            print("Erreur d'exécution :", result.stderr)
            return "execute() error : " + result.stderr

        print("Exécution réussie du programme genetic")
        return result.stdout

    except Exception as e:
        print("Exception lors de l'exécution :", str(e))
        return "error : " + str(e)



"""
Lit le fichier output_file, parse les routes, et crée un objet JSON des trajets.
    Parameters
        file_matrix_csv (str): chemin vers la matrice CSV.
        output_file (str): fichier texte avec les routes générées.
    Returns:
        dict: données des trajets ou dict d'erreur si problème.
    Note:
        Ne lance pas l'exécution du programme externe, output_file doit exister.
"""
def generate_routes_from_file(file_matrix_csv, file_coordinate_csv, output_file): 
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print("Contenu du fichier output.txt :")
        print(text)
        print("=" * 50)
        
        tab = parse_routes_from_text(text)
        print("Routes parsées :", tab)
        
        result = createJsonObject(file_matrix_csv, file_coordinate_csv, tab)
        print("Objet JSON créé :")
        pprint.pprint(result)
        
        return result
        
    except Exception as e:
        print("Erreur dans generate_routes_from_file :", str(e))
        return {"error": "generate_routes_from_file() error : " + str(e)}




def create_route_map(routes_data, coords_csv_path, output_image_path):
    """
    Crée une carte des trajets et la sauvegarde en image
    
    Parameters:
        routes_data (dict): Données des routes générées par pdf_data_builder
        coords_csv_path (str): Chemin vers le fichier CSV des coordonnées
        output_image_path (str): Chemin de sortie pour l'image de la carte
    """
    try:
        df_coords = pd.read_csv(coords_csv_path)
        
        routes = []
        for camion_key, camion_data in routes_data.items():
            route = []
            trajet = camion_data['trajet']
            
            if trajet:
                first_etape = list(trajet.values())[0]
                route.append(first_etape['pharmacie_depart_id'])
                
                for etape_data in trajet.values():
                    route.append(etape_data['pharmacie_arrivee_id'])
            
            if route:
                routes.append(route)
        
        if not routes:
            print("Aucune route trouvée pour créer la carte")
            return False
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Générateur de couleurs uniques
        used_colors = set()
        def generate_unique_color():
            while True:
                color = "#%06x" % random.randint(0, 0xFFFFFF)
                if color not in used_colors:
                    used_colors.add(color)
                    return color
        
        all_points = []
        
        for i, route in enumerate(routes):
            try:
                valid_indices = [idx for idx in route if idx < len(df_coords)]
                
                if not valid_indices:
                    continue
                    
                sous_df = df_coords.iloc[valid_indices]
                
                gdf = gpd.GeoDataFrame(
                    geometry=gpd.points_from_xy(sous_df["longitude"], sous_df["latitude"]),
                    crs="EPSG:4326"
                ).to_crs(epsg=3857)
                
                color = generate_unique_color()
                ax.plot(gdf.geometry.x, gdf.geometry.y, 
                       marker='o', linestyle='-', linewidth=2, markersize=6,
                       color=color, label=f"Camion {i+1}")
                
                for x, y, idx in zip(gdf.geometry.x, gdf.geometry.y, valid_indices):
                    ax.text(x, y + 50, str(idx), fontsize=8, ha='center', 
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.7))
                
                all_points.extend(gdf.geometry)
                
            except Exception as e:
                print(f"Erreur lors du traçage de la route {i+1}: {e}")
                continue
        
        if not all_points:
            print("Aucun point valide trouvé pour créer la carte")
            return False
        
        all_x = [pt.x for pt in all_points]
        all_y = [pt.y for pt in all_points]
        margin_x = (max(all_x) - min(all_x)) * 0.1
        margin_y = (max(all_y) - min(all_y)) * 0.1
        ax.set_xlim(min(all_x) - margin_x, max(all_x) + margin_x)
        ax.set_ylim(min(all_y) - margin_y, max(all_y) + margin_y)
        
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
        ax.set_aspect('equal')
        ax.set_title("Carte des tournées - Vue d'ensemble", fontsize=16, fontweight='bold')
        ax.axis("off")
        ax.legend(loc='upper left', bbox_to_anchor=(0, 1))
        
        plt.tight_layout()
        plt.savefig(output_image_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return True
        
    except Exception as e:
        print(f"Erreur lors de la création de la carte: {e}")
        return False
