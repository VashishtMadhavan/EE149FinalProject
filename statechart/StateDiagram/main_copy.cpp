#include "main_copy.h"

Serial bluetooth(PTE22,PTE23);
Serial device(D14, D15);

DigitalOut blue(LED3);
DigitalOut green(LED2);
DigitalOut red(LED1);

int main() {
    wait(3);
    device.baud(57600);
    bluetooth.baud(115200);
    start();
    bluetooth.attach(&read_bluetooth);
    device.attach(&read_device);
    //TODO: add sensor for iRobot create
    bool done = false;
    while(!done) {
        done = execute_statechart(init, drive, gameOver, currSpeed, directionForward, &device, gameDistance, sensorDistance); 
        wait(2);
     }
}

void read_bluetooth() {
    saveVarsToTemp();
    while (bluetooth.readable()){
        bluetooth_byte = bluetooth.getc();
        switch (bluetooth_byte_count) {
            // get OpCode
            case 0:
                if (bluetooth_byte == Initialize) {
                    init = true;
                    drive = gameOver = false;
                } else if (bluetooth_byte == IsGameOver) {
                    gameOver = true;
                    init = drive = false;
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
    device.putc(Start);
    device.putc(SafeMode);
    wait(.5);
    device.putc(SensorStream);
    device.putc(1);
    device.putc(BumpsandDrops);
    wait(.5);
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

void sendGameOver() {
    // bluetooth.printf("%d", gameOver);
    bluetooth.putc(gameOver);
}

void read_device() {
    if(device.readable()) {
        int device_byte = device.getc();
        green = 0;
        blue = 1;
        red = 1;
    }
    else {
        green = 1;
        blue = 0;
        red = 1;
    }
        
    /*
        switch(device_byte_count) {
            case 0:
                if (device_byte == Distance) device_byte_count++;
                break;
            case 1:
                sensorDistance = (device_byte << 8);
                device_byte_count++;
                break;
            case 2:
                sensorDistance = (sensorDistance | device_byte);
            default:
                device_byte_count = 0;
                break;
        }
    }

    if (sensorDistance > gameDistance) {
        gameOver = true;
        sendGameOver();
    }*/
}
