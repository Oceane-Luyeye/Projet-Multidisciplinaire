import os
import csv
import math
import argparse
import pandas as pd
import requests
import openrouteservice

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate distance and time matrix from a delivery list CSV file using OpenRouteService."
    )
    parser.add_argument(
        'input_csv',
        help='Path to the input CSV file with delivery addresses (no header, columns: name, street, postal_code, city)'
    )
    args = parser.parse_args()

    api_key = "5b3ce3597851110001cf62487e2739ab43d8469aa4faf8da7acc850d"
    all_csv_path = 'data/database/all.csv'
    output_dir = 'data/output/csv/'

    # Load input and database
    base_df = pd.read_csv(args.input_csv, header=None,
                          names=['name', 'street', 'postal_code', 'city'])
    all_df = pd.read_csv(all_csv_path)

    # Select the depot (first match containing "dépôt" in name)
    depot_row = all_df[all_df['name'].str.lower().str.contains('dépôt', case=False)].iloc[0:1].copy()

    # Merge client addresses with coordinates
    merged_df = pd.merge(base_df, all_df,
                         on=['name', 'street', 'postal_code', 'city'], how='inner')
    merged_df = merged_df[['name', 'street', 'postal_code', 'city', 'latitude', 'longitude']]

    # Combine depot and clients, assign IDs
    full_df = pd.concat([depot_row, merged_df], ignore_index=True)
    full_df.insert(0, 'id', range(len(full_df)))

    # Create suffix based on number of clients (excluding depot)
    suffix = len(full_df) - 1

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save coordinates CSV
    coord_path = os.path.join(output_dir, f'coordinates_{suffix}.csv')
    full_df.to_csv(coord_path, index=False)
    print(f"📍 Coordinates saved to: {coord_path}")

    # Read back coordinates for matrix generation
    df_coords = pd.read_csv(coord_path)
    required_columns = {'id', 'latitude', 'longitude'}
    if not required_columns.issubset(df_coords.columns):
        raise ValueError(f"CSV file must contain columns: {required_columns}")

    # Prepare locations and IDs lists
    locations = []
    ids = []
    for _, row in df_coords.iterrows():
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            locations.append([lon, lat])
            ids.append(int(row['id']))
        except ValueError:
            print(f"Invalid coordinates ignored: {row}")

    # ORS client setup
    client = openrouteservice.Client(key=api_key)
    MAX_ROUTES = 3500
    N = len(locations)
    max_block = int(math.floor(math.sqrt(MAX_ROUTES)))
    print(f"Total points (including depot): {N} | Block size: {max_block}x{max_block}")

    # Generate matrix CSV
    matrix_path = os.path.join(output_dir, f'matrix_{suffix}.csv')
    count = 0
    with open(matrix_path, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["origin_id", "destination_id", "distance_km", "time_min"])

        for i_start in range(0, N, max_block):
            for j_start in range(0, N, max_block):
                origins = locations[i_start:i_start + max_block]
                destinations = locations[j_start:j_start + max_block]
                origin_ids = ids[i_start:i_start + max_block]
                destination_ids = ids[j_start:j_start + max_block]

                body = {
                    "locations": origins + destinations,
                    "sources": list(range(len(origins))),
                    "destinations": list(range(len(origins), len(origins) + len(destinations))),
                    "metrics": ["distance", "duration"],
                    "units": "m"
                }
                headers = {
                    'Accept': 'application/json',
                    'Authorization': api_key,
                    'Content-Type': 'application/json'
                }

                print(f"Processing block: {len(origins)} origins × {len(destinations)} destinations")
                response = requests.post(
                    "https://api.openrouteservice.org/v2/matrix/driving-car",
                    json=body,
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    distances = data.get('distances', [])
                    durations = data.get('durations', [])

                    for i, oid in enumerate(origin_ids):
                        for j, did in enumerate(destination_ids):
                            if oid != did:
                                try:
                                    distance_km = distances[i][j] / 1000.0
                                    time_min = durations[i][j] / 60.0
                                    writer.writerow([oid, did, distance_km, time_min])
                                    count += 1
                                except (IndexError, TypeError) as e:
                                    print(f"Missing data for {oid} -> {did}: {e}")
                                    writer.writerow([oid, did, None, None])
                else:
                    print(f"ORS API error for block {i_start}-{j_start}: {response.status_code} - {response.text}")
                    return

    print(f"\nMatrix generated: {matrix_path} | Total rows: {count}")

    # Sort final CSV
    print("Sorting by origin_id and destination_id...")
    df_matrix = pd.read_csv(matrix_path)
    df_sorted = df_matrix.sort_values(by=['origin_id', 'destination_id'])
    df_sorted.to_csv(matrix_path, index=False)
    print("✅ Matrix sorted.")

    # Verification
    print("\nVerifying completeness...")
    expected_per_origin = N - 1
    missing_flag = False
    grouped = df_sorted.groupby('origin_id').size()

    for origin in sorted(ids):
        found = grouped.get(origin, 0)
        if found != expected_per_origin:
            print(f"Origin {origin} has {found} rows (expected {expected_per_origin})")
            missing_flag = True

    if not missing_flag:
        print("All expected rows present for each id (excluding self-loops).")

if __name__ == "__main__":
    main()