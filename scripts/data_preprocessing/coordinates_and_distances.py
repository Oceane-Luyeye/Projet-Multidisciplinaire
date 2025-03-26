import csv
import os
import time
import requests
import openrouteservice

# Clé API OpenRouteService
api_key = "5b3ce3597851110001cf62487e2739ab43d8469aa4faf8da7acc850d"

# Chemin du fichier CSV d'entrée
input_file = 'data/base_csv/livraison10.csv'

# Détermination du nom de base du fichier de bdd (exemple: "livraison10")
base_filename = os.path.splitext(os.path.basename(input_file))[0]

# Répertoires de sortie pour les fichiers de coordonnées et de distances
output_dir_coordinates = 'data/preprocessing/coordinates'
output_dir_distances = 'data/preprocessing/distances'

# Création des dossiers de sortie s'ils n'existent pas
os.makedirs(output_dir_coordinates, exist_ok=True)
os.makedirs(output_dir_distances, exist_ok=True)

# Chemins complets des fichiers de sortie
output_file_coordinates = os.path.join(output_dir_coordinates, f"{base_filename}_coordinates.csv")
output_file_distances = os.path.join(output_dir_distances, f"{base_filename}_matrix.csv")

# Initialisation du client OpenRouteService
client = openrouteservice.Client(key=api_key)

# Liste pour stocker les adresses non trouvées (pour debug)
not_found = []

##### STEP 1 : Extraction des coordonnées depuis le CSV d'entrée #####
print("Extraction des coordonnées...")
with open(input_file, 'r', encoding='utf-8') as csv_in, \
     open(output_file_coordinates, 'w', newline='', encoding='utf-8') as csv_out:
    
    reader = csv.reader(csv_in)
    writer = csv.writer(csv_out)
    
    # Écriture de l'en-tête du fichier de coordonnées
    writer.writerow(["id", "latitude", "longitude"])
    
    header = next(reader)
    
    for row in reader:
        # On attend que la ligne contienne : id, nom, adresse, code postal, ville
        record_id = row[0]
        # Concaténation des autres colonnes pour former l'adresse complète
        address_str = ", ".join(row[1:]).strip()
        
        try:
            response = client.pelias_search(text=address_str)
            
            if response.get('features'):
                # coordonnées sous la forme [longitude, latitude]
                feature = response['features'][0]
                longitude, latitude = feature['geometry']['coordinates']
                writer.writerow([record_id, latitude, longitude])
                print(f"ID {record_id}: Coordonnées trouvées -> latitude: {latitude}, longitude: {longitude}")
            else:
                not_found.append((record_id, address_str))
                print(f"ID {record_id}: Adresse non trouvée.")
        except Exception as e:
            not_found.append((record_id, address_str))
            print(f"ID {record_id}: Erreur - {e}")
        
        # Pause pour éviter les limitations de taux
        time.sleep(1)

# Affichage des adresses non trouvées
if not_found:
    print("\nLes adresses suivantes n'ont pas été trouvées :")
    for record_id, address in not_found:
        print(f"ID {record_id}: {address}")
else:
    print("\nToutes les adresses ont été géolocalisées avec succès.")


##### STEP 2: Calcul de la matrice de distances à partir des coordonnées obtenues #####

print("\nCalcul de la matrice de distances...")

# Initialisation des listes pour stocker les identifiants et les coordonnées
ids = []
locations = []

# Lecture du fichier de coordonnées généré précédemment
with open(output_file_coordinates, 'r', encoding='utf-8') as csv_in:
    reader = csv.DictReader(csv_in)
    for row in reader:
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            ids.append(row['id'])
            # OpenRouteService coordinates = [longitude, latitude]
            locations.append([lon, lat])
        except ValueError:
            print(f"ID {row['id']} ignoré à cause d'un format de coordonnées invalide.")

# Préparation de la requête JSON pour l'API Matrix
body = {
    "locations": locations,
    "metrics": ["distance"],
    "units": "m"        # en mètres
}

headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    'Authorization': api_key,
    'Content-Type': 'application/json; charset=utf-8'
}

response = requests.post("https://api.openrouteservice.org/v2/matrix/driving-car", json=body, headers=headers)

if response.status_code == 200:
    data = response.json()
    # La matrice retournée : distances[i][j] est la distance en mètres du point i au point j.
    distances = data.get('distances', [])
    
    # Écriture de la matrice des distances dans un fichier CSV de sortie
    with open(output_file_distances, 'w', newline='', encoding='utf-8') as csv_out:
        writer = csv.writer(csv_out)
        # En-tête du CSV : identifiant origine, identifiant destination, distance en km
        writer.writerow(["origin_id", "destination_id", "distance_km"])
        
        # Boucle sur chaque paire de points (on ignore les distances d'un point à lui-même)
        for i, origin_id in enumerate(ids):
            for j, destination_id in enumerate(ids):
                if i != j:
                    distance_m = distances[i][j]
                    distance_km = distance_m / 1000.0  # conversion en kilomètres
                    writer.writerow([origin_id, destination_id, distance_km])
                    print(f"Distance de ID {origin_id} à ID {destination_id} : {distance_km:.2f} km")
else:
    print("Erreur lors de l'appel à l'API Matrix:", response.status_code, response.text)