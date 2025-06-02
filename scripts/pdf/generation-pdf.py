from datetime import datetime, timedelta
import json
import csv
import subprocess
from fpdf import FPDF
import pprint

def generate_routes():
    try:
        compile = subprocess.run(["gcc", "test.c", "-o", "test"], capture_output=True, text=True)
        if compile.returncode != 0:
            return {"status": "error", "message": "Erreur compilation", "details": compile.stderr}

        result = subprocess.run(["./test"], capture_output=True, text=True)
        if result.returncode != 0:
            return {"status": "error", "message": "Erreur exécution", "details": result.stderr}

        data = json.loads(result.stdout)
        return createJsonObject(data)

    except Exception as e:
        return {"status": "error", "message": f"Erreur serveur : {e}"}

def getMatrix(csv_file):
    max_id = 0
    data = []

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            o = int(row['origin_id'])
            d = int(row['destination_id'])
            dist = float(row['distance_km'])
            dur = float(row['duration_min'])
            data.append((o, d, dist, dur))
            max_id = max(max_id, o, d)

    dist_matrice = [[0]*(max_id+1) for _ in range(max_id+1)]
    dur_matrice = [[0]*(max_id+1) for _ in range(max_id+1)]

    for o, d, dist, dur in data:
        dist_matrice[o][d] = dist
        dur_matrice[o][d] = dur

    return dist_matrice, dur_matrice

def createJsonObject(tab):
    in_matin = 1
    in_aprem = 0

    matrix_dist, matrix_time = getMatrix("../../data/depot_with_id/30/livraison30_matrix.csv")

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

            if (in_matin and current_time + timedelta(minutes=duree) > fin_matin) or duree_tournee + duree > 180:
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

res = generate_routes()
pprint.pprint(res)

# Création d'une instance de FPDF
pdf = FPDF()

# Ajout d'une page
pdf.add_page()

# Définition de la police
pdf.set_font("Arial", size=20, style="B")

# Ajout d'un titre
pdf.cell(200, 10, txt="Récapitulatif des distances parcourrue par le camion n° ", ln=True, align='C')

pdf.ln(10)

#Paramètre du tableau
col_width = 50
row_height = 10  
line_height = 7  

#Definition des entêtes 

headers = ['Départ entrepôt Cerp', 'Parcours camionnette', 'Arrivée', 'Départ']

# Couleurs pour l'entête du tableau
pdf.set_fill_color(200, 220, 255)  # Bleu clair
pdf.set_text_color(0, 0, 0)  # Texte noir
pdf.set_draw_color(0, 0, 0)  # Lignes noires
pdf.set_line_width(0.3)  # Épaisseur de ligne
pdf.set_font('Arial', 'B', 12)  # Gras pour les entêtes

#Ajout des entêtes de colonnes 

for i, header in enumerate(headers):
    pdf.cell(col_width, row_height, header, 1, 0, 'C', 1)
pdf.ln(row_height)

# Restauration des couleurs et de la police pour le contenu
pdf.set_fill_color(255, 255, 255)  # Blanc

# Exemple de données pour remplir le tableau que je vais changer avec les données extraites de l'algo génétique 

data = [
    ['8:00', 'Route A', '9:30', '9:45'],
    ['10:30', 'Route B', '12:00', '12:15'],
    ['14:00', 'Route C', '15:30', '15:45']
]

# Ajout des données dans le tableau
for row in data:
    for item in row:
        pdf.cell(col_width, row_height, item, 1, 0, 'C')
    pdf.ln(row_height)

# Ajout d'un espace après le tableau
pdf.ln(10)

# Message supplémentaire
pdf.cell(200, 10, txt="Distance totale : ", ln=True)
pdf.cell(200, 10, txt="Carburant estimé : ", ln=True)
pdf.cell(200, 10, txt="Coût carburant : ", ln=True)

# Sauvegarde du PDF
pdf.output("recapitulatif_livraison.pdf")

print("Le PDF du planning a été créé avec succès !")