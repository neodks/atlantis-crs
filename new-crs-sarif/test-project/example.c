#include <stdio.h>
#include <string.h>

int main() {
    char buffer[10];
    // 잠재적 버퍼 오버플로우
    strcpy(buffer, "This is a very long string");
    printf("%s\n", buffer);
    return 0;
}
