#include <stdio.h>
#include <string.h>

int main() {
  char buffer[10];
  // Buffer overflow vulnerability using gets (very unsafe)
  printf("Enter string: ");
  gets(buffer);
  printf("%s\n", buffer);
  return 0;
}
