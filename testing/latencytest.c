#include "mbed.h"

Serial bluetooth(PTE22,PTE23);

int main() {
	while (1) {
		if (bluetooth.readable()) {
			bluetooth.printf("%c\n", bluetooth.getc());
		}
	}
}