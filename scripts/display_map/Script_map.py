import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.backends.backend_pdf import PdfPages
import os


# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COORDS_CSV = COORDS_CSV = os.path.join(os.path.dirname(__file__), "../../data/preprocessing/coordinates/livraison30_coordinates.csv")
TOURNEES_TXT = os.path.join(os.path.dirname(__file__), "../../data/output/best_routes.txt")

#TOURNEES_TXT = ".../data/output/best_routes.txt"
PDF_OUTPUT = os.path.join(os.path.dirname(__file__),"../../scripts/pdf/carte_tournees.pdf")

#Charger les coordonnées GPS ===
df_coords = pd.read_csv(COORDS_CSV)
df_coords['index'] = df_coords.index  # Ajoute l'indice si nécessaire

#Lire les tournées depuis le fichier texte ===
def lire_tournees(fichier_txt):
    tournees = []
    with open(fichier_txt, "r") as f:
        for ligne in f:
            if ":" in ligne:
                _, chemin = ligne.split(":")
                indices = list(map(int, chemin.strip().split("->")))
                tournees.append(indices)
    return tournees

tournees = lire_tournees(TOURNEES_TXT)

#Tracer les itinéraires sur une carte ===
fig, ax = plt.subplots(figsize=(10, 10))
custom_colors = [
    "red", "green", "blue", "orange", "purple", "cyan",       
    "#FF00FF", "#00FFFF", "#FFD700", "#8B0000", "#7FFF00", 
    "#FF69B4", "#00BFFF", "#DAA520", "#556B2F", "#A52A2A",
    "#800080", "#2E8B57", "#B22222", "#5F9EA0"
]

#colors = custom_colors[i % len(custom_colors)]
#colors = custom_colors[:len(tournees)]  # Limiter les couleurs au nombre de tournées


all_points = []

for i, route in enumerate(tournees):
    sous_df = df_coords.loc[route]
    gdf = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(sous_df["longitude"], sous_df["latitude"]),
        crs="EPSG:4326"
    ).to_crs(epsg=3857)

    # Tracer les lignes et points
    ax.plot(gdf.geometry.x, gdf.geometry.y, marker='o', linestyle='-',
           color = custom_colors[i % len(custom_colors)]
, label=f"Camion {i+1}")
    for x, y, idx in zip(gdf.geometry.x, gdf.geometry.y, route):
        ax.text(x, y, str(idx), fontsize=7)

    all_points.extend(gdf.geometry)

#Zoom automatique sur la zone couverte par les points ===
all_x = [pt.x for pt in all_points]
all_y = [pt.y for pt in all_points]
margin_x = (max(all_x) - min(all_x)) * 0.05
margin_y = (max(all_y) - min(all_y)) * 0.05
ax.set_xlim(min(all_x) - margin_x, max(all_x) + margin_x)
ax.set_ylim(min(all_y) - margin_y, max(all_y) + margin_y)

#Ajouter fond de carte OpenStreetMap ===
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
ax.set_aspect('equal')
ax.set_title("Tournées des camions - Carte dynamique")
ax.axis("off")
ax.legend()

#Exporter en PDF ===
with PdfPages(PDF_OUTPUT) as pdf:
    pdf.savefig(fig)
    plt.close(fig)

print(f"✅ Carte générée avec succès : {PDF_OUTPUT}")
