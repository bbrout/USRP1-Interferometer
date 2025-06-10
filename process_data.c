#include <stdio.h>
#include <stdlib.h>
#include <complex.h>
#include <math.h>
#include <fftw3.h>

#define BLOCK_FLOATS 1024       // input floats per block (I1,Q1,I2,Q2,...)
#define BLOCK_COMPLEX 512       // input complex samples per block (I,Q pairs)
#define OUT_COMPLEX 256         // output complex after multiply
#define INTEGRATION_TIME 4      // integration time in seconds
#define BLOCKS_PER_SECOND 3906
#define BLOCKS_PER_CHUNK (BLOCKS_PER_SECOND * INTEGRATION_TIME)
#define SAMPLE_RATE 2.0e6	// sample rate, same as in Start_Observation.py

int main() {
    FILE *fin = fopen("RX_AB.dat", "rb");
    if (!fin) {
        perror("Failed to open input file");
        return 1;
    }

    // Open freq.dat and read frequency in Hz
    FILE *f_freq = fopen("freq.dat", "r");
    if (!f_freq) {
        perror("Failed to open freq.dat");
        fclose(fin);
        return 1;
    }
    double freq_hz;
    if (fscanf(f_freq, "%lf", &freq_hz) != 1) {
        fprintf(stderr, "Failed to read frequency from freq.dat\n");
        fclose(f_freq);
        fclose(fin);
        return 1;
    }
    fclose(f_freq);

    // Write FFT frequency header
    double central_freq = freq_hz;
    double delta_f = (SAMPLE_RATE / OUT_COMPLEX)/1e6; // MHz per bin

    // Buffers
    float *inbuf = malloc(BLOCK_FLOATS * sizeof(float));
    float complex *z = malloc(OUT_COMPLEX * sizeof(float complex));
    float *fft_accum = calloc(OUT_COMPLEX, sizeof(float)); // Accumulate power spectrum
    fftwf_complex *in = fftwf_malloc(sizeof(fftwf_complex) * OUT_COMPLEX);
    fftwf_complex *out = fftwf_malloc(sizeof(fftwf_complex) * OUT_COMPLEX);
    fftwf_plan p = fftwf_plan_dft_1d(OUT_COMPLEX, in, out, FFTW_FORWARD, FFTW_ESTIMATE);

    if (!inbuf || !z || !fft_accum || !in || !out) {
        fprintf(stderr, "Memory allocation failed\n");
        fclose(fin);
        return 1;
    }

    FILE *fp_power = fopen("power.dat", "w");
    FILE *fp_fft = fopen("fft.dat", "w");

    if (!fp_power || !fp_fft) {
        perror("Failed to open output files");
        return 1;
    }

    // Write header for FFT file
    fprintf(fp_fft, "time");
    for (int i = 0; i < OUT_COMPLEX; i++) {
	double freq = central_freq + (i - OUT_COMPLEX / 2) * delta_f;
        fprintf(fp_fft, ",%.6f", freq);
    }
    fprintf(fp_fft, "\n");

    size_t read_count;
    double sum_power = 0.0;
    int block_count = 0;
    float time = 0.0;

    while ((read_count = fread(inbuf, sizeof(float), BLOCK_FLOATS, fin)) == BLOCK_FLOATS) {
        // Construct z[i] = A[i] * conj(B[i])
        for (int i = 0; i < OUT_COMPLEX; i++) {
            float complex a = inbuf[2 * i] + I * inbuf[2 * i + 1];
            float complex b = inbuf[2 * (i + OUT_COMPLEX)] + I * inbuf[2 * (i + OUT_COMPLEX) + 1];
            z[i] = a * conjf(b);
        }

        // Accumulate power and FFT
        for (int i = 0; i < OUT_COMPLEX; i++) {
            float re = crealf(z[i]);
            float im = cimagf(z[i]);
            sum_power += re * re + im * im;
            in[i] = z[i];  // load FFT input
        }

        fftwf_execute(p);  // in[] -> out[]

        for (int i = 0; i < OUT_COMPLEX; i++) {
            float re = crealf(out[i]);
            float im = cimagf(out[i]);
            fft_accum[i] += re * re + im * im;
        }

        block_count++;

        if (block_count == BLOCKS_PER_CHUNK) {
            time += INTEGRATION_TIME;

            // Write power
            double avg_power = sqrt(sum_power / (OUT_COMPLEX * block_count));
            fprintf(fp_power, "%.2f %.8f\n", time, avg_power);

            // Write FFT spectrum
            fprintf(fp_fft, "%.2f", time);
            for (int i = 0; i < OUT_COMPLEX; i++) {
                double avg_fft = sqrt(fft_accum[i] / block_count);
                fprintf(fp_fft, ",%.8f", avg_fft);
                fft_accum[i] = 0.0f;
            }
            fprintf(fp_fft, "\n");


fprintf(stderr, "Written line with %d bins at time %.2f\n", OUT_COMPLEX, time);


            // Reset accumulators
            sum_power = 0.0;
            block_count = 0;
        }
    }

    // Clean up
    fclose(fin);
    fclose(fp_power);
    fclose(fp_fft);
    free(inbuf);
    free(z);
    free(fft_accum);
    fftwf_destroy_plan(p);
    fftwf_free(in);
    fftwf_free(out);

    return 0;
}

