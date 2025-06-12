#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define POP_SIZE 300
#define GENERATIONS 10000
#define MUTATION_RATE 0.1
#define ELITE_FRAC 0.35
#define SKIP_NO_CHANGE 2000
#define IDX(i, j) ((i) * n_points + (j))

typedef struct
{
    int *perm;
    double fitness;
} Individual;

static double *time_mat;
static double *dist_mat;
static int n_points;

void load_matrix(const char *path)
{
    FILE *f = fopen(path, "r");
    if (!f)
    {
        perror("fopen");
        exit(1);
    }

    char line[256];
    int max_id = 0;
    fgets(line, sizeof(line), f);
    while (fgets(line, sizeof(line), f))
    {
        int o, d;
        if (sscanf(line, "%d,%d,%*f,%*f", &o, &d) == 2)
        {
            if (o > max_id)
                max_id = o;
            if (d > max_id)
                max_id = d;
        }
    }
    n_points = max_id + 1;

    dist_mat = malloc(n_points * n_points * sizeof(double));
    time_mat = malloc(n_points * n_points * sizeof(double));
    if (!dist_mat || !time_mat)
    {
        fprintf(stderr, "Allocation failed\n");
        exit(1);
    }

    for (int i = 0; i < n_points * n_points; i++)
    {
        dist_mat[i] = -1.0;
        time_mat[i] = -1.0;
    }

    rewind(f);
    fgets(line, sizeof(line), f);
    while (fgets(line, sizeof(line), f))
    {
        int o, d;
        double dk, tm;
        if (sscanf(line, "%d,%d,%lf,%lf", &o, &d, &dk, &tm) == 4)
        {
            dist_mat[IDX(o, d)] = dk;
            time_mat[IDX(o, d)] = tm;
        }
    }

    fclose(f);
}

void two_opt_strict(int *perm, int len, int depot)
{
    int improved = 1;
    int max_iter = 500; // limite boucles pour éviter les boucles infinies
    int iter = 0;

    while (improved && iter++ < max_iter)
    {
        improved = 0;
        for (int i = 0; i < len - 1; i++)
        {
            for (int j = i + 1; j < len; j++)
            {
                int a = (i == 0) ? depot : perm[i - 1];
                int b = perm[i];
                int c = perm[j];
                int d = (j + 1 == len) ? depot : perm[j + 1];

                double before = dist_mat[IDX(a, b)] + dist_mat[IDX(c, d)];
                double after = dist_mat[IDX(a, c)] + dist_mat[IDX(b, d)];

                if (after < before)
                {
                    // inversion du segment
                    for (int k = 0; k <= (j - i) / 2; k++)
                    {
                        int tmp = perm[i + k];
                        perm[i + k] = perm[j - k];
                        perm[j - k] = tmp;
                    }
                    improved = 1;
                }
            }
        }
    }
}

double eval_split_distance(int *perm, int len)
{
    int i = 0;
    double total_dist_all = 0.0;

    while (i < len)
    {
        double current_time = 0.0, current_dist = 0.0;
        int start = i, prev = 0;

        while (i < len)
        {
            int next = perm[i];
            double to_next = time_mat[IDX(prev, next)];
            double to_depot = time_mat[IDX(next, 0)];
            double projected_time = current_time + to_next + 3.0 + to_depot;
            if (projected_time > 180.0)
                break;
            current_time += to_next + 3.0;
            current_dist += dist_mat[IDX(prev, next)];
            prev = next;
            i++;
        }

        // copie et optimisation
        int seg_len = i - start;
        int *segment = malloc(seg_len * sizeof(int));
        memcpy(segment, &perm[start], seg_len * sizeof(int));
        two_opt_strict(segment, seg_len, 0);

        // recalcul du cout
        prev = 0;
        double optimized_dist = 0.0;
        for (int j = 0; j < seg_len; j++)
        {
            optimized_dist += dist_mat[IDX(prev, segment[j])];
            prev = segment[j];
        }
        optimized_dist += dist_mat[IDX(prev, 0)];

        total_dist_all += optimized_dist;
        free(segment);
    }

    return total_dist_all;
}

void eval_ind(Individual *ind)
{
    ind->fitness = eval_split_distance(ind->perm, n_points - 1);
}

int cmp_ind(const void *a, const void *b)
{
    double fa = ((Individual *)a)->fitness;
    double fb = ((Individual *)b)->fitness;
    return (fa > fb) - (fa < fb);
}

void two_opt(int *perm, int nc)
{
    int improved = 1;
    int max_iter = 500, iter = 0;
    while (improved && iter++ < max_iter)
    {
        improved = 0;
        for (int i = 0; i < nc - 1; i++)
        {
            for (int j = i + 2; j < nc; j++)
            {
                int A = (i == 0) ? 0 : perm[i - 1];
                int B = perm[i];
                int C = perm[j];
                int D = (j + 1 == nc) ? 0 : perm[j + 1];

                double before = dist_mat[IDX(A, B)] + dist_mat[IDX(C, D)];
                double after = dist_mat[IDX(A, C)] + dist_mat[IDX(B, D)];

                if (after < before)
                {
                    // inversion le segment
                    for (int k = 0; k < (j - i + 1) / 2; k++)
                    {
                        int tmp = perm[i + k];
                        perm[i + k] = perm[j - k];
                        perm[j - k] = tmp;
                    }
                    improved = 1;
                }
            }
        }
    }
}

void advanced_mutation(int *perm, int nc)
{
    int op = rand() % 3;
    int i = rand() % nc, j = rand() % nc;
    if (op == 0)
    {
        int tmp = perm[i];
        perm[i] = perm[j];
        perm[j] = tmp;
    }
    else if (op == 1)
    {
        if (i > j)
        {
            int tmp = i;
            i = j;
            j = tmp;
        }
        while (i < j)
        {
            int tmp = perm[i];
            perm[i++] = perm[j];
            perm[j--] = tmp;
        }
    }
    else
    {
        int val = perm[i];
        if (i < j)
            memmove(&perm[i], &perm[i + 1], (j - i) * sizeof(int));
        else
            memmove(&perm[j + 1], &perm[j], (i - j) * sizeof(int));
        perm[j] = val;
    }
}

Individual run_ga()
{
    int nc = n_points - 1;
    Individual *pop = malloc(POP_SIZE * sizeof(Individual));
    int *base = malloc(nc * sizeof(int));
    for (int i = 0; i < nc; i++)
        base[i] = i + 1;

    for (int i = 0; i < POP_SIZE; i++)
    {
        pop[i].perm = malloc(nc * sizeof(int));
        memcpy(pop[i].perm, base, nc * sizeof(int));
        for (int j = nc - 1; j > 0; j--)
        {
            int k = rand() % (j + 1);
            int tmp = pop[i].perm[j];
            pop[i].perm[j] = pop[i].perm[k];
            pop[i].perm[k] = tmp;
        }
    }

    Individual best = {malloc(nc * sizeof(int)), INFINITY};
    int stagnant = 0;

    for (int gen = 0; gen < GENERATIONS; gen++)
    {
        for (int i = 0; i < POP_SIZE; i++)
            eval_ind(&pop[i]);
        qsort(pop, POP_SIZE, sizeof(Individual), cmp_ind);

        if (pop[0].fitness < best.fitness)
        {
            best.fitness = pop[0].fitness;
            memcpy(best.perm, pop[0].perm, nc * sizeof(int));
            stagnant = 0;
        }
        else if (++stagnant > SKIP_NO_CHANGE)
            break;

        if (gen % 500 == 0)
            printf("Gen %d | Best: %.2f\n", gen, best.fitness);

        Individual *next = malloc(POP_SIZE * sizeof(Individual));
        int elite = POP_SIZE * ELITE_FRAC;
        for (int i = 0; i < elite; i++)
        {
            next[i].perm = malloc(nc * sizeof(int));
            memcpy(next[i].perm, pop[i].perm, nc * sizeof(int));
        }

        int idx = elite;
        while (idx < POP_SIZE)
        {
            Individual *p1 = &pop[rand() % (POP_SIZE / 2)];
            Individual *p2 = &pop[rand() % (POP_SIZE / 2)];
            int a = rand() % nc, b = rand() % nc;
            if (a > b)
            {
                int tmp = a;
                a = b;
                b = tmp;
            }

            int *child = malloc(nc * sizeof(int));
            for (int i = 0; i < nc; i++)
                child[i] = -1;
            for (int i = a; i < b; i++)
                child[i] = p1->perm[i];
            int pos = b;
            for (int i = 0; i < nc; i++)
            {
                int gene = p2->perm[(b + i) % nc];
                int found = 0;
                for (int j = a; j < b; j++)
                    if (child[j] == gene)
                    {
                        found = 1;
                        break;
                    }
                if (!found)
                {
                    while (child[pos % nc] != -1)
                        pos++;
                    child[pos % nc] = gene;
                }
            }
            if ((rand() / (double)RAND_MAX) < MUTATION_RATE)
                advanced_mutation(child, nc);
            two_opt(child, nc);

            next[idx++].perm = child;
        }

        for (int i = 0; i < POP_SIZE; i++)
            free(pop[i].perm);
        free(pop);
        pop = next;
    }

    for (int i = 0; i < POP_SIZE; i++)
        free(pop[i].perm);
    free(pop);
    free(base);
    return best;
}



void split_route(int *perm, int n)
{
    FILE *out = fopen("output.txt", "w");
    if (!out)
    {
        perror("fopen(output.txt)");
        return;
    }

    int i = 0, route_id = 1;
    double total_time_all = 0.0, total_dist_all = 0.0;

    while (i < n)
    {
        double current_time = 0.0, current_dist = 0.0;
        int start = i, prev = 0;

        while (i < n)
        {
            int next = perm[i];
            double to_next = time_mat[IDX(prev, next)];
            double to_depot = time_mat[IDX(next, 0)];
            double projected_time = current_time + to_next + 3.0 + to_depot;
            if (projected_time > 180.0)
                break;
            current_time += to_next + 3.0;
            current_dist += dist_mat[IDX(prev, next)];
            prev = next;
            i++;
        }

        int len = i - start;
        int *segment = malloc(len * sizeof(int));
        memcpy(segment, &perm[start], len * sizeof(int));

        two_opt_strict(segment, len, 0);

        // recalcul du cout apres optim
        current_time = 0.0;
        current_dist = 0.0;
        prev = 0;
        for (int j = 0; j < len; j++)
        {
            current_time += time_mat[IDX(prev, segment[j])] + 3.0;
            current_dist += dist_mat[IDX(prev, segment[j])];
            prev = segment[j];
        }
        current_time += time_mat[IDX(prev, 0)];
        current_dist += dist_mat[IDX(prev, 0)];

        total_time_all += current_time;
        total_dist_all += current_dist;

        // Affichage + output
        fprintf(out, "%d: 0", route_id);
        printf("Truck %d: 0", route_id);
        for (int j = 0; j < len; j++)
        {
            fprintf(out, " -> %d", segment[j]);
            printf(" -> %d", segment[j]);
        }
        fprintf(out, " -> 0 | Distance: %.2f | Time: %.2f\n", current_dist, current_time);
        printf(" -> 0\n    Time: %.2f min | Distance: %.2f km\n", current_time, current_dist);

        route_id++;
        free(segment);
    }
    printf("\nTOTAL: Time = %.2f min | Distance = %.2f km\n", total_time_all, total_dist_all);
    fclose(out);
}

int main(int argc, char **argv)
{
    if (argc < 2)
    {
        fprintf(stderr, "Usage: %s matrix.csv\n", argv[0]);
        return 1;
    }
    srand(time(NULL));
    load_matrix(argv[1]);
    Individual sol = run_ga();
    printf("Best route: [0");
    for (int i = 0; i < n_points - 1; i++)
        printf(" -> %d", sol.perm[i]);
    printf(" -> 0] | Distance = %.2f\n", sol.fitness);
    split_route(sol.perm, n_points - 1);
    free(sol.perm);
    free(dist_mat);
    free(time_mat);
    return 0;
}
