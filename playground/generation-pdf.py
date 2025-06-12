from fpdf import FPDF
import pdf_data_builder
from pdf_data_builder import generate_routes_from_file, execute, create_route_map
import os
import unicodedata

def safe_text(text):
    """Supprime les accents et caractères non supportés"""
    if not isinstance(text, str):
        return str(text)
    return unicodedata.normalize('NFKD', text).encode('latin-1', 'ignore').decode('latin-1')

def draw_table(pdf, etapes, title, headers, col_widths, row_line_height):
    if not etapes:
        return
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 7, safe_text(title), ln=True)
    pdf.set_font("Arial", "B", 12)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, safe_text(h), 1, 0, 'C')
    pdf.ln()
    pdf.set_font("Arial", "", 10)

    for etape in etapes:
        dep_id = etape['pharmacie_depart']['pharmacie_depart_id']
        arr_id = etape['pharmacie_arrivee']['pharmacie_arrivee_id']
        dep = etape['pharmacie_depart']['nom_pharmacie'].lower() if dep_id != 0 else "Entrepôt"
        arr = etape['pharmacie_arrivee']['nom_pharmacie'].lower() if arr_id != 0 else "Entrepôt"
        row = [dep, arr, etape['heure_depart'], etape['heure_arrivee']]

        max_lines = 1
        for i, txt in enumerate(row):
            lines = int(pdf.get_string_width(txt) / (col_widths[i] - 2)) + 1
            if lines > max_lines:
                max_lines = lines
        height = max_lines * row_line_height

        x_start = pdf.get_x()
        y_start = pdf.get_y()

        for i, txt in enumerate(row):
            pdf.set_xy(x_start + sum(col_widths[:i]), y_start)
            txt_width = pdf.get_string_width(txt)
            if txt_width < col_widths[i]:
                pdf.cell(col_widths[i], height, safe_text(txt), 1, 0, 'C')
            else:
                pdf.multi_cell(col_widths[i], row_line_height, safe_text(txt), border=1, align='C')
                pdf.set_xy(x_start + sum(col_widths[:i]) + col_widths[i], y_start)
        pdf.ln(height)

    pdf.ln(4)

def draw_map(pdf, temp_map_path): 
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 0, safe_text("CARTE GÉNÉRALE DES TOURNÉES"), ln=True, align='C')
    pdf.ln(30)

    page_width = pdf.w - 50 
    page_height = pdf.h - 80

    x_centered = (pdf.w - page_width) / 2 
    pdf.image(temp_map_path, x=x_centered, y=pdf.get_y(), w=page_width, h=page_height - 10)
    pdf.ln(page_height - 10)


def main():
    #configuration
    file_matrix_csv = "data/matrix_85.csv" 
    coords_csv_path = "data/coordinates_85.csv" 
    output_file = "output.txt"
    
  
    #execution algo genetique
    execute(file_matrix_csv)
    obj, totaux = generate_routes_from_file(file_matrix_csv, coords_csv_path, output_file)
    
    if "error" in obj:
        print("Erreur dans la génération des routes:", obj)
        return
    
    #creation pdf
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    #creation de la carte
    temp_map_path = "temp_route_map.png"
    map_created = create_route_map(obj, coords_csv_path, temp_map_path)
    
    if map_created and os.path.exists(temp_map_path):
        draw_map(pdf, temp_map_path)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, safe_text(f"Distance totale (toutes tournées) : {totaux.get('distance_totale', 0):.2f} km"), ln=True, align='L')
        pdf.cell(0, 10, safe_text(f"Durée totale estimée : {totaux.get('temps_total', 0):.2f} minutes"), ln=True, align='L')

    for camion, infos in obj.items():
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, safe_text(camion.upper()), ln=True, align='C')
        pdf.ln(10)

        headers = ['Départ', 'Arrivée', 'H. Départ', 'H. Arrivée']
        col_widths = [50, 50, 40, 40]
        row_line_height = 5

        #tableau matin et aprem
        etapes_matin = []
        etapes_aprem = []

        for etape_key in sorted(infos['trajet'].keys(), key=lambda x: int(x.replace('etape', ''))):
            etape = infos['trajet'][etape_key]
            h_dep = etape['heure_depart']
            h_dep_h, h_dep_m = map(int, h_dep.split(':'))
            minutes = h_dep_h * 60 + h_dep_m

            if minutes < 15 * 60:
                etapes_matin.append(etape)
            elif minutes >= 15 * 60:
                etapes_aprem.append(etape)

        

        draw_table(pdf, etapes_matin, "Matin", headers, col_widths, row_line_height)
        draw_table(pdf, etapes_aprem, "Après-midi", headers, col_widths, row_line_height)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, safe_text(f"Distance totale : {infos.get('distance_total_km', 0):.2f} km"), ln=True)
        pdf.cell(0, 10, safe_text(f"Durée totale : {infos.get('duree_totale_min', 0):.2f} minutes"), ln=True)
        pdf.cell(0, 10, safe_text(f"Carburant estimé : {infos.get('total_carburant_litre', 0):.2f} litres"), ln=True)
        pdf.cell(0, 10, safe_text(f"Coût carburant : {infos.get('cout_carburant_eur', 0):.2f} EUR"), ln=True)

    pdf.output("recapitulatif_globale.pdf")

    if os.path.exists(temp_map_path):
        os.remove(temp_map_path)

    print("Le PDF récapitulatif avec carte a été généré avec succès !")
    print("Fichier de sortie: recapitulatif_globale.pdf")

if __name__ == "__main__":
    main()
