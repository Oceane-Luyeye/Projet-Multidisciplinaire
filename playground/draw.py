#!/usr/bin/env python3
"""
plot_routes.py

Reads:
- output.txt: contains routes in the format:
    1: 0 -> 1 -> 12 -> 9 -> 3 -> 14 -> 0 | Distance: 98.80 | Time: 135.54
    2: 0 -> 4 -> 10 -> 5 -> 13 -> 6 -> 0 | Distance: 88.19 | Time: 121.29
    ...

- coordinates CSV: has columns id, name, latitude, longitude

Produces a matplotlib plot showing each route with a distinct color,
drawing lines between consecutive points, and marking all points.
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt

def parse_output(output_file):
    """
    Parse output.txt and return a list of routes.
    Each route is a list of integer node IDs.
    """
    routes = []
    with open(output_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # We expect lines like "1: 0 -> 1 -> ... -> 0 | Distance: ..."
            parts = line.split('|')[0].strip()  # take the left part before '|'
            # Remove the "1: " prefix
            colon_idx = parts.find(':')
            if colon_idx == -1:
                continue
            route_str = parts[colon_idx+1:].strip()
            # route_str like "0 -> 1 -> 12 -> 9 -> 3 -> 14 -> 0"
            node_strs = [s.strip() for s in route_str.split('->')]
            try:
                nodes = [int(s) for s in node_strs]
                routes.append(nodes)
            except ValueError:
                # skip lines that don't parse properly
                continue
    return routes

def plot_routes(routes, coords_df, output_image=None):
    """
    Given a list of routes (each a list of node IDs) and a DataFrame
    coords_df with columns ['id','latitude','longitude'], draw the routes.
    """
    # Build a dict: id -> (longitude, latitude)
    id_to_coord = {int(row['id']): (row['longitude'], row['latitude'])
                   for _, row in coords_df.iterrows()}

    plt.figure(figsize=(7,5))
    cmap = plt.get_cmap('tab10')

    # Plot all points with ID labels
    for _, row in coords_df.iterrows():
        x, y = row['longitude'], row['latitude']
        plt.scatter(x, y, color='black', s=20)
        plt.text(x + 0.001, y + 0.001, str(int(row['id'])), fontsize=9)

    # Draw each route in a different color
    for i, route in enumerate(routes):
        xs, ys = [], []
        for node in route:
            if node not in id_to_coord:
                raise ValueError(f"Node ID {node} not found in coordinates CSV.")
            lon, lat = id_to_coord[node]
            xs.append(lon)
            ys.append(lat)
        color = cmap(i % 10)
        plt.plot(xs, ys, marker='o', color=color, linewidth=2, label=f'Route {i+1}')

    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Vehicle Routing Solution')
    plt.legend(loc='best')
    plt.grid(True)

    if output_image:
        plt.savefig(output_image, dpi=300)
        print(f"Figure saved to {output_image}")
    else:
        plt.show()

def main():
    parser = argparse.ArgumentParser(description='Plot routes from output.txt using coordinates.')
    parser.add_argument('output_txt', help='Path to output.txt containing routes')
    parser.add_argument('coords_csv', help='Path to CSV file with id,latitude,longitude')
    parser.add_argument('--save', '-s', help='Optional path to save the figure (e.g. routes.png)')
    args = parser.parse_args()

    # Load coordinates (only need id, latitude, longitude columns)
    coords_df = pd.read_csv(args.coords_csv, usecols=['id','latitude','longitude'])
    routes = parse_output(args.output_txt)
    if not routes:
        print("No routes found in output file.")
        return

    plot_routes(routes, coords_df, args.save)

if __name__ == '__main__':
    main()