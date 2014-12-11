#include "main_copy.h"

Serial bluetooth(PTE22,PTE23);
Serial device(D14, D15);

DigitalOut blue(LED3);
DigitalOut green(LED2);
DigitalOut red(LED1);

static bool ready = false;

int main() {
    wait(5);
    device.baud(57600);
    bluetooth.baud(115200);
    start();
    bluetooth.attach(&read_bluetooth);

    while(1) {
        // bluetooth.printf("%d", 0);
        // while (!ready) {
        //     wait(.01);
        // }
        // ready = false;
        execute_statechart(init, drive, gameOver, currSpeed, directionForward, &device);
        // bluetooth.printf("%d", 1);
        // wait(.01);
     }
}

void read_bluetooth() {
    saveVarsToTemp();
    while (bluetooth.readable()){
        bluetooth_byte = bluetooth.getc();
        ready = true;
        switch (bluetooth_byte_count) {
            // get OpCode
            case 0:
                if (bluetooth_byte == Initialize) {
                    init = true;
                    drive = gameOver = false;
                } else if (bluetooth_byte == IsGameOver) {
                    gameOver = true;
                    init = drive = false;
                    bluetooth_byte_count++;
                    green=1;
                    red=1;
                    blue=0;
                } else {
                    drive = true;
                    init = gameOver = false;
                    bluetooth_byte_count++;
                    checksum += bluetooth_byte;
                }
                break;
            // get Drive id
            case 1: 
                if (bluetooth_byte == DriveID) {
                    bluetooth_byte_count++;
                    checksum += bluetooth_byte;
                }
                break;
            // get Drive data
            case 2: 
                directionForward = getDriveDirection(bluetooth_byte);
                if(directionForward){
                    green=0;
                    red=1;
                    blue=1;
                }else{
                    red=0;
                    green=1;
                    blue=1;
                }
                currSpeed = getSpeed(bluetooth_byte);
                checksum += bluetooth_byte;
                bluetooth_byte_count++;
                break;
            // get checksum
            case 3:
                checksum += bluetooth_byte;
                if ((checksum & 0xFF) != 0) {
                    restoreVarsToTemp();
                }
                bluetooth_byte_count = 0;
                break;                
        }
    }
    return;
}

void start() {
    device.printf("%c%c",Start,SafeMode);
    wait(1);
    device.printf("%c%c%c",SensorStream,char(1),Distance);
    wait(0.6);
}

bool getDriveDirection(char input) {
    char bitmask = 0x08;
    bool forward = ((input & bitmask) == 0);
    return forward;
}

int getSpeed(char input) {
    input = 0x07 & input;
    int speed = 50 * input;
    return speed;
}

void saveVarsToTemp() {
    initTemp = init;
    driveTemp = drive;
    gameOverTemp = gameOver;
    directionForwardTemp = directionForward;
    currSpeedTemp = currSpeed;
}

void restoreVarsToTemp() {
    init = initTemp;
    drive = driveTemp;
    gameOver = gameOverTemp;
    directionForward = directionForwardTemp;
    currSpeed = currSpeedTemp;
}