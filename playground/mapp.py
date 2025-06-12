# Script pour dessiner les coordinnées dans un fichier html pour voir si on est hors sujet

import pandas as pd
import folium

# Path to your CSV with coordinates
csv_file = '/Users/ayoub/Documents/GitHub/Projet-Multidisciplinaire/RENDU/data/output/csv/coordinates_85.csv'

# Load the CSV file
df = pd.read_csv(csv_file)

# Check if necessary columns exist
required_cols = {'latitude', 'longitude', 'name'}
if not required_cols.issubset(df.columns):
    raise ValueError(f"CSV must contain columns: {required_cols}")

# Create the base map centered around the average coordinates
center_lat = df['latitude'].mean()
center_lon = df['longitude'].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

# Add points to the map
for _, row in df.iterrows():
    popup_text = f"{row['name']}<br>{row['city']} {row['postal_code']}"
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup_text,
        icon=folium.Icon(color='blue', icon='plus-sign')
    ).add_to(m)

# Save the map to an HTML file
map_output_path = '/Users/ayoub/Documents/GitHub/Projet-Multidisciplinaire/RENDU/data/output/maps/livraison85_map.html'
m.save(map_output_path)

print(f"Map saved to: {map_output_path}")