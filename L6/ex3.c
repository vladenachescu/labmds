#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char* name;
    int*  grades;
    int   count;
} Student;

Student* new_student(const char* name, int grades[], int n) {
    Student* s = malloc(sizeof(Student));
    if (!s) return NULL;
    
    // Bug 1 Fix: allocate strlen(name) + 1 for null terminator
    s->name = malloc(strlen(name) + 1);
    if (s->name) {
        strcpy(s->name, name);
    }
    
    s->grades = malloc(n * sizeof(int));
    if (s->grades) {
        memcpy(s->grades, grades, n * sizeof(int));
    }
    s->count = n;
    return s;
}

float average(Student* s) {
    int sum = 0;
    // Bug 2 Fix: index must be strictly less than s->count
    for (int i = 0; i < s->count; i++) {  
        sum += s->grades[i];
    }
    return (float)sum / s->count;
}

void free_student(Student* s) {
    if (s) {
        free(s->name);
        // Bug 3 Fix: free the allocated grades array
        free(s->grades);
        free(s);
    }
}

int main() {
    int grades[] = {85, 90, 78, 92};
    Student* alice = new_student("Alice", grades, 4);
    if (alice) {
        printf("%s: avg = %.1f\n", alice->name, average(alice));
        free_student(alice);
    }
    return 0;
}
