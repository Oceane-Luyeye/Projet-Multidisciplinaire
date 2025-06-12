from fpdf import FPDF
import pdf_data_builder
from pdf_data_builder import generate_routes_from_file, execute, create_route_map
import os

def main():
    # Configuration
    file_matrix_csv = "data/matrix_85.csv" 
    coords_csv_path = "data/coordinates_85.csv" 
    output_file = "output.txt"
  
    
    # Exécute l'algo
    print("Exécution de l'algorithme génétique...")
    execute(file_matrix_csv)
    obj = generate_routes_from_file(file_matrix_csv, coords_csv_path, output_file)
    
    if "error" in obj:
        print("Erreur dans la génération des routes:", obj)
        return
    
    # Créer la carte
    print("Génération de la carte...")
    temp_map_path = "temp_route_map.png"
    map_created = create_route_map(obj, coords_csv_path, temp_map_path)
    
    # Création du PDF
    print("Création du PDF...")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Page de carte générale (si la carte a été créée)
    if map_created and os.path.exists(temp_map_path):
        pdf.add_page()
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 0, "CARTE GÉNÉRALE DES TOURNÉES", ln=True, align='C')
        pdf.ln(30)
        
        # Ajouter l'image de la carte
        page_width = pdf.w - 20  # Largeur de page moins marges
        page_height = pdf.h - 60  # Hauteur de page moins marges et titre
        
        # Insérer l'image (FPDF ajuste automatiquement les proportions)
        pdf.image(temp_map_path, w=page_width, h=page_height-10)
    
    for camion, infos in obj.items():
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt=f"{camion.upper()}", ln=True, align='C')
        pdf.ln(10)
        
        headers = ['Départ', 'Arrivée', 'H. Départ', 'H. Arrivée', 'Observations']
        col_widths = [40, 40, 30, 30, 50]
        row_height = 10
        
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(52, 152, 219)   

        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], row_height, header, 1, 0, 'C')
        pdf.ln(row_height)
        
        pdf.set_font("Arial", "", 11)
        for etape_key in sorted(infos['trajet'].keys(), key=lambda x: int(x.replace('etape', ''))):
            etape = infos['trajet'][etape_key]
            # drill into nested dicts
            dep_id = etape['pharmacie_depart']['pharmacie_depart_id']
            arr_id = etape['pharmacie_arrivee']['pharmacie_arrivee_id']

            dep = etape['pharmacie_depart']['nom_pharmacie'] if dep_id != 0 else "Entrepôt"
            arr = etape['pharmacie_arrivee']['nom_pharmacie'] if arr_id != 0 else "Entrepôt"
            h_dep = etape['heure_depart']
            h_arr = etape['heure_arrivee']

            if dep_id == 0:
                obs = "Départ entrepôt"
            elif arr_id == 0:
                obs = "Retour entrepôt"
            else:
                obs = "Livraison"
            
            row = [dep, arr, h_dep, h_arr, obs]
            for i, item in enumerate(row):
                pdf.cell(col_widths[i], row_height, str(item), 1, 0, 'C')
            pdf.ln(row_height)
        
        pdf.ln(10)
       
        pdf.set_font("Arial", "B", 12)
        distance = infos.get('distance_total_km', 0)
        duree = infos.get('duree_totale_min', 0)
        carburant = infos.get('total_carburant_litre', 0)
        cout = infos.get('cout_carburant_eur', 0)
        
        pdf.cell(0, 10, f"Distance totale : {distance:.2f} km", ln=True)
        pdf.cell(0, 10, f"Durée totale : {duree:.2f} minutes", ln=True)
        pdf.cell(0, 10, f"Carburant estimé : {carburant:.2f} litres", ln=True)
        pdf.cell(0, 10, f"Coût carburant : {cout:.2f} EUR", ln=True)
    
    pdf.output("recapitulatif_globale.pdf")
    
    if os.path.exists(temp_map_path):
        os.remove(temp_map_path)
    
    print(" Le PDF récapitulatif avec carte a été généré avec succès !")
    print(" Fichier de sortie: recapitulatif_global_avec_carte.pdf")

if __name__ == "__main__":
    main()
