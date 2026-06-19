#include <stdio.h>
#include <pthread.h>
#include <stdatomic.h>

#define ITERATIONS 100000

// Using C11 atomic variable to resolve the data race
atomic_int counter = 0;

void* increment_routine(void* arg) {
    for (int i = 0; i < ITERATIONS; i++) {
        counter++;
    }
    return NULL;
}

int main(void) {
    pthread_t thread1, thread2;

    pthread_create(&thread1, NULL, increment_routine, NULL);
    pthread_create(&thread2, NULL, increment_routine, NULL);

    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);

    printf("Final counter value (with stdatomic): %d\n", counter);
    printf("Expected value: %d\n", ITERATIONS * 2);

    return 0;
}
