#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Uso: %s <dimensione_N> <nome_file>\n", argv[0]);
        return 1;
    }

    int N = atoi(argv[1]);
    char *filename = argv[2];

    if (N <= 0) {
        fprintf(stderr, "Error: N grt 0.\n");
        return 1;
    }

    FILE *f = fopen(filename, "w");
    if (f == NULL) {
        perror("Error");
        return 1;
    }

    srand(time(NULL));

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            float valore = ((float)rand() / (float)(RAND_MAX)) * 100.0f;
            fprintf(f, "%.6f,", valore);
        }
        fprintf(f, "\n");
    }

    fclose(f);
    return 0;
}
