#define OPENSSL_SUPPRESS_DEPRECATED
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <openssl/sha.h>

#define ITERS 2000000

// Shared thread pool variables
pthread_mutex_t queue_mutex = PTHREAD_MUTEX_INITIALIZER;
int next_file_index = 0;
int total_files = 0;
char** file_paths = NULL;
unsigned long* results = NULL;

unsigned long stretch_hash(const char* path) {
    FILE* f = fopen(path, "r");
    if (!f) {
        perror("Error opening file");
        return 0;
    }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    unsigned char* buf = malloc(sz);
    if (!buf) {
        fclose(f);
        return 0;
    }
    fread(buf, 1, sz, f);
    fclose(f);

    unsigned char digest[32];
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    SHA256_Update(&ctx, buf, sz);
    SHA256_Final(digest, &ctx);
    free(buf);

    for (int i = 0; i < ITERS; i++) {
        SHA256_Init(&ctx);
        SHA256_Update(&ctx, digest, 32);
        SHA256_Final(digest, &ctx);
    }

    unsigned long sum = 0;
    for (int i = 0; i < 32; i++) sum += digest[i];
    return sum;
}

void* worker_routine(void* arg) {
    while (1) {
        int current_idx = -1;
        
        pthread_mutex_lock(&queue_mutex);
        if (next_file_index < total_files) {
            current_idx = next_file_index;
            next_file_index++;
        }
        pthread_mutex_unlock(&queue_mutex);

        if (current_idx == -1) {
            break; // No more files to process
        }

        results[current_idx] = stretch_hash(file_paths[current_idx]);
    }
    return NULL;
}

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <num_threads> <file1> [file2 ...]\n", argv[0]);
        return 1;
    }

    int num_threads = atoi(argv[1]);
    if (num_threads < 1) num_threads = 1;

    total_files = argc - 2;
    file_paths = &argv[2];
    results = calloc(total_files, sizeof(unsigned long));

    printf("Processing %d files using %d threads...\n", total_files, num_threads);

    pthread_t* threads = malloc(num_threads * sizeof(pthread_t));
    for (int i = 0; i < num_threads; i++) {
        pthread_create(&threads[i], NULL, worker_routine, NULL);
    }

    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("\n=== Results ===\n");
    for (int i = 0; i < total_files; i++) {
        printf("File: %s -> Hash Sum: %lu\n", file_paths[i], results[i]);
    }

    free(results);
    free(threads);
    return 0;
}
