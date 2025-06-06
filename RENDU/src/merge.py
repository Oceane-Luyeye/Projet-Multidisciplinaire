import os
import csv
import math
import pandas as pd
import requests
import openrouteservice

api_key = "5b3ce3597851110001cf62487e2739ab43d8469aa4faf8da7acc850d"
base_csv_path = 'RENDU/data/input/livraison10.csv'
all_csv_path = 'RENDU/data/database/all.csv'
output_dir = 'RENDU/data/output/csv/'



base_df = pd.read_csv(base_csv_path, header=None, names=['name', 'street', 'postal_code', 'city'])
all_df = pd.read_csv(all_csv_path)

# .merge to get coordinates
merged_df = pd.merge(base_df, all_df, on=['name', 'street', 'postal_code', 'city'], how='inner')
merged_df = merged_df[['name', 'street', 'postal_code', 'city', 'latitude', 'longitude']]
merged_df.insert(0, 'id', range(len(merged_df)))

coord_filename = f'coordinates_{len(merged_df)}.csv'
coord_path = os.path.join(output_dir, coord_filename)
merged_df.to_csv(coord_path, index=False)
print(f" saved in : {coord_path}")



# Load coordinates again
df_coords = pd.read_csv(coord_path)
required_columns = {'id', 'latitude', 'longitude'}
if not required_columns.issubset(df_coords.columns):
    raise ValueError(f"Le fichier doit contenir les colonnes : {required_columns}")

# Prepare locations and IDs
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

# setup
client = openrouteservice.Client(key=api_key)
MAX_ROUTES = 3500 # imposé par api
N = len(locations)
max_block = int(math.floor(math.sqrt(MAX_ROUTES)))
print(f"🔢 Nombre de points : {N} | Taille max bloc : {max_block} x {max_block}")

# Output matrix CSV
matrix_filename = f'matrix_{len(df_coords)}.csv'
matrix_path = os.path.join(output_dir, matrix_filename)

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

print(f"\n Matrice générée : {matrix_path} | Total lignes : {count}")

# Sort and verify
print("tri des lignes...")
df_matrix = pd.read_csv(matrix_path)
df_sorted = df_matrix.sort_values(by=['origin_id', 'destination_id'])
df_sorted.to_csv(matrix_path, index=False)
print("mtrice triée par origin_id puis destination_id.")

print("\n🔍 Vérification de la complétude...")
expected_count = N - 1
missing_flag = False
grouped = df_sorted.groupby('origin_id').size()

for origin_id in sorted(ids):
    count_found = grouped.get(origin_id, 0)
    if count_found != expected_count:
        print(f"{origin_id} a {count_found} lignes (attendu : {expected_count})")
        missing_flag = True

if not missing_flag:
    print("All lignes attendues sont présentes pour chaque id")