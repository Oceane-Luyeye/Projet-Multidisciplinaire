from fpdf import FPDF
import pdf_data_builder
from pdf_data_builder import generate_routes_from_file, execute, create_route_map
import os
import unicodedata

def safe_text(text):
    """Supprime les accents et caractères non supportés """
    if not isinstance(text, str):
        return str(text)
    return unicodedata.normalize('NFKD', text).encode('latin-1', 'ignore').decode('latin-1')

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
    
    if map_created and os.path.exists(temp_map_path):
        pdf.add_page()
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 0, safe_text("CARTE GÉNÉRALE DES TOURNÉES"), ln=True, align='C')
        pdf.ln(30)

        page_width = pdf.w - 20
        page_height = pdf.h - 60
        pdf.image(temp_map_path, w=page_width, h=page_height - 10)

    for camion, infos in obj.items():
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt=safe_text(f"{camion.upper()}"), ln=True, align='C')
        pdf.ln(10)
        
        headers = ['Départ', 'Arrivée', 'H. Départ', 'H. Arrivée']
        col_widths = [50, 50, 40, 40]
        row_line_height = 5
        
        # en-tête
        pdf.set_font("Arial", "B", 12)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, safe_text(header), 1, 0, 'C')
        pdf.ln()

        pdf.set_font("Arial", "", 11)

        # etapes
        for etape_key in sorted(infos['trajet'].keys(), key=lambda x: int(x.replace('etape', ''))):
            etape = infos['trajet'][etape_key]

            dep_id = etape['pharmacie_depart']['pharmacie_depart_id']
            arr_id = etape['pharmacie_arrivee']['pharmacie_arrivee_id']
            dep = etape['pharmacie_depart']['nom_pharmacie'].lower() if dep_id != 0 else "Entrepôt"
            arr = etape['pharmacie_arrivee']['nom_pharmacie'].lower() if arr_id != 0 else "Entrepôt"
            h_dep = etape['heure_depart']
            h_arr = etape['heure_arrivee']

            row = [dep, arr, h_dep, h_arr]

            line_heights = []
            for i, text in enumerate(row):
                text_width = pdf.get_string_width(text)
                lines = (text_width // (col_widths[i] - 2)) + 1
                line_heights.append(lines)
            
            max_lines = max(line_heights)
            total_height = max_lines * row_line_height

            x_start = pdf.get_x()
            y_start = pdf.get_y()

            for i, text in enumerate(row):
                pdf.set_xy(x_start + sum(col_widths[:i]), y_start)
                
                text_width = pdf.get_string_width(safe_text(text))
                if text_width < col_widths[i]:
                    pdf.cell(col_widths[i], total_height, safe_text(text), border=1, align='C')
                    pdf.set_y(y_start+total_height)

                else:
                    pdf.multi_cell(col_widths[i], row_line_height, safe_text(text), border=1, align='C')
                    pdf.set_y(y_start+row_line_height)

        pdf.ln(10)

        pdf.set_font("Arial", "B", 12)
        distance = infos.get('distance_total_km', 0)
        duree = infos.get('duree_totale_min', 0)
        carburant = infos.get('total_carburant_litre', 0)
        cout = infos.get('cout_carburant_eur', 0)

        pdf.cell(0, 10, safe_text(f"Distance totale : {distance:.2f} km"), ln=True)
        pdf.cell(0, 10, safe_text(f"Durée totale : {duree:.2f} minutes"), ln=True)
        pdf.cell(0, 10, safe_text(f"Carburant estimé : {carburant:.2f} litres"), ln=True)
        pdf.cell(0, 10, safe_text(f"Coût carburant : {cout:.2f} EUR"), ln=True)

    pdf.output("recapitulatif_globale.pdf")

    if os.path.exists(temp_map_path):
        os.remove(temp_map_path)

    print("Le PDF récapitulatif avec carte a été généré avec succès !")
    print("Fichier de sortie: recapitulatif_globale.pdf")

if __name__ == "__main__":
    main()
