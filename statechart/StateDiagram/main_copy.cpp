#include "mbed.h"
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include "statechart.h"


Serial bluetooth(D9,D10);
Serial robot(D11,D12);
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

int main() {
    bool error=false;
    wait(3);
    device.baud(57600);
    start();
    device.attach(&read_sensor);
    bluetooth.attach(&read_bluetooth);

    while(1) {
        error=bluetooth_byte & 0X80; //checking if the highest bit is set to zero
        execute_statechart(error,bluetooth_byte,robot,sensorDistance);
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

//ISR which triggers whenever bluetooth is sending byte
void read_bluetooth(){
    if(bluetooth.readable()){
        bluetooth_byte=bluetooth.getc();
    }
}


// ISR which triggers when we want to read the distance sensor
void read_sensor(){
    char start_char;
    while(device.readable()){
        switch(Sensor_byte_count){
            case 0:{
                //reading packet header ID
                start_char=device.getc();
                if(start_char==19) Sensor_byte_count++;
                break;
            }
            case 1:{
                //number of packet bytes
                Sensor_Num_Bytes=device.getc();
                Sensor_byte_count++;
                break;
            }
            case 2: {
                //sensor ID of next data value
                Sensor_ID=device.getc();
                Sensor_byte_count++;
                break;
            }
            case 3: {
                Sensor_Data_Byte= device.getc();
                Sensor_byte_count++;
                sensorDistance= ((int16_t)Sensor_Data_Byte) << 8;
                break;
            }
            case 4: {
                Sensor_Data_Byte = device.getc();
                Sensor_byte_count++;
                sensorDistance+=Sensor_Data_Byte;
                break;
            }
            case 5: {
                Sensor_Checksum= device.getc();
                Sensor_byte_count=0;
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