import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import time
import math


def generate_city_coords(num_cities, x_range=(0, 400), y_range=(0, 400), seed=None):
    if seed is not None:
        random.seed(seed)
    
    return [
        (random.randint(*x_range), random.randint(*y_range))
        for _ in range(num_cities)
    ]

CITY_COORDS = generate_city_coords(20, x_range=(20, 350), y_range=(20, 350), seed=42)

def euclidean_distance(p1, p2):
    return round(math.dist(p1, p2))

n = len(CITY_COORDS)
DISTANCES = [[0]*n for _ in range(n)]

for i in range(n):
    for j in range(n):
        if i != j:
            DISTANCES[i][j] = euclidean_distance(CITY_COORDS[i], CITY_COORDS[j])

CITIES = list(range(len(DISTANCES)))

def create_route():
    route = CITIES[:]
    random.shuffle(route)
    return route

def initialize_population(pop_size):
    return [create_route() for _ in range(pop_size)]

def fitness(route):
    distance = sum(DISTANCES[route[i]][route[i+1]] for i in range(len(route)-1)) + DISTANCES[route[-1]][route[0]]
    fuel_consumption = distance / 100 * 8.5  # Consommation en litre (8.5L pour 100 km)
    return distance + fuel_consumption  # La fitness combine distance et carburant

def select_parents(population, k=15):   
    return min(random.sample(population, k), key=fitness)

def crossover(parent1, parent2):
    size = len(parent1)
    start, end = sorted(random.sample(range(size), 2))
    child = [-1] * size
    child[start:end] = parent1[start:end]
    p2_filtered = [city for city in parent2 if city not in child]
    j = 0
    for i in range(size):
        if child[i] == -1:
            child[i] = p2_filtered[j]
            j += 1
    return child

def mutate(route, mutation_rate=0.1):
    if random.random() < mutation_rate:
        i, j = random.sample(range(len(route)), 2)
        route[i], route[j] = route[j], route[i]
    return route

def divide_route_into_trucks(best_route, num_trucks):
    trucks_routes = []
    
    best_route_without_zero = [city for city in best_route if city != 0]
    
    chunk_size = len(best_route_without_zero) // num_trucks
    remainder = len(best_route_without_zero) % num_trucks
    
    index = 0
    for i in range(num_trucks):
        segment_size = chunk_size + (1 if i < remainder else 0)
        truck_route = [0] + best_route_without_zero[index:index + segment_size] + [0]
        trucks_routes.append(truck_route)
        index += segment_size

    return trucks_routes

# Déterminer automatiquement le nombre de camions
def determine_num_trucks(num_cities):
    return max(1, num_cities // 5)  # Diviser les villes par 5 pour obtenir une estimation du nombre de camions.

# GUI Class
class TSPGui:
    def __init__(self, root):
        self.root = root
        self.root.title("TSP Genetic Algorithm Visualizer")

        self.start_button = ttk.Button(root, text="Start", command=self.run_algorithm)
        self.start_button.pack(pady=10)
        
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

    def draw_route(self, trucks_routes, gen, distance):
        self.ax.clear()
        colors = ['r', 'g', 'b', 'y', 'm', 'c', 'orange', 'purple', 'pink', 'brown', 
                  'lime', 'indigo', 'violet', 'teal', 'navy', 'gold', 'silver', 'aqua', 
                  'fuchsia', 'coral', 'tomato', 'orchid', 'chartreuse', 'plum', 'khaki']  # Liste de couleurs plus grande
        
        # Affichage des itinéraires des camions avec couleurs
        for truck_idx, route in enumerate(trucks_routes):
            x = [CITY_COORDS[city][0] for city in route] + [CITY_COORDS[route[0]][0]]
            y = [CITY_COORDS[city][1] for city in route] + [CITY_COORDS[route[0]][1]]
            self.ax.plot(x, y, marker='o', color=colors[truck_idx % len(colors)], label=f"Truck {truck_idx + 1}")

        for i, (xx, yy) in enumerate(CITY_COORDS):
            self.ax.text(xx + 5, yy + 5, str(i))

        self.ax.set_title(f"Total Distance: {distance:.2f}")
        self.ax.legend()
        self.canvas.draw()

    def run_algorithm(self):
        pop_size = 200
        generations = 1000
        mutation_rate = 0.1
        population = initialize_population(pop_size)

        best_route = None
        best_distance = float('inf')

        for gen in range(generations):
            population = sorted(population, key=fitness)
            new_population = [population[0]]

            while len(new_population) < pop_size:
                parent1, parent2 = select_parents(population), select_parents(population)
                child = crossover(parent1, parent2)
                child = mutate(child, mutation_rate)
                new_population.append(child)

            population = new_population
            current_best_route = min(population, key=fitness)
            current_best_distance = fitness(current_best_route)

            if current_best_distance < best_distance:
                best_route = current_best_route
                best_distance = current_best_distance

            if gen % 10 == 0:
                print(f"Generation {gen} - Distance: {best_distance}")

        # Déterminer le nombre de camions à utiliser
        num_trucks = determine_num_trucks(len(CITY_COORDS))
        
        # Diviser le meilleur itinéraire en itinéraires pour les camions
        trucks_routes = divide_route_into_trucks(best_route, num_trucks)
        
        # Affichage de l'itinéraire des camions
        self.draw_route(trucks_routes, generations, best_distance)

        # Affichage du meilleur itinéraire et de la distance
        print("Best Route:", best_route)
        print("Best Distance:", best_distance)

if __name__ == '__main__':
    root = tk.Tk()
    app = TSPGui(root)
    root.mainloop()
genetic.py


## Generation du pdf 

{
    
}