import csv
import os
import time
import openrouteservice

api_key = "5b3ce3597851110001cf62487e2739ab43d8469aa4faf8da7acc850d"

input_file = 'data/base_csv/livraison10.csv'

base_filename = os.path.splitext(os.path.basename(input_file))[0]

output_dir_coordinates = 'data/preprocessing/coordinates'
os.makedirs(output_dir_coordinates, exist_ok=True)

output_file_coordinates = os.path.join(output_dir_coordinates, f"{base_filename}_coordinates.csv")

client = openrouteservice.Client(key=api_key)

# Liste pour stocker les adresses non trouvées (pour suivi)
not_found = []

print("Début de la géolocalisation des adresses...")

with open(input_file, 'r', encoding='utf-8') as csv_in, \
     open(output_file_coordinates, 'w', newline='', encoding='utf-8') as csv_out:
    
    reader = csv.reader(csv_in)
    writer = csv.writer(csv_out)
    
    writer.writerow(["id", "latitude", "longitude"])
    
    header = next(reader)
    
    for row in reader:
        record_id = row[0]
        address_str = ", ".join(row[1:]).strip()
        
        try:
            response = client.pelias_search(text=address_str)
            
            if response.get('features'):
                feature = response['features'][0]
                longitude, latitude = feature['geometry']['coordinates']
                writer.writerow([record_id, latitude, longitude])
                print(f"ID {record_id} : Coordonnées trouvées -> latitude : {latitude}, longitude : {longitude}")
            else:
                not_found.append((record_id, address_str))
                print(f"ID {record_id} : Adresse non trouvée.")
        except Exception as e:
            not_found.append((record_id, address_str))
            print(f"ID {record_id} : Erreur - {e}")
        
        time.sleep(1)

if not_found:
    print("\nLes adresses suivantes n'ont pas été trouvées :")
    for record_id, address in not_found:
        print(f"ID {record_id} : {address}")
else:
    print("\nToutes les adresses ont été géolocalisées avec succès.")