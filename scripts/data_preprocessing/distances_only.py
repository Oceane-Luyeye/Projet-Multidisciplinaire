import csv
import os
import requests

api_key = "5b3ce3597851110001cf62487e2739ab43d8469aa4faf8da7acc850d"

base_filename = "livraison10"

input_file_coordinates = os.path.join('data/preprocessing/coordinates', f"{base_filename}_coordinates.csv")

output_dir_distances = 'data/preprocessing/distances'
os.makedirs(output_dir_distances, exist_ok=True)

output_file_distances = os.path.join(output_dir_distances, f"{base_filename}_matrix.csv")

matrix_url = "https://api.openrouteservice.org/v2/matrix/driving-car"

ids = []
locations = []

print("Lecture du fichier de coordonnées et préparation des données...")

with open(input_file_coordinates, 'r', encoding='utf-8') as csv_in:
    reader = csv.DictReader(csv_in)
    for row in reader:
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            ids.append(row['id'])
            locations.append([lon, lat])
        except ValueError:
            print(f"ID {row['id']} ignoré à cause d'un format de coordonnées invalide.")

body = {
    "locations": locations,
    "metrics": ["distance"],
    "units": "m"
}

headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    'Authorization': api_key,
    'Content-Type': 'application/json; charset=utf-8'
}

print("Envoi de la requête à l'API Matrix pour le calcul des distances...")
response = requests.post(matrix_url, json=body, headers=headers)

if response.status_code == 200:
    data = response.json()
    distances = data.get('distances', [])
    
    with open(output_file_distances, 'w', newline='', encoding='utf-8') as csv_out:
        writer = csv.writer(csv_out)
        # En-tête du CSV
        writer.writerow(["origin_id", "destination_id", "distance_km"])
        
        for i, origin_id in enumerate(ids):
            for j, destination_id in enumerate(ids):
                if i != j:
                    distance_m = distances[i][j]
                    distance_km = distance_m / 1000.0
                    writer.writerow([origin_id, destination_id, distance_km])
                    print(f"Distance de ID {origin_id} à ID {destination_id} : {distance_km:.2f} km")
else:
    print("Erreur lors de l'appel à l'API Matrix :", response.status_code, response.text)