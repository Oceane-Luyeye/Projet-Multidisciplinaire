from fpdf import FPDF

import subprocess
import requests
import time

process = subprocess.Popen(["python3", "app.py"])

time.sleep(2)

r = requests.get("http://127.0.0.1:5000/generate")

print(r)

process.terminate()

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