#include "mbed.h"
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include "statechart.h"


Serial bluetooth(D9,D10); //TODO: change this to the proper UART ports
Serial device(D11,D12);  //CHANGE THIS TO PROPER SERIAL ports
DigitalOut myled(LED1);

void start();
void read_sensor();

/* Global variables with sensor packet info */
char Sensor_byte_count = 0;
char Sensor_Data_Byte = 0;
char Sensor_ID = 0;
char Sensor_Num_Bytes = 0;
char Sensor_Checksum = 0;
char bluetooth_byte=0; // byte from the bluetooth protocol that gets written into by the BlueSMIRF

int16_t sensorDistance=0;

//wait until system clock passes to next integer multiple of period
//taken from main.c in the irobot navigation folders
void waitUntilNextMultiple(const uint64_t msMultiple);

//returns system clock time in ms
uint64_t getTimeInMs(void);
//delay
void delayMs(const uint64_t msDelay);




//DECLARING ALL VARIABLES FOR USE IN THE STATECHART
//TODO: MAKESURE THE VARIABLES ARE ASSIGNED IN THE PROPER ISRs
bool init = false;
bool drive = false;
bool gameOver = false;
int currSpeed = 0;
int8_t direction = 0;
int16_t gameDistance = 300; //this is the distance to goal for the game

int main() {

    device.baud(57600);
    start();
    device.attach(&read_sensor); //getting distance readings from iRobot sensors
    //bluetooth.attach(&read_bluetooth); //getting bluetooth info from leapmotion

    while(1) {
        execute_statechart(init,drive,gameOver,currSpeed,direction, device, gameDistance,sensorDistance);
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
    //TODO: alter this to fit the bluetooth protocol
    if(bluetooth.readable()){
        bluetooth_byte=bluetooth.getc();
    }
}


// ISR which triggers when we want to read the distance sensor
void read_sensor(){
     char start_character;
    while (device.readable()) {
        switch (Sensor_byte_count) {
            case 0: {
                start_character = device.getc();
                if (start_character == 19) Sensor_byte_count++;
                break;
            }
            case 1: {
                Sensor_Num_Bytes = device.getc();
                Sensor_byte_count++;
                break;
            }
            case 2: {
                Sensor_ID = device.getc();
                Sensor_byte_count++;
                break;
            }
            case 3: {
                Sensor_Data_Byte = device.getc();
                Sensor_byte_count++;
                break;
            }
            case 4: {
                Sensor_Checksum = device.getc();
                // Could add code here to check the checksum and ignore a bad data packet
                led1 = Sensor_Data_Byte &0x01;
                led2 = Sensor_Data_Byte &0x02;
                led3 = Sensor_Data_Byte &0x04;
                led4 = Sensor_Data_Byte &0x08;
                Sensor_byte_count = 0;
                break;
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