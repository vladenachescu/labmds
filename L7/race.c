#include <stdio.h>
#include <pthread.h>

#define ITERATIONS 100000

int counter = 0;

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

    printf("Final counter value (with race): %d\n", counter);
    printf("Expected value: %d\n", ITERATIONS * 2);

    return 0;
}
