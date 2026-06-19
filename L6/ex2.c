#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int* data;
    int size;
    int capacity;
} Vec;

Vec* vec_new(int capacity) {
    Vec* v = malloc(sizeof(Vec));
    v->data = malloc(capacity * sizeof(int));
    v->size = 0;
    v->capacity = capacity;
    return v;
}

void vec_push(Vec* v, int value) {
    if (v->size == v->capacity) {
        v->capacity *= 2;
        // Use realloc to grow the memory dynamically
        int* new_data = realloc(v->data, v->capacity * sizeof(int));
        if (!new_data) {
            fprintf(stderr, "Out of memory\n");
            exit(1);
        }
        v->data = new_data;
    }
    v->data[v->size++] = value;
}

void vec_free(Vec* v) {
    free(v->data);
    free(v);
}

int main() {
    Vec* scores = vec_new(2);
    vec_push(scores, 85);
    vec_push(scores, 92);

    // Storing the index instead of a raw pointer to avoid dangling pointer on reallocation
    int top_score_index = 1;

    vec_push(scores, 78);
    vec_push(scores, 95);
    vec_push(scores, 61);

    printf("Top score was: %d\n", scores->data[top_score_index]);

    vec_free(scores);
    return 0;
}
