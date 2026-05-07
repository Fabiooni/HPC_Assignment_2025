#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <math.h>

#define ABS_EPS 0.001  // threshold di convergenza 

void dif(float** In, float** Out, float Wx, float Wy, int dimx, int dimy, float* max_diff) // defines the diffusion model and handles also boundary condition for boundary cells
{
    int i, j;
    float local_max = 0.0f;

    #pragma omp parallel for collapse(2) reduction(max:local_max)
    for (i = 0; i < dimx; i++) {
        for (j = 0; j < dimy; j++) {

            float old = In[i][j];
            float newval;

            if (i==0 || i==dimx-1 || j==0 || j==dimy-1) {
                float sum = 0.0f;
                float coeff = 1.0f;

                if (j > 0) { sum += Wx * In[i][j-1]; coeff -= Wx; }
                if (j < dimy-1) { sum += Wx * In[i][j+1]; coeff -= Wx; }
                if (i > 0) { sum += Wy * In[i-1][j]; coeff -= Wy; }
                if (i < dimx-1) { sum += Wy * In[i+1][j]; coeff -= Wy; }

                newval = coeff*old + sum;
            } else {
                float coeff = 1.0f - 2.0f * (Wx + Wy);
                newval = coeff*old +
                         Wx * (In[i][j-1] + In[i][j+1]) +
                         Wy * (In[i-1][j] + In[i+1][j]);
            }

            Out[i][j] = newval;

            float diff = fabsf(newval - old);
            if (diff > local_max) local_max = diff;
        }
    }

    *max_diff = local_max;
}

void save_snapshot(float** In, int dimx, int dimy, int t) // function used to save snapshots images during the diffusion simulation
{
    char fname[256];
    sprintf(fname, "snapshot_%d.txt", t);
    FILE* f = fopen(fname, "w");
    for(int i=0;i<dimx;i++){
        for(int j=0;j<dimy;j++) fprintf(f, "%.6f ", In[i][j]);
        fprintf(f, "\n");
    }
    fclose(f);
    printf("Snapshot saved at iteration %d\n", t);
}

int main(int argc, char* argv[])
{
    if (argc != 8) {
        printf("Usage: %s input_file output_file dimx dimy Wx Wy T\n", argv[0]); //arises error if variables are not given correctly
        return 1;
    }

    char* input_file = argv[1];
    char* output_file = argv[2];
    int dimx = atoi(argv[3]);
    int dimy = atoi(argv[4]);
    float Wx = atof(argv[5]);
    float Wy = atof(argv[6]);
    int T = atoi(argv[7]);

    float** In = malloc(dimx * sizeof(float*));
    float** Out = malloc(dimx * sizeof(float*));
    float** In_orig = malloc(dimx * sizeof(float*));
    for (int i = 0; i < dimx; i++) {
        In[i] = malloc(dimy * sizeof(float));
        Out[i] = malloc(dimy * sizeof(float));
        In_orig[i] = malloc(dimy * sizeof(float));
    }

    FILE* fin = fopen(input_file, "r");
    for (int i=0;i<dimx;i++)
        for(int j=0;j<dimy;j++){
            fscanf(fin, "%f", &In[i][j]);
            In_orig[i][j] = In[i][j];
        }
    fclose(fin);

    printf("Simulation started: %dx%d matrix, Wx=%.3f, Wy=%.3f, max it=%d\n",
           dimx, dimy, Wx, Wy, T);

    int sample_period = 1000; // every sample_period iteration a snapshot is taken
    float max_diff;
    float** Mom;

    // ----------- SNAPSHOT RUN to be enabled-----------
    /*omp_set_num_threads(4);
    printf("\n[Snapshot Run] Using 4 thread\n");

    for(int i=0;i<dimx;i++)
        for(int j=0;j<dimy;j++)
            In[i][j] = In_orig[i][j];

    for (int t = 0; t < T; t++) {
        dif(In, Out, Wx, Wy, dimx, dimy, &max_diff);
        Mom = In; In = Out; Out = Mom;

        if (t % sample_period == 0) save_snapshot(In, dimx, dimy, t);
        if (max_diff < ABS_EPS) {
            printf("Converged at iteration %d (max diff=%.8f)\n", t, max_diff);
            break;
        }
    }*/

    // ------------- PERFORMANCE RUNS -------------
    int thread_counts[] = {1,2,4,8,16,32};
    int n_tests = 6;

    for (int test=0; test<n_tests; test++) {
        int nthreads = thread_counts[test];
        omp_set_num_threads(nthreads);
        printf("\n[Perf Run] %d threads\n", nthreads);

        for(int i=0;i<dimx;i++)
            for(int j=0;j<dimy;j++)
                In[i][j] = In_orig[i][j];

        double start = omp_get_wtime();
        int converged_iter = -1;
        for (int t = 0; t < T; t++) {
            dif(In, Out, Wx, Wy, dimx, dimy, &max_diff);
            Mom = In; In = Out; Out = Mom;

            if (max_diff < ABS_EPS){
              converged_iter = t;
              break;
          }
        }
        double end = omp_get_wtime();
        if (converged_iter >= 0)
          printf("Converged at iteration %d (max diff=%.8f)\n", converged_iter, max_diff);
        printf("Runtime: %.6f seconds (converged diff %.8f)\n", end-start, max_diff);
    }

    FILE* fout = fopen(output_file, "w");
    for (int i = 0; i < dimx; i++) {
        for (int j = 0; j < dimy; j++) fprintf(fout, "%.6f ", In[i][j]);
        fprintf(fout, "\n");
    }
    fclose(fout);

    for (int i=0;i<dimx;i++){ free(In[i]); free(Out[i]); free(In_orig[i]); }
    free(In); free(Out); free(In_orig);

    printf("\nSimulation completed\n");
    return 0;
}
