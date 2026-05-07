#define _CRT_SECURE_NO_WARNINGS // Disabilita l'errore MSVC C4996 su localtime()

#include <opencv2/opencv.hpp>
#include <cuda_runtime.h>
#include <iostream>
#include <fstream>
#include <string>
#include <ctime>

using namespace cv;
using namespace std;

// --- MATRICE COSTANTE W ---
__constant__ float d_W[9] = {
    1.0f/16.0f, 2.0f/16.0f, 1.0f/16.0f,
    2.0f/16.0f, 4.0f/16.0f, 2.0f/16.0f,
    1.0f/16.0f, 2.0f/16.0f, 1.0f/16.0f
};

// --- KERNEL GAUSSIANO (W) CONDIVISO ---
__global__ void gaussianFilterFixed(const unsigned char* input, unsigned char* output, int width, int height) {
    __shared__ unsigned char s_data[34][34];

    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;

    int tx = threadIdx.x;
    int ty = threadIdx.y;
    int bw = blockDim.x;
    int bh = blockDim.y;

    int g_x = min(max(x, 0), width - 1);
    int g_y = min(max(y, 0), height - 1);

    s_data[ty + 1][tx + 1] = input[g_y * width + g_x];

    if (tx == 0)      s_data[ty + 1][0]      = input[g_y * width + min(max(x - 1, 0), width - 1)];
    if (tx == bw - 1) s_data[ty + 1][bw + 1] = input[g_y * width + min(max(x + 1, 0), width - 1)];
    if (ty == 0)      s_data[0][tx + 1]      = input[min(max(y - 1, 0), height - 1) * width + g_x];
    if (ty == bh - 1) s_data[bh + 1][tx + 1] = input[min(max(y + 1, 0), height - 1) * width + g_x];

    if (tx == 0 && ty == 0)           s_data[0][0]           = input[min(max(y - 1, 0), height - 1) * width + min(max(x - 1, 0), width - 1)];
    if (tx == bw - 1 && ty == 0)      s_data[0][bw + 1]      = input[min(max(y - 1, 0), height - 1) * width + min(max(x + 1, 0), width - 1)];
    if (tx == 0 && ty == bh - 1)      s_data[bh + 1][0]      = input[min(max(y + 1, 0), height - 1) * width + min(max(x - 1, 0), width - 1)];
    if (tx == bw - 1 && ty == bh - 1) s_data[bh + 1][bw + 1] = input[min(max(y + 1, 0), height - 1) * width + min(max(x + 1, 0), width - 1)];

    __syncthreads();

    if (x < width && y < height) {
        float sum = 0.0f;
        sum += s_data[ty][tx]     * d_W[0]; sum += s_data[ty][tx+1]   * d_W[1]; sum += s_data[ty][tx+2]   * d_W[2];
        sum += s_data[ty+1][tx]   * d_W[3]; sum += s_data[ty+1][tx+1] * d_W[4]; sum += s_data[ty+1][tx+2] * d_W[5];
        sum += s_data[ty+2][tx]   * d_W[6]; sum += s_data[ty+2][tx+1] * d_W[7]; sum += s_data[ty+2][tx+2] * d_W[8];
        output[y * width + x] = static_cast<unsigned char>(sum);
    }
}

// --- KERNEL MEDIANO CONDIVISO ---
__global__ void medianFilterFixed(const unsigned char* input, unsigned char* output, int width, int height) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;

    if (x >= width || y >= height) return;

    unsigned char values[9];
    int count = 0;

    #pragma unroll
    for (int ky = -1; ky <= 1; ky++) {
        #pragma unroll
        for (int kx = -1; kx <= 1; kx++) {
            int nx = min(max(x + kx, 0), width - 1);
            int ny = min(max(y + ky, 0), height - 1);
            values[count++] = input[ny * width + nx];
        }
    }

    #pragma unroll
    for (int i = 0; i < 8; i++) {
        #pragma unroll
        for (int j = 0; j < 8 - i; j++) {
            if (values[j] > values[j + 1]) {
                unsigned char tmp = values[j];
                values[j] = values[j + 1];
                values[j + 1] = tmp;
            }
        }
    }
    output[y * width + x] = values[4];
}

void printHelp() {
    cout << "Usage: ./filter <noisy_image> <clean_image> <gaussian|median> <block size: 8|16|32> <iterations> <save_output: 0|1>" << endl;
}

int main(int argc, char* argv[]) {
    if (argc < 7) {
        printHelp();
        return 1;
    }

    string noisyFile = argv[1];
    string cleanFile = argv[2];
    string filterType = argv[3];
    int blockSize = stoi(argv[4]);
    int iterations = stoi(argv[5]);
    int saveOutput = stoi(argv[6]);

    if (blockSize > 32) {
        cerr << "Error: Block size must be <= 32." << endl;
        return 1;
    }

    // --- ESTRAZIONE NOME FILE ---
    size_t lastSlash = noisyFile.find_last_of("/\\");
    string nameWithExt = (lastSlash != string::npos) ? noisyFile.substr(lastSlash + 1) : noisyFile;
    size_t lastDot = nameWithExt.find_last_of(".");
    string baseName = (lastDot != string::npos) ? nameWithExt.substr(0, lastDot) : nameWithExt;

    // --- CARICAMENTO IMMAGINI ---
    Mat image = imread(noisyFile, IMREAD_COLOR);
    Mat cleanImage = imread(cleanFile, IMREAD_COLOR); // Ground truth per PSNR

    if (image.empty()) {
        cerr << "Error: Could not load noisy image." << endl;
        return 1;
    }

    vector<Mat> channels;
    split(image, channels);

    int width = image.cols;
    int height = image.rows;
    size_t imgSize = width * height * sizeof(unsigned char);

    dim3 block(blockSize, blockSize);
    dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);

    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);
    cudaEventRecord(start);

    for (int c = 0; c < 3; c++) {
        unsigned char *d_input, *d_output;
        cudaMalloc(&d_input, imgSize);
        cudaMalloc(&d_output, imgSize);
        cudaMemcpy(d_input, channels[c].data, imgSize, cudaMemcpyHostToDevice);

        for (int i = 0; i < iterations; i++) {
            if (filterType == "gaussian") {
                gaussianFilterFixed<<<grid, block>>>(d_input, d_output, width, height);
            } else if (filterType == "median") {
                medianFilterFixed<<<grid, block>>>(d_input, d_output, width, height);
            }
            cudaDeviceSynchronize();
            
            if (iterations > 1 && i < iterations - 1) {
                cudaMemcpy(d_input, d_output, imgSize, cudaMemcpyDeviceToDevice);
            }
        }

        cudaMemcpy(channels[c].data, d_output, imgSize, cudaMemcpyDeviceToHost);
        cudaFree(d_input);
        cudaFree(d_output);
    }

    cudaEventRecord(stop);
    cudaEventSynchronize(stop);
    float ms;
    cudaEventElapsedTime(&ms, start, stop);

    // --- RICOSTRUZIONE IMMAGINE ---
    Mat outputImg;
    merge(channels, outputImg);

    // --- CALCOLO PSNR CON OPENCV ---
    double psnr_value = 0.0;
    if (!cleanImage.empty() && cleanImage.size() == outputImg.size()) {
        psnr_value = PSNR(cleanImage, outputImg);
    } else {
        cerr << "Warning: Clean image not found or size mismatch. PSNR set to 0." << endl;
    }

    // --- SALVATAGGIO IMMAGINE (Solo se flag = 1) ---
    if (saveOutput == 1) {
        // Formato richiesto: ad esempio 4K_50_32_out.png
        string outputName = baseName + "_" + to_string(blockSize) + "_out.png";
        imwrite(outputName, outputImg);
        cout << "Saved result to: " << outputName << endl;
    }

    // --- SALVATAGGIO LOG CSV ---
    time_t now = time(0);
    tm *ltm = localtime(&now);
    char timestamp[32];
    strftime(timestamp, sizeof(timestamp), "%Y%m%d_%H%M%S", ltm);

    // Nuova struttura CSV: Filename, Time_ms, PSNR_dB, Filter, BlockSize, Kernel, Iterations, Timestamp
    ofstream csv("execution_times.csv", ios::app);
    csv << baseName << "," << ms << "," << psnr_value << "," << filterType << "," << blockSize << ",3," << iterations << "," << timestamp << "\n";
    csv.close();

    cout << "Execution time: " << ms << " ms | PSNR: " << psnr_value << " dB" << endl;
    return 0;
}
