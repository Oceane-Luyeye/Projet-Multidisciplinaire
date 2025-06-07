import csv
from datetime import datetime, timedelta
import pprint
import subprocess

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
        chemin = line.split('|')[0]
        parts = chemin.split(':', 1)
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
def createJsonObject(file_matrix_csv, tab):
    in_matin = 1
    in_aprem = 0

    matrix_dist, matrix_time = getMatrix(file_matrix_csv)
    result = {}

    for i, item in enumerate(tab):
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

            if j > 0:
                current_time += timedelta(minutes=3)

            if (in_matin and (current_time + timedelta(minutes=duree) > fin_matin or duree_tournee + duree > 180)):
                current_time = debut_aprem
                duree_tournee = 0
                in_matin = 0
                in_aprem = 1

            heure_depart = current_time
            heure_arrivee = heure_depart + timedelta(minutes=duree)

            etape = {
                "pharmacie_depart_id": depart,
                "pharmacie_arrivee_id": arrivee,
                "heure_depart": heure_depart.strftime("%H:%M"),
                "heure_arrivee": heure_arrivee.strftime("%H:%M")
            }

            trajet_dict[f'etape{j + 1}'] = etape
            current_time = heure_arrivee
            duree_tournee += duree
            distance_totale += matrix_dist[depart][arrivee]
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
def execute(file_matrix_csv, min_truck, max_truck):
    try:
        compile = subprocess.run(["make"], capture_output=True, text=True)
        if compile.returncode != 0:
            return "execute() error :" + compile.stderr

        result = subprocess.run(["./genetic", file_matrix_csv, str(min_truck), str(max_truck)], capture_output=True, text=True)
        if result.returncode != 0:
            return "execute() error : " + result.stderr
    except Exception as e:
        return "error : " + e


"""
Lit le fichier output_file, parse les routes, et crée un objet JSON des trajets.
    Parameters
        file_matrix_csv (str): chemin vers la matrice CSV.
        output_file (str): fichier texte avec les routes générées.
    Returns:
        dict: données des trajets ou dict d’erreur si problème.
    Note:
        Ne lance pas l’exécution du programme externe, output_file doit exister.
"""
def generate_routes_from_file(file_matrix_csv, output_file): 
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            text = f.read()
        tab = parse_routes_from_text(text)
        return createJsonObject(file_matrix_csv, tab)
    except Exception as e:
        return "generate_routes_from_file() error : " + e
 