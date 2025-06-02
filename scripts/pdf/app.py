from datetime import datetime, timedelta
import pprint
from flask import Flask, json, render_template, send_file, jsonify
import subprocess
import csv

app = Flask(__name__, static_url_path="", static_folder="static")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/generate')
def generate_routes():
    try:
        compile = subprocess.run(["gcc", "test.c", "-o", "test"], capture_output=True, text=True)
        if compile.returncode != 0:
            return jsonify({"status": "error", "message": "Erreur compilation", "details": result.stderr}), 500

        result = subprocess.run(["./test"], capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({"status": "error", "message": "Erreur exécution", "details": result.stderr}), 500

        data = json.loads(result.stdout)
        return createJsonObject(data)
        

    except Exception as e:
        return jsonify({"status": "error", "message": f"Erreur serveur : {e}"}), 500


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

    matrix_dist, matrix_time = getMatrix("data/depot_with_id/30/livraison30_matrix.csv")

    result = {}

    for i, item in enumerate(tab):
        trajet_dict = {}
        distance_totale = 0
        duree_totale = 0

        current_time = datetime.strptime("09:00", "%H:%M")
        fin_matin = datetime.strptime("12:00", "%H:%M")
        debut_aprem = datetime.strptime("15:00", "%H:%M")
        fin_aprem = datetime.strptime("18:00", "%H:%M")

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

            #if (in_aprem and current_time + timedelta(minutes=duree) > fin_aprem) or duree_tournee + duree > 180:
            #    break

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




if __name__ == '__main__':
    app.run(debug=True)

