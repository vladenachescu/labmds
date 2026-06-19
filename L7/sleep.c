#include <stdio.h>
#include <pthread.h>

#ifdef _WIN32
#include <windows.h>
#define sleep(x) Sleep((x) * 1000)
#else
#include <unistd.h>
#endif

void* thread_routine(void* arg) {
    int id = *(int*)arg;
    printf("thread %d: going to sleep\n", id);
    sleep(2);
    printf("thread %d: woke up\n", id);
    return NULL;
}

int main(void) {
    pthread_t threads[4];
    int ids[4] = {1, 2, 3, 4};
    for (int i = 0; i < 4; i++) {
        pthread_create(&threads[i], NULL, thread_routine, &ids[i]);
    }
    for (int i = 0; i < 4; i++) {
        pthread_join(threads[i], NULL);
    }
    printf("all threads done\n");
    return 0;
}
