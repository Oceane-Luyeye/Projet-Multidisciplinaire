
from fpdf import FPDF
import json
import subprocess
import csv
from datetime import datetime, timedelta
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

def generate_pdf_for_all_trucks():
    """Génère un PDF récapitulatif pour tous les camions"""
    # Récupération des données
    res = generate_routes()
    
    # Vérification des erreurs
    if "status" in res and res["status"] == "error":
        print(f"Erreur lors de la génération des routes : {res['message']}")
        return
    
    # Création du PDF principal avec encodage UTF-8
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16, style="B")
    pdf.cell(200, 10, txt="Recapitulatif general des livraisons", ln=True, align='C')
    pdf.ln(10)
    
    # Statistiques globales
    total_distance = sum([camion['distance_total_km'] for camion in res.values()])
    total_cout = sum([camion['cout_carburant_eur'] for camion in res.values()])
    total_carburant = sum([camion['total_carburant_litre'] for camion in res.values()])
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 8, txt=f"Nombre total de camions : {len(res)}", ln=True)
    pdf.cell(200, 8, txt=f"Distance totale parcourue : {round(total_distance, 2)} km", ln=True)
    pdf.cell(200, 8, txt=f"Carburant total estime : {round(total_carburant, 2)} litres", ln=True)
    pdf.cell(200, 8, txt=f"Cout total carburant : {round(total_cout, 2)} EUR", ln=True)
    pdf.ln(10)
    
    # Génération d'un PDF détaillé pour chaque camion
    for camion_id, camion_data in res.items():
        generate_pdf_for_single_truck(camion_id, camion_data)
    
    # Sauvegarde du PDF récapitulatif général
    pdf.output("recapitulatif_general_livraisons.pdf")
    print("Le PDF récapitulatif général a été créé avec succès !")

def generate_pdf_for_single_truck(camion_id, camion_data):
    """Génère un PDF détaillé pour un camion spécifique"""
    # Création d'une instance de FPDF
    pdf = FPDF()
    pdf.add_page()
    
    # Définition de la police pour le titre
    pdf.set_font("Arial", size=20, style="B")
    
    # Ajout du titre avec le numéro du camion
    numero_camion = camion_id.replace('camion', '')
    pdf.cell(200, 10, txt=f"Recapitulatif des distances parcourues par le camion n° {numero_camion}", ln=True, align='C')
    pdf.ln(10)
    
    # Paramètres du tableau
    col_width = 45
    row_height = 10
    
    # Définition des entêtes
    headers = ['Depart', 'Arrivee', 'Heure depart', 'Heure arrivee']
    
    # Couleurs pour l'entête du tableau
    pdf.set_fill_color(200, 220, 255)  # Bleu clair
    pdf.set_text_color(0, 0, 0)  # Texte noir
    pdf.set_draw_color(0, 0, 0)  # Lignes noires
    pdf.set_line_width(0.3)  # Épaisseur de ligne
    pdf.set_font('Arial', 'B', 12)  # Gras pour les entêtes
    
    # Ajout des entêtes de colonnes
    for header in headers:
        pdf.cell(col_width, row_height, header, 1, 0, 'C', 1)
    pdf.ln(row_height)
    
    # Restauration des couleurs et de la police pour le contenu
    pdf.set_fill_color(255, 255, 255)  # Blanc
    pdf.set_font('Arial', '', 10)  # Police normale
    
    # Extraction et ajout des données du trajet
    trajet = camion_data['trajet']
    for etape_key in sorted(trajet.keys(), key=lambda x: int(x.replace('etape', ''))):
        etape = trajet[etape_key]
        row_data = [
            f"Pharmacie {etape['pharmacie_depart_id']}",
            f"Pharmacie {etape['pharmacie_arrivee_id']}",
            etape['heure_depart'],
            etape['heure_arrivee']
        ]
        
        for item in row_data:
            pdf.cell(col_width, row_height, str(item), 1, 0, 'C')
        pdf.ln(row_height)
    
    # Ajout d'un espace après le tableau
    pdf.ln(10)
    
    # Informations récapitulatives
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, txt=f"Distance totale : {camion_data['distance_total_km']} km", ln=True)
    pdf.cell(200, 10, txt=f"Duree totale : {camion_data['duree_totale_min']} minutes", ln=True)
    pdf.cell(200, 10, txt=f"Carburant estime : {camion_data['total_carburant_litre']} litres", ln=True)
    pdf.cell(200, 10, txt=f"Cout carburant : {camion_data['cout_carburant_eur']} EUR", ln=True)
    
    # Sauvegarde du PDF pour ce camion
    filename = f"recapitulatif_livraison_{camion_id}.pdf"
    pdf.output(filename)
    print(f"Le PDF pour le {camion_id} a été créé avec succès : {filename}")

# Fonction principale pour générer tous les PDFs
def main():
    """Fonction principale qui génère les PDFs"""
    try:
        # Génération du PDF récapitulatif général et des PDFs individuels
        generate_pdf_for_all_trucks()
        
        # Si vous voulez aussi voir les données dans la console
        res = generate_routes()
        if "status" not in res or res["status"] != "error":
            print("\nDonnées générées :")
            pprint.pprint(res)
        
    except Exception as e:
        print(f"Erreur lors de la génération des PDFs : {e}")

# Exécution du programme
if __name__ == "__main__":
    main()