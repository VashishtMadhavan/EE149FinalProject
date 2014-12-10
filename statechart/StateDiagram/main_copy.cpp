#include "main_copy.h"

Serial bluetooth(PTE22,PTE23);
Serial device(D14, D15);

DigitalOut blue(LED3);
DigitalOut green(LED2);
DigitalOut red(LED1);
static int16_t start_dist = 0;
bool finished =false;
bool ignored =  false;


int main() {
    wait(5);
    device.baud(57600);
    bluetooth.baud(115200);
    start();
    bluetooth.attach(&read_bluetooth);
    device.attach(&read_device);
    
    while(1) {
        bluetooth.printf("sensorDistance: %d\n", start_dist);
        execute_statechart(init, drive, gameOver, currSpeed, directionForward, &device, gameDistance, sensorDistance);
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

void sendGameOver() {
    bluetooth.printf("youre done\n");
}

void read_device() {
    finished = false;
    ignored = false;

    while(device.readable()) {
        switch(device_byte_count) {
            case 0:
                star_char = device.getc();
                if (star_char == 19) device_byte_count++;
                break;
            case 1:
                device_num_bytes = device.getc();
                device_byte_count++;
                break;
            case 2:
                device_packet_id = device.getc();
                device_byte_count++;
                break;
            case 3:
                device_data_byte = device.getc();
                sensorDistance = (device_data_byte << 8);
                device_byte_count++;
                break;
            case 4:
                device_byte = device.getc();
                sensorDistance = (sensorDistance | (int16_t) device_byte);
                device_byte_count++;
                break;
            case 5:
                device_checksum= device.getc();
                device_byte_count = 0;
                finished = true;
                start_dist += sensorDistance;
                break;
        }
        if (finished){
            green = 1;
            blue =1;
            red=0;
            break;
        }  
    }        
    if (!ignored &&  start_dist  > 200) {
        blue = 0;
        green = 1;
        red = 1;
        gameOver = true;
        drive = init = false;
        sendGameOver();
    }
}

