import sys
import os
import time
import pandas as pd
import openrouteservice

# Vérification des arguments
if len(sys.argv) < 2:
    print(f"Usage: python {os.path.basename(sys.argv[0])} <input_csv_file>")
    sys.exit(1)
input_file = sys.argv[1]

all_csv_path = 'data/database/all.csv'

# Clé API ORS
api_key = "5b3ce3597851110001cf62487e2739ab43d8469aa4faf8da7acc850d"
client = openrouteservice.Client(key=api_key)

# Chargement de la base all.csv
all_df = pd.read_csv(all_csv_path, dtype={'name': str, 'street': str, 'postal_code': str, 'city': str, 'latitude': float, 'longitude': float})

# Chargement du fichier d'input (4 ou 5 colonnes)
temp_df = pd.read_csv(input_file, header=None, dtype=str)
if temp_df.shape[1] == 4:
    temp_df.columns = ['name', 'street', 'postal_code', 'city']
    temp_df.insert(0, 'id', range(1, len(temp_df) + 1))
elif temp_df.shape[1] == 5:
    temp_df.columns = ['id', 'name', 'street', 'postal_code', 'city']
else:
    raise ValueError(f"Le fichier {input_file} doit contenir 4 ou 5 colonnes")
df_in = temp_df[['id', 'name', 'street', 'postal_code', 'city']].copy()

# Liste pour nouvelles entrées et suivi des non trouvées
new_entries = []
not_found = []

print("Début de la géolocalisation et mise à jour de all.csv...")
for _, row in df_in.iterrows():
    record_id = row['id']
    name = row['name'].strip()
    street = row['street'].strip()
    postal = row['postal_code'].strip()
    city = row['city'].strip()
    address_str = f"{name}, {street}, {postal}, {city}"

    try:
        resp = client.pelias_search(text=address_str)
        feats = resp.get('features', [])
        if feats:
            lon, lat = feats[0]['geometry']['coordinates']
            print(f"ID {record_id}: Coordonnées -> lat {lat}, lon {lon}")

            exists = ((all_df['name'] == name) &
                      (all_df['street'] == street) &
                      (all_df['postal_code'] == postal) &
                      (all_df['city'] == city)).any()
            if not exists:
                new_entries.append({
                    'name': name,
                    'street': street,
                    'postal_code': postal,
                    'city': city,
                    'latitude': lat,
                    'longitude': lon
                })
        else:
            not_found.append((record_id, address_str))
            print(f"ID {record_id}: Adresse non trouvée.")
    except Exception as e:
        not_found.append((record_id, address_str))
        print(f"ID {record_id}: Erreur - {e}")
    time.sleep(1)

# Mise à jour de all.csv
if new_entries:
    new_df = pd.DataFrame(new_entries)
    all_df = pd.concat([all_df, new_df], ignore_index=True)
    all_df.to_csv(all_csv_path, index=False)
    print(f"\n{len(new_entries)} nouvelles adresses ajoutées à {all_csv_path}.")
else:
    print("\nAucune nouvelle adresse à ajouter dans all.csv.")

# Rapport des adresses non géolocalisées
if not_found:
    print("\nAdresses non trouvées :")
    for rid, addr in not_found:
        print(f"ID {rid}: {addr}")
else:
    print("\nToutes les adresses ont été géolocalisées ou déjà existantes dans all.csv.")
