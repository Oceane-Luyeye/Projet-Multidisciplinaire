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

CITY_COORDS = generate_city_coords(50, x_range=(50, 350), y_range=(50, 350), seed=42)

def euclidean_distance(p1, p2):
    return round(math.dist(p1, p2))

n = len(CITY_COORDS)
DISTANCES = [[0]*n for _ in range(n)]

for i in range(n):
    for j in range(n):
        if i != j:
            DISTANCES[i][j] = euclidean_distance(CITY_COORDS[i], CITY_COORDS[j])


print(CITY_COORDS)
print(DISTANCES)
CITIES = list(range(len(DISTANCES)))

def create_route():
    route = CITIES[:]
    random.shuffle(route)
    return route

def initialize_population(pop_size):
    return [create_route() for _ in range(pop_size)]

def fitness(route):
    return sum(DISTANCES[route[i]][route[i+1]] for i in range(len(route)-1)) + DISTANCES[route[-1]][route[0]]

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

# GUI Class
class TSPGui:
    def __init__(self, root):
        self.root = root
        self.root.title("TSP Genetic Algorithm Visualizer")

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        self.start_button = ttk.Button(root, text="Start", command=self.run_algorithm)
        self.start_button.pack(pady=10)

    def draw_route(self, route, gen, distance):
        self.ax.clear()
        x = [CITY_COORDS[city][0] for city in route] + [CITY_COORDS[route[0]][0]]
        y = [CITY_COORDS[city][1] for city in route] + [CITY_COORDS[route[0]][1]]

        self.ax.plot(x, y, marker='o')
        for i, (xx, yy) in enumerate(CITY_COORDS):
            self.ax.text(xx + 5, yy + 5, str(i))

        self.ax.set_title(f"Generation {gen}, Distance: {distance:.2f}")
        self.canvas.draw()

    def run_algorithm(self):
        pop_size = 200
        generations = 1000
        mutation_rate = 0.1
        population = initialize_population(pop_size)

        for gen in range(generations):
            population = sorted(population, key=fitness)
            new_population = [population[0]]

            while len(new_population) < pop_size:
                parent1, parent2 = select_parents(population), select_parents(population)
                child = crossover(parent1, parent2)
                child = mutate(child, mutation_rate)
                new_population.append(child)

            population = new_population
            best_route = min(population, key=fitness)
            best_distance = fitness(best_route)

            if gen % 10 == 0:
                self.draw_route(best_route, gen, best_distance)
                self.root.update()
                time.sleep(0.1)

        self.draw_route(best_route, generations, best_distance)
        print("Best Route:", best_route)
        print("Best Distance:", best_distance)


if __name__ == '__main__':
    root = tk.Tk()
    app = TSPGui(root)
    root.mainloop()
