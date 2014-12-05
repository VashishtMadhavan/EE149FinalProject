#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include "statechart.h"


Serial bluetooth(PTE22,PTE23);
Serial device(D14, D15);

// Bluetooth Commands
const char         Initialize = 19;
const char         IsGameOver = 23;
const char         SpeedControl = 31;
const char         DriveID = 34;


void start();
void read_bluetooth();
bool getDriveDirection(char input);
int getSpeed(char input);
void resetAllVars();
void saveVarsToTemp();
void restoreVarsToTemp();


/* Global variables with sensor packet info */
char bluetooth_byte_count = 0;
char bluetooth_Data_Byte = 0;
char bluetooth_ID = 0;
char bluetooth_byte = 0; // byte from the bluetooth protocol that gets written into by the BlueSMIRF

int16_t sensorDistance = 0;

int checksum = 0;


//DECLARING ALL VARIABLES FOR USE IN THE STATECHART
bool init;
bool drive;
bool gameOver;
int currSpeed=0;
bool directionForward;
int16_t gameDistance = 300; //this is the distance to goal for the game

//temp copies for vars
bool initTemp;
bool driveTemp;
bool gameOverTemp;
int currSpeedTemp;
bool directionForwardTemp;




int main() {
    resetAllVars();
    wait(3);
    device.baud(57600);
    bluetooth.baud(115200);
    start();
    bluetooth.attach(&read_bluetooth);
    //TODO: add sensor for iRobot create
    while(1) {
        execute_statechart(init, drive, gameOver, currSpeed, directionForward, &device, gameDistance, sensorDistance);
        wait(2);
     }
}



void read_bluetooth(){
    saveVarsToTemp();
    resetAllVars();
    while (bluetooth.readable()){
        bluetooth_byte = bluetooth.getc();
        switch (bluetooth_byte_count) {
            // get OpCode
            case 0:
                if (bluetooth_byte == Initialize) {
                    init = true;
                } else if (bluetooth_byte == IsGameOver) {
                    gameOver = true;
                } else {
                    drive = true;
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
                checksum = checksum + bluetooth_byte;
                if ((checksum & 0xFF) != 0) {
                    restoreVarsToTemp();
                }
                bluetooth_byte_count = 0;
                break;                
        }
    }
    return;
}

void start(){
    // device.printf("%c%c", Start, SafeMode);
    device.putc(Start);
    device.putc(SafeMode);
    wait(.5);
  //  device.printf("%c%c%c", SensorStream, char(1), BumpsandDrops);
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
    int speed=0;
    switch (input){
        case 0: 
            speed = 0;
            break; 
        case 1: 
            speed = 50;
            break; 
        case 2: 
            speed = 100;
            break; 
        case 3: 
            speed = 125;
            break; 
        case 4: 
            speed = 150;
            break; 
        case 5: 
            speed = 200;
            break; 
        case 6: 
            speed = 250;
            break; 
        default:
            speed = 0;
            break;
       } 
        return speed;
}

void resetAllVars() {
    init = false;
    drive = false;
    gameOver = false;
    directionForward = true;
    currSpeed = 0;
    bluetooth_byte_count = 0;
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