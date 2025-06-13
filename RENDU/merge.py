import os
import csv
import math
import argparse
import pandas as pd
import requests
import openrouteservice


DEPOT = {
    'name':         'Dépôt',
    'street':       '600 Rue des Madeleines',
    'postal_code':  '77100',
    'city':         'Mareuil-lès-Meaux',
    'latitude':      48.934926,
    'longitude':    2.874246
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate distance/time matrix from a delivery list CSV using OpenRouteService."
    )
    parser.add_argument(
        'input_csv',
        help='Path to input CSV file (no header: name,street,postal_code,city)'
    )
    args = parser.parse_args()

    api_key       = "5b3ce3597851110001cf62487e2739ab43d8469aa4faf8da7acc850d"
    all_csv_path  = 'data/database/all.csv'
    output_dir    = 'data/output/'

    # 1) read your clients
    base_df = pd.read_csv(args.input_csv, header=None,
                          names=['name','street','postal_code','city'])

    # 2) look up coords for clients only
    all_df  = pd.read_csv(all_csv_path)
    merged  = pd.merge(base_df, all_df,
                       on=['name','street','postal_code','city'],
                       how='inner')
    merged  = merged[['name','street','postal_code','city','latitude','longitude']]

    # 3) build a one-row df for the hard-coded depot
    depot_row = pd.DataFrame([{
        'name':        DEPOT['name'],
        'street':      DEPOT['street'],
        'postal_code': DEPOT['postal_code'],
        'city':        DEPOT['city'],
        'latitude':    DEPOT['latitude'],
        'longitude':   DEPOT['longitude']
    }])

    # 4) combine depot + clients, assign incremental IDs
    full_df = pd.concat([depot_row, merged], ignore_index=True)
    full_df.insert(0, 'id', range(len(full_df)))

    # 5) suffix = number of clients
    suffix = len(full_df) - 1

    # ensure output directory
    os.makedirs(output_dir, exist_ok=True)

    # 6) write coords CSV
    coord_path = os.path.join(output_dir, f'coordinates_{suffix}.csv')
    full_df.to_csv(coord_path, index=False)

    # 7) reload coords (just to be safe)
    df_coords = pd.read_csv(coord_path)
    if not {'id','latitude','longitude'}.issubset(df_coords):
        raise ValueError("Coordinates CSV missing required columns")

    # 8) extract locations and IDs
    locations, ids = [], []
    for _, row in df_coords.iterrows():
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            locations.append([lon, lat])
            ids.append(int(row['id']))
        except ValueError:
            print("Invalid coordinate, skipped:", row)

    # 9) build ORS matrix in blocks
    client = openrouteservice.Client(key=api_key)
    MAX_ROUTES = 3500
    N          = len(locations)
    block      = int(math.floor(math.sqrt(MAX_ROUTES)))

    matrix_path = os.path.join(output_dir, f'matrix_{suffix}.csv')
    count = 0
    with open(matrix_path, 'w', newline='', encoding='utf-8') as fo:
        writer = csv.writer(fo)
        writer.writerow(["origin_id","destination_id","distance_km","time_min"])

        for i in range(0, N, block):
            for j in range(0, N, block):
                orig = locations[i:i+block]
                dest = locations[j:j+block]
                oids = ids[i:i+block]
                dids = ids[j:j+block]

                body = {
                    "locations": orig + dest,
                    "sources":   list(range(len(orig))),
                    "destinations": list(range(len(orig), len(orig)+len(dest))),
                    "metrics":   ["distance","duration"],
                    "units":     "m"
                }
                headers = {
                    'Accept':       'application/json',
                    'Authorization': api_key,
                    'Content-Type':  'application/json'
                }

                resp = requests.post(
                    "https://api.openrouteservice.org/v2/matrix/driving-car",
                    json=body, headers=headers
                )
                if resp.status_code != 200:
                    print("ORS error", resp.status_code, resp.text)
                    return

                data = resp.json()
                dists = data.get('distances',[])
                times = data.get('durations',[]) 

                for ii, oid in enumerate(oids):
                    for jj, did in enumerate(dids):
                        if oid == did:
                            continue
                        try:
                            dk = dists[ii][jj]/1000.0
                            tm = times[ii][jj]/60.0
                            writer.writerow([oid,did,dk,tm])
                            count += 1
                        except Exception as e:
                            print("Missing", oid, "→", did, e)
                            writer.writerow([oid,did,None,None])

    print(f"\nMatrix generated: {matrix_path} | rows: {count}")

    # 10) sort & verify
    dfm = pd.read_csv(matrix_path)
    dfm.sort_values(['origin_id','destination_id'], inplace=True)
    dfm.to_csv(matrix_path, index=False)

    expected = N - 1
    counts   = dfm.groupby('origin_id').size()
    bad = False
    for origin in sorted(ids):
        got = counts.get(origin,0)
        if got != expected:
            print(f"Origin {origin}: {got}/{expected}")
            bad = True
    if not bad:
        print("All expected rows present (no self-loops).")


if __name__ == "__main__":
    main()