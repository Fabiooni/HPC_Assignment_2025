#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <mpi.h>
#include <omp.h>

void local_matmul_add(const float *A, const float *B, float *C, int nloc) {
    #pragma omp parallel for default(none) shared(A, B, C, nloc)
    for (int i = 0; i < nloc; ++i) {
        for (int k = 0; k < nloc; ++k) {
            float aik = A[i * nloc + k];
            #pragma omp simd
            for (int j = 0; j < nloc; ++j) {
                C[i * nloc + j] += aik * B[k * nloc + j];
            }
        }
    }
}

int main(int argc, char *argv[]) {
    int provided;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc < 5) {
        if (rank == 0) fprintf(stderr, "Uso: %s <N> <input_A> <input_B> <output_C>\n", argv[0]);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    int N = atoi(argv[1]);
    char *input_file1 = argv[2];
    char *input_file2 = argv[3];
    char *output_file = argv[4];

    int q = (int)floor(sqrt((double)size));
    if (q * q != size || N % q != 0) {
        if (rank == 0) fprintf(stderr, "Errore: check parametri (N=%d, Proc=%d)\n", N, size);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    int nloc = N / q;
    int dims[2] = {q, q}, periods[2] = {1, 1}, coords[2];
    MPI_Comm cart_comm;
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 1, &cart_comm);
    MPI_Cart_coords(cart_comm, rank, 2, coords);

    float *A_local = malloc(nloc * nloc * sizeof(float));
    float *B_local = malloc(nloc * nloc * sizeof(float));
    float *A_next  = malloc(nloc * nloc * sizeof(float));
    float *B_next  = malloc(nloc * nloc * sizeof(float));
    float *C_local = calloc(nloc * nloc, sizeof(float));

    // --- AGGIUNTA: Array di stati per evitare il warning/crash ---
    MPI_Status stats[4]; 

    float *sendA = NULL, *sendB = NULL;
    int *sendcounts = NULL, *displs = NULL;

    if (rank == 0) {
        float *A = malloc(N * N * sizeof(float));
        float *B = malloc(N * N * sizeof(float));
        sendA = malloc(size * nloc * nloc * sizeof(float));
        sendB = malloc(size * nloc * nloc * sizeof(float));
        sendcounts = malloc(size * sizeof(int));
        displs = malloc(size * sizeof(int));

        FILE *f1 = fopen(input_file1, "r");
        if(f1) { for (int i = 0; i < N * N; ++i) fscanf(f1, "%f,", &A[i]); fclose(f1); }

        FILE *f2 = fopen(input_file2, "r");
        if(f2) { for (int i = 0; i < N * N; ++i) fscanf(f2, "%f,", &B[i]); fclose(f2); }

        for (int pi = 0; pi < q; ++pi) {
            for (int pj = 0; pj < q; ++pj) {
                int dest_rank;
                int coords_tmp[2] = {pi, pj};
                MPI_Cart_rank(cart_comm, coords_tmp, &dest_rank);
                sendcounts[dest_rank] = nloc * nloc;
                displs[dest_rank] = dest_rank * nloc * nloc;
                float *blockA = sendA + dest_rank * nloc * nloc;
                float *blockB = sendB + dest_rank * nloc * nloc;
                for (int i = 0; i < nloc; ++i) {
                    for (int j = 0; j < nloc; ++j) {
                        blockA[i * nloc + j] = A[(pi * nloc + i) * N + (pj * nloc + j)];
                        blockB[i * nloc + j] = B[(pi * nloc + i) * N + (pj * nloc + j)];
                    }
                }
            }
        }
        free(A); free(B);
    }

    MPI_Scatterv(sendA, sendcounts, displs, MPI_FLOAT, A_local, nloc * nloc, MPI_FLOAT, 0, cart_comm);
    MPI_Scatterv(sendB, sendcounts, displs, MPI_FLOAT, B_local, nloc * nloc, MPI_FLOAT, 0, cart_comm);

    if (rank == 0) { free(sendA); free(sendB); }

    MPI_Barrier(cart_comm);
    double start_time = MPI_Wtime();

    int srcA, dstA, srcB, dstB;
    MPI_Cart_shift(cart_comm, 1, -coords[0], &srcA, &dstA);
    MPI_Cart_shift(cart_comm, 0, -coords[1], &srcB, &dstB);

    MPI_Request reqs[4];
    MPI_Irecv(A_next, nloc * nloc, MPI_FLOAT, srcA, 0, cart_comm, &reqs[0]);
    MPI_Isend(A_local, nloc * nloc, MPI_FLOAT, dstA, 0, cart_comm, &reqs[1]);
    MPI_Irecv(B_next, nloc * nloc, MPI_FLOAT, srcB, 1, cart_comm, &reqs[2]);
    MPI_Isend(B_local, nloc * nloc, MPI_FLOAT, dstB, 1, cart_comm, &reqs[3]);

    // USARE stats INVECE DI IGNORE
    MPI_Waitall(4, reqs, stats);

    float *tmpA = A_local; A_local = A_next; A_next = tmpA;
    float *tmpB = B_local; B_local = B_next; B_next = tmpB;

    MPI_Cart_shift(cart_comm, 1, 1, &srcA, &dstA);
    MPI_Cart_shift(cart_comm, 0, 1, &srcB, &dstB);

    for (int step = 0; step < q; ++step) {
        MPI_Request move_reqs[4];
        if (step < q - 1) {
            MPI_Irecv(A_next, nloc * nloc, MPI_FLOAT, srcA, 10, cart_comm, &move_reqs[0]);
            MPI_Irecv(B_next, nloc * nloc, MPI_FLOAT, srcB, 20, cart_comm, &move_reqs[1]);
            MPI_Isend(A_local, nloc * nloc, MPI_FLOAT, dstA, 10, cart_comm, &move_reqs[2]);
            MPI_Isend(B_local, nloc * nloc, MPI_FLOAT, dstB, 20, cart_comm, &move_reqs[3]);
        }

        local_matmul_add(A_local, B_local, C_local, nloc);

        if (step < q - 1) {
            // USARE stats INVECE DI IGNORE
            MPI_Waitall(4, move_reqs, stats);
            float *tA = A_local; A_local = A_next; A_next = tA;
            float *tB = B_local; B_local = B_next; B_next = tB;
        }
    }

    MPI_Barrier(cart_comm);
    double end_time = MPI_Wtime();

    float *recvC = NULL;
    if (rank == 0) recvC = malloc(size * nloc * nloc * sizeof(float));

    MPI_Gatherv(C_local, nloc * nloc, MPI_FLOAT, recvC, sendcounts, displs, MPI_FLOAT, 0, cart_comm);

    if (rank == 0) {
        printf("Tempo di esecuzione: %f secondi\n", end_time - start_time);
        FILE *fout = fopen(output_file, "w");
        if(fout) {
            for (int pi = 0; pi < q; ++pi) {
                for (int i = 0; i < nloc; ++i) {
                    for (int pj = 0; pj < q; ++pj) {
                        int src_rank;
                        int coords_tmp[2] = {pi, pj};
                        MPI_Cart_rank(cart_comm, coords_tmp, &src_rank);
                        float *block = recvC + src_rank * nloc * nloc;
                        for (int j = 0; j < nloc; ++j) fprintf(fout, "%.6f,", block[i * nloc + j]);
                    }
                    fprintf(fout, "\n");
                }
            }
            fclose(fout);
        }
        free(recvC); if(sendcounts) free(sendcounts); if(displs) free(displs);
    }

    free(A_local); free(B_local); free(C_local); free(A_next); free(B_next);
    MPI_Comm_free(&cart_comm);
    MPI_Finalize();
    return 0;
}
