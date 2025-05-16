import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import time
import math
import numpy as np # type: ignore

def generate_city_coords(num_cities, x_range=(0, 400), y_range=(0, 400), seed=None):
    if seed is not None:
        random.seed(seed)
    
    return [
        (random.randint(*x_range), random.randint(*y_range))
        for _ in range(num_cities)
    ]

CITY_COORDS = generate_city_coords(50, x_range=(50, 350), y_range=(50, 350), seed=42)
DEPOT_INDEX = 0  # Le premier point est notre dépôt

def euclidean_distance(p1, p2):
    return round(math.dist(p1, p2))

n = len(CITY_COORDS)
DISTANCES = [[0]*n for _ in range(n)]

for i in range(n):
    for j in range(n):
        if i != j:
            DISTANCES[i][j] = euclidean_distance(CITY_COORDS[i], CITY_COORDS[j])

CITIES = list(range(len(DISTANCES)))


class DeliveryTruck:
    
    def __init__(self, truck_id, capacity, color):
        self.truck_id = truck_id
        self.capacity = capacity
        self.color = color
        self.route = []
        
    def __str__(self):
        return f"Truck {self.truck_id} (capacity: {self.capacity})"


def create_truck_fleet(num_trucks, capacity_range=(500, 1000)):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
    return [
        DeliveryTruck(
            i+1, 
            random.randint(*capacity_range),
            colors[i % len(colors)]
        ) 
        for i in range(num_trucks)
    ]


NUM_TRUCKS = 5
TRUCK_FLEET = create_truck_fleet(NUM_TRUCKS)


def generate_demands(num_cities, demand_range=(10, 100), seed=None):
    if seed is not None:
        random.seed(seed)
    
    demands = [0]  # Le dépôt n'a pas de demande
    for _ in range(num_cities - 1):
        demands.append(random.randint(*demand_range))
    
    return demands

DEMANDS = generate_demands(n, demand_range=(10, 100), seed=42)

def split_route_for_trucks(cities, trucks, demands):
    """Divise une liste de villes entre plusieurs camions, en respectant les capacités"""
    if not cities:
        return []
    
    # On commence toujours par le dépôt
    result = []
    for truck in trucks:
        truck.route = [DEPOT_INDEX]
    
    remaining_cities = [city for city in cities if city != DEPOT_INDEX]
    random.shuffle(remaining_cities)
    


    for city in remaining_cities:
        selected_truck = random.choice(trucks)
        selected_truck.route.append(city)
    
    for truck in trucks:
        total_load = sum(demands[city] for city in truck.route if city != DEPOT_INDEX)
        
        while total_load > truck.capacity and len(truck.route) > 1:
            # Trouver une ville à enlever (pas le dépôt)
            removable = [i for i, city in enumerate(truck.route) if city != DEPOT_INDEX]
            if not removable:
                break
            
            idx_to_remove = random.choice(removable)
            city_to_remove = truck.route[idx_to_remove]
            
            # L'enlever de ce camion
            truck.route.pop(idx_to_remove)
            
            # Mettre à jour la charge
            total_load -= demands[city_to_remove]
            
            # Essayer de l'ajouter à un autre camion
            other_trucks = [t for t in trucks if t != truck]
            random.shuffle(other_trucks)
            
            assigned = False
            for other_truck in other_trucks:
                other_load = sum(demands[c] for c in other_truck.route if c != DEPOT_INDEX)
                if other_load + demands[city_to_remove] <= other_truck.capacity:
                    other_truck.route.append(city_to_remove)
                    assigned = True
                    break
            
            # Si on n'a pas pu l'affecter, on le met de côté
            if not assigned:
                result.append(city_to_remove)
    
    # S'assurer que chaque route de camion se termine au dépôt
    for truck in trucks:
        if truck.route[-1] != DEPOT_INDEX:
            truck.route.append(DEPOT_INDEX)
    
    return result  # Villes non assignées

def create_initial_solution():
    # Créer une flotte de camions
    trucks = [DeliveryTruck(truck.truck_id, truck.capacity, truck.color) for truck in TRUCK_FLEET]
    
    # Répartir les villes entre les camions
    unassigned = split_route_for_trucks(CITIES, trucks, DEMANDS)
    
    # Optimiser l'ordre des villes pour chaque camion
    for truck in trucks:
        # Garder le dépôt au début et à la fin
        middle_route = truck.route[1:-1] if len(truck.route) > 2 else []
        random.shuffle(middle_route)
        truck.route = [DEPOT_INDEX] + middle_route + [DEPOT_INDEX]
    
    return trucks

def initialize_population(pop_size):
    return [create_initial_solution() for _ in range(pop_size)]

def calculate_route_distance(route):
    """Calcule la distance totale d'une route"""
    return sum(DISTANCES[route[i]][route[i+1]] for i in range(len(route)-1))

def fitness(solution):
    """Évalue une solution (ensemble de camions avec leurs routes)"""
    total_distance = 0
    for truck in solution:
        if len(truck.route) > 1:  # Si le camion a une route non vide
            total_distance += calculate_route_distance(truck.route)
    return total_distance

def select_parents(population, k=5):
    """Sélectionne les meilleurs parents d'un échantillon aléatoire"""
    candidates = random.sample(population, k)
    return min(candidates, key=fitness)

def crossover(parent1, parent2):
    """Croise deux solutions pour en créer une nouvelle"""
    # Créer des camions vides pour la solution enfant
    child_trucks = [DeliveryTruck(truck.truck_id, truck.capacity, truck.color) 
                   for truck in TRUCK_FLEET]
    
    # Choisir aléatoirement des routes à prendre du premier parent
    selected_trucks = random.sample(range(len(parent1)), len(parent1) // 2)
    
    # Copier les routes sélectionnées du premier parent
    cities_used = set()
    for idx in selected_trucks:
        child_trucks[idx].route = parent1[idx].route.copy()
        for city in parent1[idx].route:
            if city != DEPOT_INDEX:  # Ignorer le dépôt car il est dans toutes les routes
                cities_used.add(city)
    
    # Trouver les villes restantes du deuxième parent
    remaining_cities = []
    for truck in parent2:
        for city in truck.route:
            if city != DEPOT_INDEX and city not in cities_used:
                remaining_cities.append(city)
                cities_used.add(city)
    
    empty_trucks = [truck for i, truck in enumerate(child_trucks) if i not in selected_trucks]
    
    if empty_trucks and remaining_cities:
        # Diviser les villes restantes entre les camions vides
        split_route_for_trucks(remaining_cities, empty_trucks, DEMANDS)
        
        # S'assurer que chaque camion commence et termine au dépôt
        for truck in empty_trucks:
            if not truck.route:
                truck.route = [DEPOT_INDEX, DEPOT_INDEX]
            elif truck.route[0] != DEPOT_INDEX:
                truck.route.insert(0, DEPOT_INDEX)
            if truck.route[-1] != DEPOT_INDEX:
                truck.route.append(DEPOT_INDEX)
    
    return child_trucks

def mutate(solution, mutation_rate=0.1):
    """Mute une solution en réordonnant ou en échangeant des villes"""
    if random.random() < mutation_rate:
        # Sélectionner un camion au hasard
        truck_idx = random.randrange(len(solution))
        truck = solution[truck_idx]
        
        # Si la route est assez longue, permuter deux villes
        if len(truck.route) > 3:  # Dépôt + au moins 2 villes + dépôt
            # Exclure le dépôt du début et de fin
            i, j = random.sample(range(1, len(truck.route)-1), 2)
            truck.route[i], truck.route[j] = truck.route[j], truck.route[i]
    
    # Parfois, transférer une ville d'un camion à un autre
    if random.random() < mutation_rate:
        # Choisir deux camions différents
        if len(solution) >= 2:
            truck1, truck2 = random.sample(solution, 2)
            
            # Essayer de déplacer une ville du premier au second
            if len(truck1.route) > 3:  # S'assurer qu'il reste au moins une ville après le transfert
                # Choisir une ville à transférer (pas le dépôt)
                idx = random.randint(1, len(truck1.route)-2)
                city_to_move = truck1.route[idx]
                
                # Vérifier si le second camion peut l'accueillir (capacité)
                current_load_truck2 = sum(DEMANDS[city] for city in truck2.route if city != DEPOT_INDEX)
                
                if current_load_truck2 + DEMANDS[city_to_move] <= truck2.capacity:
                    # Effectuer le transfert
                    truck1.route.pop(idx)
                    # Insérer la ville à une position aléatoire dans la route du second camion
                    insert_idx = random.randint(1, len(truck2.route)-1)
                    truck2.route.insert(insert_idx, city_to_move)
    
    return solution

# GUI Class
class TSPGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Truck TSP Genetic Algorithm Visualizer")

        # Paramètres de simulation
        self.frame_controls = ttk.Frame(root)
        self.frame_controls.pack(pady=5, fill=tk.X)
        
        ttk.Label(self.frame_controls, text="Nombre de camions:").grid(row=0, column=0, padx=5)
        self.truck_var = tk.IntVar(value=NUM_TRUCKS)
        self.truck_selector = ttk.Spinbox(self.frame_controls, from_=1, to=10, textvariable=self.truck_var, width=5)
        self.truck_selector.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.frame_controls, text="Générations:").grid(row=0, column=2, padx=5)
        self.gen_var = tk.IntVar(value=1000)
        self.gen_selector = ttk.Spinbox(self.frame_controls, from_=10, to=1000, textvariable=self.gen_var, width=5)
        self.gen_selector.grid(row=0, column=3, padx=5)
        
        ttk.Label(self.frame_controls, text="Population:").grid(row=0, column=4, padx=5)
        self.pop_var = tk.IntVar(value=50)
        self.pop_selector = ttk.Spinbox(self.frame_controls, from_=10, to=500, textvariable=self.pop_var, width=5)
        self.pop_selector.grid(row=0, column=5, padx=5)

        # Figure matplotlib
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Panneau d'information
        self.info_frame = ttk.Frame(root)
        self.info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_text = tk.Text(self.info_frame, height=6, width=80)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.info_frame, command=self.info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)

        # Boutons
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(self.button_frame, text="Démarrer", command=self.run_algorithm)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="Arrêter", command=self.stop_algorithm)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Variable pour arrêter l'algorithme
        self.running = False

    def update_truck_fleet(self):
        global NUM_TRUCKS, TRUCK_FLEET
        NUM_TRUCKS = self.truck_var.get()
        TRUCK_FLEET = create_truck_fleet(NUM_TRUCKS)

    def draw_solution(self, solution, gen, distance):
        self.ax.clear()
        
        # Afficher toutes les villes
        x = [coord[0] for coord in CITY_COORDS]
        y = [coord[1] for coord in CITY_COORDS]
        self.ax.scatter(x, y, color='gray', alpha=0.5)
        
        # Marquer le dépôt
        depot_x, depot_y = CITY_COORDS[DEPOT_INDEX]
        self.ax.scatter([depot_x], [depot_y], color='black', s=100, marker='*')
        self.ax.text(depot_x + 5, depot_y + 5, "DÉPÔT", fontweight='bold')
        
        # Dessiner les routes pour chaque camion
        for truck in solution:
            if len(truck.route) > 1:
                route = truck.route
                route_x = [CITY_COORDS[city][0] for city in route]
                route_y = [CITY_COORDS[city][1] for city in route]
                
                self.ax.plot(route_x, route_y, marker='o', linestyle='-', 
                           color=truck.color, label=f"Camion {truck.truck_id}")
                
                # Ajouter des flèches pour montrer la direction
                for i in range(len(route)-1):
                    dx = route_x[i+1] - route_x[i]
                    dy = route_y[i+1] - route_y[i]
                    # Normaliser pour obtenir une flèche de longueur fixe
                    length = math.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        dx, dy = dx/length*20, dy/length*20  # Flèche de longueur 20
                        midx, midy = (route_x[i] + route_x[i+1])/2, (route_y[i] + route_y[i+1])/2
                        self.ax.arrow(midx-dx/2, midy-dy/2, dx, dy, 
                                    head_width=5, head_length=7, fc=truck.color, ec=truck.color)
        
        # Afficher la légende
        self.ax.legend(loc='upper right')
        
        # Afficher les informations de la génération
        self.ax.set_title(f"Génération {gen}, Distance totale: {distance:.2f}")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        
        # Ajuster les limites
        self.ax.set_xlim(0, 400)
        self.ax.set_ylim(0, 400)
        
        self.canvas.draw()
        
        # Mettre à jour le panneau d'information
        self.info_text.delete(1.0, tk.END)
        
        info = f"Génération: {gen}/{self.gen_var.get()}\n"
        info += f"Distance totale: {distance:.2f}\n\n"
        
        for truck in solution:
            route_distance = calculate_route_distance(truck.route) if len(truck.route) > 1 else 0
            cities_count = len(truck.route) - 2 if len(truck.route) > 1 else 0  # -2 pour exclure le dépôt au début et à la fin
            load = sum(DEMANDS[city] for city in truck.route if city != DEPOT_INDEX)
            
            info += f"Camion {truck.truck_id} (capacité: {truck.capacity}): {cities_count} villes, charge: {load}, distance: {route_distance:.2f}\n"
        
        self.info_text.insert(tk.END, info)

    def stop_algorithm(self):
        self.running = False

    def run_algorithm(self):
        self.update_truck_fleet()
        self.running = True
        
        pop_size = self.pop_var.get()
        generations = self.gen_var.get()
        mutation_rate = 0.1
        
        # Initialiser la population
        population = initialize_population(pop_size)
        
        # Évaluer la population initiale
        best_solution = min(population, key=fitness)
        best_distance = fitness(best_solution)
        
        self.draw_solution(best_solution, 0, best_distance)
        self.root.update()
        
        # Boucle principale
        for gen in range(1, generations + 1):
            if not self.running:
                break
                
            # Trier la population par fitness
            population.sort(key=fitness)
            
            # Créer une nouvelle population
            new_population = [population[0]]  # Élitisme
            
            while len(new_population) < pop_size:
                parent1 = select_parents(population)
                parent2 = select_parents(population)
                
                child = crossover(parent1, parent2)
                child = mutate(child, mutation_rate)
                
                new_population.append(child)
            
            population = new_population
            
            # Trouver la meilleure solution dans cette génération
            current_best = min(population, key=fitness)
            current_best_distance = fitness(current_best)
            
            # Mettre à jour la meilleure solution globale si nécessaire
            if current_best_distance < best_distance:
                best_solution = current_best
                best_distance = current_best_distance
            
            # Affichage périodique
            if gen % 5 == 0 or gen == generations:
                self.draw_solution(best_solution, gen, best_distance)
                self.root.update()
                time.sleep(0.1)
        
        # Affichage final
        self.draw_solution(best_solution, generations if self.running else "Arrêté", best_distance)
        
        # Afficher les détails de la meilleure solution
        print(f"Meilleure distance trouvée: {best_distance:.2f}")
        for truck in best_solution:
            print(f"Camion {truck.truck_id}: {truck.route}")


if __name__ == '__main__':
    root = tk.Tk()
    app = TSPGui(root)
    root.mainloop()