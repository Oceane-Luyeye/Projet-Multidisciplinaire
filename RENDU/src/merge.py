import os
import csv
import math
import pandas as pd
import requests
import openrouteservice

# Configuration
api_key = "5b3ce3597851110001cf62487e2739ab43d8469aa4faf8da7acc850d"
base_csv_path = 'data/input/livraison70.csv'
all_csv_path = 'data/database/all.csv'
output_dir = 'data/output/csv/'

# Chargement des données
base_df = pd.read_csv(base_csv_path, header=None, names=['name', 'street', 'postal_code', 'city'])
all_df = pd.read_csv(all_csv_path)

# Sélection du dépôt (premier match contenant "dépôt")
depot_row = all_df[all_df['name'].str.lower().str.contains('dépôt', case=False)].iloc[0:1].copy()

# Fusion des adresses clients avec coordonnées
merged_df = pd.merge(base_df, all_df, on=['name', 'street', 'postal_code', 'city'], how='inner')
merged_df = merged_df[['name', 'street', 'postal_code', 'city', 'latitude', 'longitude']]

# Ajout du dépôt au début avec id=0
full_df = pd.concat([depot_row, merged_df], ignore_index=True)
full_df.insert(0, 'id', range(len(full_df)))

# Création du suffixe basé sur le nombre de clients (hors dépôt)
suffix = len(full_df) - 1

# Sauvegarde des coordonnées
coord_path = os.path.join(output_dir, f'coordinates_{suffix}.csv')
full_df.to_csv(coord_path, index=False)
print(f"📍 Coordonnées enregistrées dans : {coord_path}")

# Chargement des coordonnées
df_coords = pd.read_csv(coord_path)
required_columns = {'id', 'latitude', 'longitude'}
if not required_columns.issubset(df_coords.columns):
    raise ValueError(f"Le fichier doit contenir les colonnes : {required_columns}")

# Préparation des points
locations = []
ids = []
for _, row in df_coords.iterrows():
    try:
        lat = float(row['latitude'])
        lon = float(row['longitude'])
        locations.append([lon, lat])
        ids.append(row['id'])
    except ValueError:
        print(f" coordonnées invalides ignorées : {row}")

# Configuration ORS
client = openrouteservice.Client(key=api_key)
MAX_ROUTES = 3500
N = len(locations)
max_block = int(math.floor(math.sqrt(MAX_ROUTES)))
print(f"Nombre de points (incluant dépôt) : {N} | Taille max bloc : {max_block} x {max_block}")

# Génération de la matrice
matrix_path = os.path.join(output_dir, f'matrix_{suffix}.csv')
count = 0
with open(matrix_path, 'w', newline='', encoding='utf-8') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["origin_id", "destination_id", "distance_km", "time_min"])

    for i_start in range(0, N, max_block):
        for j_start in range(0, N, max_block):
            origins = locations[i_start:i_start + max_block]
            destinations = locations[j_start:j_start + max_block]
            origin_ids = ids[i_start:i_start + max_block]
            destination_ids = ids[j_start:j_start + max_block]

            body = {
                "locations": origins + destinations,
                "sources": list(range(len(origins))),
                "destinations": list(range(len(origins), len(origins) + len(destinations))),
                "metrics": ["distance", "duration"],
                "units": "m"
            }

            headers = {
                'Accept': 'application/json',
                'Authorization': api_key,
                'Content-Type': 'application/json'
            }

            print(f"{len(origins)} origines × {len(destinations)} destinations")

            response = requests.post(
                "https://api.openrouteservice.org/v2/matrix/driving-car",
                json=body,
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                distances = data.get('distances', [])
                durations = data.get('durations', [])

                for i, origin_id in enumerate(origin_ids):
                    for j, destination_id in enumerate(destination_ids):
                        if origin_id != destination_id:
                            try:
                                distance_km = distances[i][j] / 1000.0
                                time_min = durations[i][j] / 60.0
                                writer.writerow([origin_id, destination_id, distance_km, time_min])
                                count += 1
                            except (IndexError, TypeError) as e:
                                print(f"Données manquantes pour {origin_id} → {destination_id} : {e}")
                                writer.writerow([origin_id, destination_id, None, None])
            else:
                print(f"echec appel ORS bloc {i_start}-{j_start} : {response.status_code} - {response.text}")
                exit(1)

print(f"\n Matrice générée : {matrix_path} | Total de lignes : {count}")

# Tri final
print("Tri des lignes par origin_id/destination_id...")
df_matrix = pd.read_csv(matrix_path)
df_sorted = df_matrix.sort_values(by=['origin_id', 'destination_id'])
df_sorted.to_csv(matrix_path, index=False)
print("✅ Matrice triée.")

# Vérification
print("\n Vérification de la complétude...")
expected_count = N - 1
missing_flag = False
grouped = df_sorted.groupby('origin_id').size()

for origin_id in sorted(ids):
    count_found = grouped.get(origin_id, 0)
    if count_found != expected_count:
        print(f"{origin_id} a {count_found} lignes (attendu : {expected_count})")
        missing_flag = True

if not missing_flag:
    print("✅ Toutes les lignes attendues sont présentes pour chaque id (sauf self-loop exclue).")