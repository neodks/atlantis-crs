#include <cstdlib>
#include <iostream>

int main() { // Command injection vulnerability
  char cmd[100];
  std::cout << "Enter command: ";
  std::cin >> cmd;
  system(cmd);

  int *ptr = new int(10);
  delete ptr;
  // Use-after-free vulnerability
  std::cout << "Value after delete: " << *ptr << std::endl;

  return 0;
}
