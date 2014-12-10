#include <iostream>


int main(){
 char input = 6;
 char bitmask = 0x08;
 bool forward = ((input & bitmask) == 0);
 std::cout << forward << "\n";
 return 0;
}


