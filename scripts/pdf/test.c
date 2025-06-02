#include <stdio.h>

int main() {
    int tab[3][13] = {
        {0, 3, 11, 26, 9, 6, 12, 25, 4, 8, 0},
        {0, 2, 13, 5, 7, 10, 14, 3, 6, 4, 19, 0},
        {0, 1, 28, 8, 4, 14, 2, 3, 5, 9, 16, 18, 0},
    };

    printf("[\n");
    for (int i = 0; i < 3; i++) {
        printf("  [");
        for (int j = 0; j < 13; j++) {
            printf("%d", tab[i][j]);
            if (j < 12) printf(", ");
        }
        printf("]");
        if (i < 2) printf(",\n");
    }
    printf("\n]\n");

    return 0;
}
