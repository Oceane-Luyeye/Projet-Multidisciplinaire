import subprocess
import csv
from datetime import datetime, timedelta
import pprint
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os
import random  
import colorsys

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

def execute(file_matrix_csv, *_):
    try:
        subprocess.run(["make", "clean"], check=True)
        print("Compiling genetic.c on this machine…")
        subprocess.run(["make"], check=True)
        print("Lancement de ./genetic…")
        result = subprocess.run(["./genetic", file_matrix_csv], check=False)
        if result.returncode != 0:
            print("Erreur d'exécution")
            return "execute() error"
        print("Exécution réussie du programme genetic")
        return None
    except Exception as e:
        print("Exception lors de l'exécution :", str(e))
        return "error : " + str(e)

def parse_routes_from_text(text):
    routes = []
    totaux = {}

    lines = text.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("Total_Distance"):
            try:
                parts = line.split('|')
                dist_part = parts[0].split('=')[1].strip().split()[0]
                time_part = parts[1].split('=')[1].strip().split()[0]
                totaux = {
                    "distance_totale": float(dist_part),
                    "temps_total": float(time_part)
                }
            except Exception as e:
                print(f"Erreur lors du parsing des totaux : {line} — {e}")
            continue

        if ':' not in line.split('|')[0]:
            continue
        try:
            chemin_part, *infos = line.split('|')
            route_str = chemin_part.split(':', 1)[1].strip()
            route_ids = [int(x.strip()) for x in route_str.split('->')]
            distance = float([x for x in infos if 'Distance' in x][0].split(':')[1])
            time = float([x for x in infos if 'Time' in x][0].split(':')[1])
            routes.append({
                "route": route_ids,
                "distance": distance,
                "time": time
            })
        except Exception as e:
            print(f"Erreur de parsing sur la ligne : {line} — {e}")
            continue
    return routes, totaux

def fusionne_trajet(trajets):
    camions = []
    i = 0
    while i < len(trajets):
        if i + 1 < len(trajets):
            t1 = trajets[i]
            t2 = trajets[i + 1]
            route_fusionnee = t1["route"] + t2["route"][1:]
            distance_totale = t1["distance"] + t2["distance"]
            time_total = t1["time"] + t2["time"]
            camions.append({
                "route": route_fusionnee,
                "distance": distance_totale,
                "time": time_total
            })
            i += 2
        else:
            camions.append(trajets[i])
            i += 1
    return camions

def regroup_and_split_by_truck(trajets):
    """
    Regroupe les trajets 2 par 2 mais garde la séparation (matin/soir) pour chaque camion.
    Retourne une liste : [{matin: {...}, soir: {...}}, ...]
    """
    camions = []
    i = 0
    while i < len(trajets):
        if i + 1 < len(trajets):
            t1 = trajets[i]
            t2 = trajets[i + 1]
            camions.append({
                "matin": t1,
                "soir": t2
            })
            i += 2
        else:
            camions.append({"matin": trajets[i], "soir": None})
            i += 1
    return camions

def generate_camion_colors(camion_index):
    """
    Génère deux couleurs bien distinctes mais proches pour un camion donné :
    - La première (matin) sera plus claire
    - La seconde (soir) sera plus foncée
    """
    base_hue = (camion_index * 0.618033988749895) % 1.0
    matin_sat = 0.65 + random.random() * 0.2
    matin_val = 0.90 + random.random() * 0.08
    r1, g1, b1 = colorsys.hsv_to_rgb(base_hue, matin_sat, matin_val)
    color_matin = "#%02x%02x%02x" % (int(r1*255), int(g1*255), int(b1*255))
    soir_sat = matin_sat * 0.85
    soir_val = matin_val * 0.7
    r2, g2, b2 = colorsys.hsv_to_rgb(base_hue, soir_sat, soir_val)
    color_soir = "#%02x%02x%02x" % (int(r2*255), int(g2*255), int(b2*255))
    return color_matin, color_soir

def createJsonObject(file_matrix_csv, file_coordinate_csv, tab, totaux):
    matrix_dist, matrix_time = getMatrix(file_matrix_csv)
    adresses = get_adresses_pharmacie(file_coordinate_csv)
    result = {}
    for i, trajet_data in enumerate(tab):
        route = trajet_data["route"]
        trajet_dict = {}
        distance_totale = 0
        duree_totale = 0
        current_time = datetime.strptime("09:00", "%H:%M")
        fin_matin = datetime.strptime("12:00", "%H:%M")
        debut_aprem = datetime.strptime("15:00", "%H:%M")
        duree_tournee = 0
        in_matin = 1
        for j in range(len(route) - 1):
            depart = route[j]
            arrivee = route[j + 1]
            duree = matrix_time[depart][arrivee]
            distance = matrix_dist[depart][arrivee]
            if j > 0:
                current_time += timedelta(minutes=3)
            if (in_matin and (current_time + timedelta(minutes=duree) > fin_matin or duree_tournee + duree > 180)):
                current_time = debut_aprem
                duree_tournee = 0
                in_matin = 0
            heure_depart = current_time
            heure_arrivee = heure_depart + timedelta(minutes=duree)
            etape = {
                "pharmacie_depart": {
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
            'duree_totale_min': trajet_data['time'],
            'distance_total_km': trajet_data['distance'],
            'cout_carburant_eur': round(((float(trajet_data['distance'])* 8.5) / 100) * 1.72, 2),
            'total_carburant_litre': round((float(trajet_data['distance']) * 8.5) / 100, 2)
        }
    return result, totaux

def generate_routes_from_file(file_matrix_csv, file_coordinate_csv, output_file): 
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            text = f.read()
        tab, totaux = parse_routes_from_text(text)
        tab_fusion = fusionne_trajet(tab)
        result = createJsonObject(file_matrix_csv, file_coordinate_csv, tab_fusion, totaux)
        pprint.pprint(result)
        return result
    except Exception as e:
        return {"error": "generate_routes_from_file() error : " + str(e)}

def create_route_map(camions, coords_csv_path, output_image_path):
    """
    camions: liste [{matin: {...}, soir: {...}}, ...]
    """
    try:
        df_coords = pd.read_csv(coords_csv_path)
        fig, ax = plt.subplots(figsize=(12, 8))
        all_points = []
        for i, c in enumerate(camions):
            color_matin, color_soir = generate_camion_colors(i)
            if c["matin"] and c["matin"]["route"]:
                route = c["matin"]["route"]
                valid_indices = [idx for idx in route if idx < len(df_coords)]
                if valid_indices:
                    sous_df = df_coords.iloc[valid_indices]
                    gdf = gpd.GeoDataFrame(
                        geometry=gpd.points_from_xy(sous_df["longitude"], sous_df["latitude"]),
                        crs="EPSG:4326"
                    ).to_crs(epsg=3857)
                    ax.plot(gdf.geometry.x, gdf.geometry.y,
                        marker='o', linestyle='-', linewidth=2, markersize=6,
                        color=color_matin, label=f"Camion {i+1} matin")
                    for x, y, idx in zip(gdf.geometry.x, gdf.geometry.y, valid_indices):
                        ax.text(x, y + 50, str(idx), fontsize=8, ha='center',
                                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.7))
                    all_points.extend(gdf.geometry)
            if c["soir"] and c["soir"]["route"]:
                route = c["soir"]["route"]
                valid_indices = [idx for idx in route if idx < len(df_coords)]
                if valid_indices:
                    sous_df = df_coords.iloc[valid_indices]
                    gdf = gpd.GeoDataFrame(
                        geometry=gpd.points_from_xy(sous_df["longitude"], sous_df["latitude"]),
                        crs="EPSG:4326"
                    ).to_crs(epsg=3857)
                    ax.plot(gdf.geometry.x, gdf.geometry.y,
                        marker='o', linestyle='--', linewidth=2, markersize=6,
                        color=color_soir, label=f"Camion {i+1} soir")
                    for x, y, idx in zip(gdf.geometry.x, gdf.geometry.y, valid_indices):
                        ax.text(x, y + 50, str(idx), fontsize=8, ha='center',
                                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.7))
                    all_points.extend(gdf.geometry)
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
