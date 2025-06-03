/* genetic_vrp_cli.c
 * Command-line Genetic Algorithm for Vehicle Routing Problem (VRP).
 * Reads CSV with columns: origin_id,destination_id,distance_km,time_min
 * Usage:
 *   ./genetic_vrp_cli <matrix_csv> [min_trucks max_trucks]
 * If min_trucks and max_trucks are omitted, the program uses
 *   min_trucks = n_points/10, max_trucks = n_points/5.
 * IDs in the CSV should be 0-based (0 = depot, 1..N = customers).
 * Outputs best solution per truck count and global best, and writes
 *   each route’s distance & time into output.txt.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* Hyperparameters */
#define POP_SIZE 1000
#define GENERATIONS 10000
#define MUTATION_RATE 0.075
#define ELITE_FRAC 0.45
#define MAX_DURATION 180.0
#define STOP_TIME 3.0
#define PENALTY_BASE 1e6
#define PENALTY_RATE 10.0
#define SKIP_NO_CHANGE 5000

/* Individual representation */
typedef struct
{
    int *perm;      // permutation of customer IDs (1..n_points-1)
    int trucks;     // number of trucks/routes
    double fitness; // total distance (with penalties)
} Individual;

/* Global data */
static int n_points;     // total number of points (including depot = 0)
static double *dist_mat; // flattened n_points × n_points distance matrix
static double *time_mat; // flattened n_points × n_points travel-time matrix
#define IDX(i, j) ((i) * n_points + (j))

/* Load matrices from CSV (expects IDs 0..max_id, 0 = depot) */
void load_matrices(const char *path)
{
    FILE *f = fopen(path, "r");
    if (!f)
    {
        perror("fopen");
        exit(1);
    }
    char line[256];
    int max_id = 0;

    /* First pass: find highest ID */
    fgets(line, sizeof(line), f); // skip header
    while (fgets(line, sizeof(line), f))
    {
        int o, d;
        if (sscanf(line, "%d,%d,%*f,%*f", &o, &d) >= 2)
        {
            if (o > max_id)
                max_id = o;
            if (d > max_id)
                max_id = d;
        }
    }
    /* Since IDs are 0-based, total points = max_id + 1 */
    n_points = max_id + 1;

    /* Allocate flattened matrices */
    dist_mat = calloc((size_t)n_points * n_points, sizeof(double));
    time_mat = calloc((size_t)n_points * n_points, sizeof(double));
    if (!dist_mat || !time_mat)
    {
        fprintf(stderr, "Allocation failed\n");
        exit(1);
    }

    /* Second pass: read distances and times */
    rewind(f);
    fgets(line, sizeof(line), f); // skip header again
    while (fgets(line, sizeof(line), f))
    {
        int o, d;
        double dk, tm;
        if (sscanf(line, "%d,%d,%lf,%lf", &o, &d, &dk, &tm) == 4)
        {
            /* Use IDs directly (0-based) */
            int i = o;
            int j = d;
            dist_mat[IDX(i, j)] = dk;
            time_mat[IDX(i, j)] = tm;
        }
    }
    fclose(f);

    /* Fill symmetric entries (assume undirected) */
    for (int i = 0; i < n_points; i++)
    {
        for (int j = i + 1; j < n_points; j++)
        {
            dist_mat[IDX(j, i)] = dist_mat[IDX(i, j)];
            time_mat[IDX(j, i)] = time_mat[IDX(i, j)];
        }
    }
}

/* Initialize population of size POP_SIZE for a given number of trucks */
Individual *init_pop(int trucks)
{
    int nc = n_points - 1; // number of customers (exclude depot 0)
    int *cust = malloc(nc * sizeof(int));
    if (!cust)
    {
        fprintf(stderr, "Allocation failed\n");
        exit(1);
    }
    /* Customer IDs = 1..(n_points-1) */
    for (int i = 1; i < n_points; i++)
    {
        cust[i - 1] = i;
    }

    Individual *pop = malloc(POP_SIZE * sizeof(Individual));
    if (!pop)
    {
        fprintf(stderr, "Allocation failed\n");
        exit(1);
    }

    for (int p = 0; p < POP_SIZE; p++)
    {
        pop[p].trucks = trucks;
        pop[p].perm = malloc(nc * sizeof(int));
        if (!pop[p].perm)
        {
            fprintf(stderr, "Allocation failed\n");
            exit(1);
        }
        /* Copy the customer list and shuffle */
        memcpy(pop[p].perm, cust, nc * sizeof(int));
        for (int i = nc - 1; i > 0; i--)
        {
            int j = rand() % (i + 1);
            int t = pop[p].perm[i];
            pop[p].perm[i] = pop[p].perm[j];
            pop[p].perm[j] = t;
        }
    }
    free(cust);
    return pop;
}

/* Evaluate fitness (total dist + penalty) of one individual */
void eval_ind(Individual *ind)
{
    int nc = n_points - 1; // customers
    int trucks = ind->trucks;
    int size = (nc + trucks - 1) / trucks; // ceil(nc / trucks)
    double tot = 0.0;

    for (int t = 0; t < trucks; ++t)
    {
        int start = t * size;
        int end = start + size;
        if (end > nc)
            end = nc;

        double tt = 0.0; // total travel‐time for this truck
        int prev = 0;    // start at depot (0)

        for (int i = start; i < end; ++i)
        {
            int c = ind->perm[i];
            if (c < 0 || c >= n_points)
                continue; // safety
            tot += dist_mat[IDX(prev, c)];
            tt += time_mat[IDX(prev, c)] + STOP_TIME;
            prev = c;
        }
        /* Return to depot */
        tot += dist_mat[IDX(prev, 0)];
        tt += time_mat[IDX(prev, 0)];

        /* Add penalty if over max duration */
        if (tt > MAX_DURATION)
        {
            tot += PENALTY_BASE + (tt - MAX_DURATION) * PENALTY_RATE;
        }
    }
    ind->fitness = tot;
}

/* Comparator for qsort: ascending fitness */
int cmp_ind(const void *a, const void *b)
{
    double fa = ((Individual *)a)->fitness;
    double fb = ((Individual *)b)->fitness;
    if (fa < fb)
        return -1;
    if (fa > fb)
        return 1;
    return 0;
}

/* Run GA for a fixed number of trucks, return best Individual (caller must free .perm) */
Individual run_ga(int trucks)
{
    int nc = n_points - 1;
    /* Initialize population */
    Individual *pop = init_pop(trucks);
    int elite = (int)(POP_SIZE * ELITE_FRAC);
    if (elite < 2)
        elite = 2;

    /* Prepare best‐so‐far */
    Individual best;
    best.perm = malloc(nc * sizeof(int));
    if (!best.perm)
    {
        fprintf(stderr, "Allocation failed\n");
        exit(1);
    }
    best.trucks = trucks;
    best.fitness = INFINITY;
    int cpt = 0; // count of generations with no improvement

    for (int gen = 0; gen < GENERATIONS; gen++)
    {
        /* Evaluate all */
        for (int i = 0; i < POP_SIZE; i++)
        {
            eval_ind(&pop[i]);
        }
        /* Sort by fitness (ascending) */
        qsort(pop, POP_SIZE, sizeof(Individual), cmp_ind);

        /* Check for new best */
        if (pop[0].fitness < best.fitness)
        {
            best.fitness = pop[0].fitness;
            cpt = 0;
            memcpy(best.perm, pop[0].perm, nc * sizeof(int));
        }
        else
        {
            cpt++;
            if (cpt > SKIP_NO_CHANGE)
            {
                printf("No improvement for %d generations, stopping.\n", SKIP_NO_CHANGE);
                printf("Gen: %d\n", gen);
                break;
            }
        }

        /* Create next generation */
        Individual *next = malloc(POP_SIZE * sizeof(Individual));
        if (!next)
        {
            fprintf(stderr, "Allocation failed\n");
            exit(1);
        }
        int idx = 0;

        /* Copy elites */
        for (int i = 0; i < elite; i++)
        {
            next[idx].trucks = pop[i].trucks;
            next[idx].perm = malloc(nc * sizeof(int));
            if (!next[idx].perm)
            {
                fprintf(stderr, "Allocation failed\n");
                exit(1);
            }
            memcpy(next[idx].perm, pop[i].perm, nc * sizeof(int));
            idx++;
        }

        /* Generate offspring until next is full */
        while (idx < POP_SIZE)
        {
            /* Pick two parents from top half */
            Individual *p1 = &pop[rand() % (POP_SIZE / 2)];
            Individual *p2 = &pop[rand() % (POP_SIZE / 2)];

            /* Ordered crossover */
            int a = rand() % nc;
            int b = rand() % nc;
            if (a > b)
            {
                int t = a;
                a = b;
                b = t;
            }

            int *c1 = calloc(nc, sizeof(int));
            int *c2 = calloc(nc, sizeof(int));
            if (!c1 || !c2)
            {
                fprintf(stderr, "Allocation failed\n");
                exit(1);
            }

            /* Copy segment [a..b) */
            for (int i = a; i < b; i++)
            {
                c1[i] = p1->perm[i];
                c2[i] = p2->perm[i];
            }

            /* Fill remainder for c1 from p2 */
            int pos1 = b;
            for (int i = 0; i < nc; i++)
            {
                int gene = p2->perm[(b + i) % nc];
                int found = 0;
                for (int k = a; k < b; k++)
                {
                    if (c1[k] == gene)
                    {
                        found = 1;
                        break;
                    }
                }
                if (!found)
                {
                    if (pos1 >= nc)
                        pos1 = 0;
                    c1[pos1++] = gene;
                }
            }
            /* Fill remainder for c2 from p1 */
            int pos2 = b;
            for (int i = 0; i < nc; i++)
            {
                int gene = p1->perm[(b + i) % nc];
                int found = 0;
                for (int k = a; k < b; k++)
                {
                    if (c2[k] == gene)
                    {
                        found = 1;
                        break;
                    }
                }
                if (!found)
                {
                    if (pos2 >= nc)
                        pos2 = 0;
                    c2[pos2++] = gene;
                }
            }

            /* Mutation: swap pairs in each child */
            int swaps = (int)(nc * MUTATION_RATE);
            for (int m = 0; m < swaps; m++)
            {
                int i = rand() % nc;
                int j = rand() % nc;
                int tmp = c1[i];
                c1[i] = c1[j];
                c1[j] = tmp;
                tmp = c2[i];
                c2[i] = c2[j];
                c2[j] = tmp;
            }

            /* Add child 1 */
            next[idx].trucks = trucks;
            next[idx].perm = c1;
            idx++;
            /* Add child 2 if space remains */
            if (idx < POP_SIZE)
            {
                next[idx].trucks = trucks;
                next[idx].perm = c2;
                idx++;
            }
            else
            {
                free(c2);
            }
        }

        /* Free old population */
        for (int i = 0; i < POP_SIZE; i++)
        {
            free(pop[i].perm);
        }
        free(pop);
        pop = next;
    }

    /* Cleanup final population */
    for (int i = 0; i < POP_SIZE; i++)
    {
        free(pop[i].perm);
    }
    free(pop);
    return best; // best.perm was malloc'd
}

int main(int argc, char **argv)
{
    if (argc < 2)
    {
        fprintf(stderr, "Usage: %s matrix.csv [min_trucks max_trucks]\n", argv[0]);
        return 1;
    }

    srand(time(NULL));
    load_matrices(argv[1]);

    int min_t, max_t;
    if (argc == 4)
    {
        /* User provided a range */
        min_t = atoi(argv[2]);
        max_t = atoi(argv[3]);
        if (min_t < 1 || max_t < min_t)
        {
            fprintf(stderr, "Error: need 1 <= min_trucks <= max_trucks.\n");
            return 1;
        }
    }
    else
    {
        /* Fallback to heuristic based on number of points */
        min_t = n_points / 10;
        max_t = n_points / 5;
        if (min_t < 1)
            min_t = 1;
        if (max_t < min_t)
            max_t = min_t;
    }

    printf("GA trucks %d..%d\n", min_t, max_t);

    Individual global = {NULL, 0, INFINITY};
    int gk = min_t;

    for (int k = min_t; k <= max_t; k++)
    {
        Individual sol = run_ga(k);
        printf("%d trucks: %.2f\n", k, sol.fitness);
        if (sol.fitness < global.fitness)
        {
            if (global.perm)
                free(global.perm);
            global = sol;
            gk = k;
        }
        else
        {
            free(sol.perm);
        }
    }

    /* Print best overall solution to stdout */
    printf("Best %d trucks: routes=[", gk);
    {
        int nc = n_points - 1;
        int size = (nc + gk - 1) / gk;
        for (int t = 0; t < gk; ++t)
        {
            int start = t * size;
            int end = start + size;
            if (end > nc)
                end = nc;
            printf("[0");
            for (int i = start; i < end; ++i)
            {
                printf(", %d", global.perm[i]);
            }
            printf(", 0]");
            if (t < gk - 1)
                printf(", ");
        }
    }
    printf("] dist=%.2f\n", global.fitness);

    /* Write only the detailed routes + metrics into output.txt */
    {
        FILE *out = fopen("output.txt", "w");
        if (!out)
        {
            perror("fopen(output.txt)");
            // Continue even if file creation fails
        }
        else
        {
            int nc = n_points - 1;
            int size = (nc + gk - 1) / gk;

            /* For each truck, compute distance & time, and print one line */
            for (int t = 0; t < gk; ++t)
            {
                int route_idx = t + 1;
                int start = t * size;
                int end = start + size;
                if (end > nc)
                    end = nc;

                /* Recompute distance & time for this route */
                double route_dist = 0.0;
                double route_time = 0.0;
                int prev = 0;

                /* From depot to first customer, through all, then back to depot */
                for (int i = start; i < end; ++i)
                {
                    int c = global.perm[i];
                    route_dist += dist_mat[IDX(prev, c)];
                    route_time += time_mat[IDX(prev, c)] + STOP_TIME;
                    prev = c;
                }
                /* Return to depot */
                route_dist += dist_mat[IDX(prev, 0)];
                route_time += time_mat[IDX(prev, 0)];

                /* Print route and metrics */
                fprintf(out, "%d: 0", route_idx);
                for (int i = start; i < end; ++i)
                {
                    fprintf(out, " -> %d", global.perm[i]);
                }
                fprintf(out, " -> 0");
                fprintf(out, " | Distance: %.2f | Time: %.2f\n",
                        route_dist, route_time);
            }

            fclose(out);
        }
    }

    free(global.perm);
    free(dist_mat);
    free(time_mat);
    return 0;
}