#include "mbed.h"
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include "statechart.h"


Serial bluetooth(D9,D10); //TODO: change this to the proper UART ports
Serial device(D11,D12);  //CHANGE THIS TO PROPER SERIAL ports

// Bluetooth Commands
const char         Initialize = 19;
const char         IsGameOver = 23;
const char         SpeedControl = 31;
const char         DriveID = 34;

// Other static vars
const char         Forward = 1;

void start();
void read_sensor();

/* Global variables with sensor packet info */
char bluetooth_byte_count = 0;
char bluetooth_Data_Byte = 0;
char bluetooth_ID = 0;
char bluetooth_byte = 0; // byte from the bluetooth protocol that gets written into by the BlueSMIRF

int16_t sensorDistance = 0;

int checksum = 0;

//wait until system clock passes to next integer multiple of period
//taken from main.c in the irobot navigation folders
void waitUntilNextMultiple(const uint64_t msMultiple);

//returns system clock time in ms
uint64_t getTimeInMs(void);
//delay
void delayMs(const uint64_t msDelay);

//DECLARING ALL VARIABLES FOR USE IN THE STATECHART
bool init;
bool drive;
bool gameOver;
int currSpeed;
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
    device.baud(57600);
    start();
    device.attach(&read_bluetooth);
    while(1) {
        execute_statechart(init, drive, gameOver, currSpeed, direction, device, gameDistance, sensorDistance);
        //waitUntilNextMultiple(60);
     }
}

uint64_t getTimeInMs(void){
    time_t seconds = time(NULL);
    return (seconds) * 1000;
}

void delayMs(const uint64_t msDelay){
    wait_ms(msDelay * 1000);
}

void waitUntilNextMultiple(const uint64_t msMultiple){
    const uint64_t msCounter = getTimeInMs() % msMultiple;
    if(msCounter > 0){
        delayMs(msMultiple - msCounter);
    }
}

void read_bluetooth(){
    saveVarsToTemp();
    resetAllVars();
    while (bluetooth.readable()){
        bluetooth_byte = bluetooth.getc();
        switch (bluetooth_byte_count) {
            // get OpCode
            case 0: {
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
            }
            // get Drive id
            case 1: {
                if (bluetooth_byte == DriveDirectionID) {
                    bluetooth_byte_count++;
                    checksum += bluetooth_byte;
                }
                break;
            }
            // get Drive data
            case 2: {
                directionForward = getDriveDirection(bluetooth_byte);
                currSpeed = getSpeed(bluetooth_byte);
                checksum += bluetooth_byte;
                bluetooth_byte_count++;
            }
            // get checksum
            case 3: {
                checksum += bluetooth_byte.getc();
                if ((checksum & 0xFF) != 0) {
                    restoreVarsToTemp();
                }
                bluetooth_byte_count = 0;
            }
        }
    }
    return;
}

void start(){
    device.putc(Start);
    device.putc(SafeMode);
    wait(.5);
    device.putc(SensorStream);
    device.putc(1);
    device.putc(Distance);
    wait(.2);
}

bool getDriveDirection(char input) {
    char bitmask = 0b1000;
    bool forward = ((input & bitmask) == 0);
    return forward
}

int getSpeed(char input) {
    input = 0b0111 & input;
    int speed;
    switch (input):
        case 0: {
            speed = 0;
            break; 
        }
        case 1: {
            speed = 50;
            break; 
        }
        case 2: {
            speed = 100;
            break; 
        }
        case 3: {
            speed = 125;
            break; 
        }
        case 4: {
            speed = 150;
            break; 
        }
        case 5: {
            speed = 200;
            break; 
        }
        case 6: {
            speed = 250;
            break; 
        }
        
        return speed
}

void resetAllVars() {
    init = false;
    drive = false;
    gameOver = false;
    directionForward = false;
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