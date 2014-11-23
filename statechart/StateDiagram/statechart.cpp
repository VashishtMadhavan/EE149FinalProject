#include "statechart.h"
#include <math.h>

typedef enum{
    STOP=0,
    DRIVE,
    TURN
} robotState_t

const char         Start = 128;
const char         SafeMode = 131;
const char         FullMode = 132;
const char         Drive = 137;                // 4:   [Vel. Hi] [Vel Low] [Rad. Hi] [Rad. Low]
const char         DriveDirect = 145;          // 4:   [Right Hi] [Right Low] [Left Hi] [Left Low]
const char         Demo = 136;                 // 2:    Run Demo x
const char         Sensors = 142;              // 1:    Sensor Packet ID
const char         CoverandDock = 143;         // 1:    Return to Charger
const char         SensorStream = 148;               // x+1: [# of packets requested] IDs of requested packets to stream
const char         QueryList = 149;            // x+1: [# of packets requested] IDs of requested packets to stream
const char         StreamPause = 150;          // 1:    0 = stop stream, 1 = start stream
const char         PlaySong = 141;
const char         Song = 140;
                /* iRobot Create Sensor IDs */
const char         BumpsandDrops = 7;
const char         Distance = 19;
const char         Angle = 20;

//may need to change these to adjust speed
int speed_left=0;
int speed_right=0;

void execute_statechart(bool error, bool correcting,Serial bluetooth,Serial device, const int32_t netAngle){
    static robotState_t state= STOP;
    static robotState_t prevState= STOP;
    //0 - absent , 1= true, -1= false
    static int32_t keepGoing=0;
    static int32_t angleAtManueverStart=0;
    
    //*****************************************************
    // state data - process inputs                        *
    //*****************************************************
    
    if(state==STOP && correcting && !error){
        state=DRIVE;
        prevState=STOP;
        keepGoing=1;
    }
    
    else if(state==STOP && error && !correcting){
        state=TURN;
        speed_left = 100;
        speed_right= - speed_left;
        prevState=STOP;
        keepGoing=-1;
    }
    
    else if(state==DRIVE && (error || correcting)){
        state=STOP;
        prevState=DRIVE;
        keepGoing=-1;
    }
    else if(state==TURN && error && !correcting){
        state=DRIVE;
        prevState=TURN;
        keepGoing=1;
    }
    else if(state==TURN && correcting && !error){
        state=STOP;
        prevState=TURN;
        keepGoing=0;
    }
    
    //*****************************************************
    // state transition - pause region (highest priority) *
    //*****************************************************
    
    //*************************************
    // state transition - run region      *
    //*************************************
     else if(state==TURN && abs(netAngle - angleAtManueverStart) >=30){
         // still in the TURN state but does not keep moving
         speed_left=speed_right=0;
    }

    
    // else, no transitions are taken

    //*****************
    //* state actions *
    //*****************
    
    switch(state){
    case STOP:
        speed_left=speed_right=0;
        drive_forward(device);
    case TURN:
        //speed_left=100;
        //speed_right=-speed_left;
        turn_left(device)
    case DRIVE:
        speed_left=speed_right=300;
        drive_forwad(device);
        break;
    default:
        // Unknown state
        speed_left = speed_right = 0;
        break;
    }

}

void drive_forward(Serial device){
    device.putc(DriveDirect);
    device.putc(char(((speed_right)>>8)&0xFF));
    device.putc(char((speed_right)&0xFF));
    device.putc(char(((speed_left)>>8)&0xFF));
    device.putc(char((speed_left)&0xFF));
 }
 
void turn_left(Serial device) {
    device.putc(DriveDirect);
    device.putc(char(((speed_right)>>8)&0xFF));
    device.putc(char((speed_right)&0xFF));
    device.putc(char(((-speed_left)>>8)&0xFF));
    device.putc(char((-speed_left)&0xFF));
}

void turn_right(Serial device) {
    device.putc(DriveDirect);
    device.putc(char(((-speed_right)>>8)&0xFF));
    device.putc(char((-speed_right)&0xFF));
    device.putc(char(((speed_left)>>8)&0xFF));
    device.putc(char((speed_left)&0xFF));
}

