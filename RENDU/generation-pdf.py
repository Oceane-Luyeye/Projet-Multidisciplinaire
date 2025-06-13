import argparse
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

import pdf_data_builder
from pdf_data_builder import (
    execute,
    create_route_map,
    parse_routes_from_text,
    fusionne_trajet,
    regroup_and_split_by_truck,
    createJsonObject,
)

def draw_table(pdf, etapes, title, headers, col_widths, row_line_height):
    if not etapes:
        return

    # Title
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 7, title)
    pdf.ln(7)

    # Header row
    pdf.set_font("DejaVu", "B", 12)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, border=1, align='C')
    pdf.ln(7)

    # Data rows
    pdf.set_font("DejaVu", "", 10)
    for etape in etapes:
        dep_id = etape['pharmacie_depart']['pharmacie_depart_id']
        arr_id = etape['pharmacie_arrivee']['pharmacie_arrivee_id']
        dep = etape['pharmacie_depart']['nom_pharmacie'].lower() if dep_id != 0 else "Entrepôt"
        arr = etape['pharmacie_arrivee']['nom_pharmacie'].lower() if arr_id != 0 else "Entrepôt"
        row = [dep, arr, etape['heure_depart'], etape['heure_arrivee']]

        # figure out cell height
        max_lines = 1
        for i, txt in enumerate(row):
            # approximate lines by width
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
                pdf.cell(col_widths[i], height, txt, border=1, align='L' if i < 2 else 'C')
            else:
                pdf.multi_cell(col_widths[i], row_line_height, txt, border=1, align='L' if i < 2 else 'C')
                # after a multi_cell, cursor is at start of next line—reset to our row’s y
                pdf.set_xy(x_start + sum(col_widths[:i]) + col_widths[i], y_start)

        pdf.ln(height)

    pdf.ln(4)


def add_trucks_pdf_pages(pdf, obj):
    headers = ['Départ', 'Arrivée', 'H. Départ', 'H. Arrivée']
    col_widths = [50, 50, 40, 40]
    row_line_height = 5

    for camion, infos in obj.items():
        pdf.add_page()
        pdf.set_font("DejaVu", "B", 16)
        pdf.cell(0, 10, camion.upper(), align='C')
        pdf.ln(10)

        etapes_matin, etapes_aprem = [], []
        for etape_key in sorted(infos['trajet'].keys(),
                                key=lambda x: int(x.replace('etape', ''))):
            etape = infos['trajet'][etape_key]
            h_dep_h, h_dep_m = map(int, etape['heure_depart'].split(':'))
            if h_dep_h * 60 + h_dep_m < 15 * 60:
                etapes_matin.append(etape)
            else:
                etapes_aprem.append(etape)

        draw_table(pdf, etapes_matin, "Matin", headers, col_widths, row_line_height)
        draw_table(pdf, etapes_aprem, "Après-midi", headers, col_widths, row_line_height)

        pdf.set_font("DejaVu", "B", 12)
        # two cells side by side, then move to next line
        pdf.cell(100, 7, f"Distance totale : {infos.get('distance_total_km', 0):.2f} km")
        pdf.cell(0, 7, f"Durée totale : {infos.get('duree_totale_min', 0):.2f} min")
        pdf.ln(7)
        pdf.cell(100, 7, f"Carburant estimé : {infos.get('total_carburant_litre', 0):.2f} L")
        pdf.cell(0, 7, f"Coût carburant : {infos.get('cout_carburant_eur', 0):.2f} €")
        pdf.ln(10)


def draw_map(pdf, temp_map_path):
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 20)
    pdf.cell(0, 0, "CARTE GÉNÉRALE DES TOURNÉES", align='C')
    pdf.ln(30)

    page_w = pdf.w - 50
    page_h = pdf.h - 80
    x_center = (pdf.w - page_w) / 2

    pdf.image(temp_map_path, x=x_center, y=pdf.get_y(),
              w=page_w, h=page_h - 10)
    pdf.ln(page_h - 10)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a PDF report from a precomputed distance/time matrix and coordinates."
    )
    parser.add_argument('--matrix', required=True,
                        help="Path to the matrix CSV")
    parser.add_argument('--coords', required=True,
                        help="Path to the coordinates CSV")
    args = parser.parse_args()

    file_matrix_csv = args.matrix
    coords_csv_path = args.coords
    output_file = "output.txt"

    print("Exécution de l'algorithme génétique…")
    execute(file_matrix_csv)

    with open(output_file, 'r', encoding='utf-8') as f:
        output_text = f.read()
    routes_raw, totaux = parse_routes_from_text(output_text)

    print("Génération de la carte…")
    camions = regroup_and_split_by_truck(routes_raw)
    temp_map_path = "temp_route_map.png"
    create_route_map(camions, coords_csv_path, temp_map_path)

    tab_fusion = fusionne_trajet(routes_raw)
    obj, totaux = createJsonObject(file_matrix_csv, coords_csv_path,
                                   tab_fusion, totaux)
    if "error" in obj:
        print("Erreur dans la génération des routes :", obj)
        return

    print("Création du PDF…")
    pdf = FPDF()
    pdf.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf')
    pdf.add_font('DejaVu', 'B', 'fonts/DejaVuSans.ttf')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('DejaVu', '', 12)

    if os.path.exists("temp_route_map.png"):
        draw_map(pdf, "temp_route_map.png")
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10,
                 f"Distance totale (toutes tournées) : {totaux.get('distance_totale', 0):.2f} km")
        pdf.ln(7)
        pdf.cell(0, 10,
                 f"Durée totale estimée : {totaux.get('temps_total', 0):.2f} min")
        pdf.ln(10)

    add_trucks_pdf_pages(pdf, obj)
    pdf.output("recapitulatif_globale.pdf")

    if os.path.exists(temp_map_path):
        os.remove(temp_map_path)

    print("Le PDF récapitulatif avec carte a été généré avec succès !")
    print("Fichier de sortie : recapitulatif_globale.pdf")


if __name__ == "__main__":
    main()