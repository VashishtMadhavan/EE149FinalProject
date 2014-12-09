#include "main_copy.h"

Serial bluetooth(PTE22,PTE23);
Serial device(D14, D15);

DigitalOut blue(LED3);
DigitalOut green(LED2);
DigitalOut red(LED1);
static int16_t start_dist = 0;
static int16_t initial_dist = 0;


int main() {
    wait(3);
    device.baud(57600);
    bluetooth.baud(115200);
    start();
    bluetooth.attach(&read_bluetooth);
    // read_device();
    
    initial_dist = start_dist;
    device.attach(&read_device);
    //TODO: add sensor for iRobot create
    while(1) {
        execute_statechart(init, drive, gameOver, currSpeed, directionForward, &device, gameDistance, sensorDistance);
        // read_device();
        wait(.5);
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
    device.putc(Distance);
    // wait();
    bluetooth.printf("Read1: %d\n", device.getc());
    bluetooth.printf("Read2: %d\n", device.getc());
    bluetooth.printf("Read3: %d\n", device.getc());
    bluetooth.printf("Read4: %d\n", device.getc());
    bluetooth.printf("Read5: %d\n", device.getc());
    bluetooth.printf("Done here\n" );
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
    // bluetooth.printf("youre done\n");
    bluetooth.putc(IsGameOver);
}

void read_device() {
    bool finished = false;
    int device_checksum = 0;
    bool ignored = false;
    // bluetooth.printf("Start Distance: \n");
    // bluetooth.printf("%d\n",start_dist);
    green =0;
    red=1; 
    blue =1;
    while(1) {
    // while(device.readable()) {
    //     switch(device_byte_count) {
    //         case 0:
    //             device_byte = device.getc();
    //             if (device_byte == 19) device_byte_count++;
    //             bluetooth.printf("First byte: %d\n", device_byte);
    //             break;
    //         case 1:
    //             device_byte = device.getc();
    //             bluetooth.printf("Num bytes: %d\n", device_byte);
    //             device_checksum += device_byte;
    //             device_byte_count++;
    //             break;
    //         case 2:
    //             device_byte = device.getc();
    //             bluetooth.printf("Packet ID: %d\n", device_byte);
    //             if (device_byte == Distance){ 
    //                 device_byte_count++;
    //                 device_checksum += device_byte;
    //             } else {
    //                 device_byte_count = 0;
    //             }
    //             break;
    //         case 3:
    //             device_byte = device.getc();
    //             device_checksum += device_byte;
    //             bluetooth.printf("Distance byte 1: %d\n", device_byte);
    //             sensorDistance = (device_byte << 8);
    //             device_byte_count++;
    //             break;
    //         case 4:
    //             device_byte = device.getc();
    //             device_checksum += device_byte;
    //             bluetooth.printf("Distance byte 2: %d\n", device_byte);
    //             sensorDistance = (sensorDistance | (int16_t) device_byte);
    //             device_byte_count++;
    //             break;
    //         case 5:
    //             device_byte = device.getc();
    //             bluetooth.printf("device_checksum: %d\n", device_byte);
    //             device_checksum += device_byte;
    //             device_byte_count = 0;
    //             finished = true;
    //             start_dist += sensorDistance;
    //             break;
    //     }
    //     if (finished){
    //         green = 1;
    //         blue =1;
    //         red=0;
    //         break;
    //     }  
    // }        
    // if (!ignored &&  start_dist  > 0) {
    //     blue = 0;
    //     green = 1;
    //     red = 1;
    //     gameOver = true;
    //     drive = init = false;
    //     sendGameOver();
    // }
        // bluetooth.printf("Read: %d\n", device.getc());
    }
}
