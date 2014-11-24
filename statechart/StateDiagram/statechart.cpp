#include "statechart.h"

typedef enum{
    STOP=0,
    DRIVE,
    REVERSE,
    END
} robotState_t


const int8_t       maxCorrect=12;  //can get only 12 in a row correct
const int32_t      totalGameDistance=500; //tunable distance of DDR game
const int          maxSpeed=300;

//may need to change these to adjust speed
int speed_left=0;
int speed_right=0;

void execute_statechart(bool error,char bluetooth_byte,Serial device, const int32_t netDistance){
    static robotState_t state= STOP;
    static int8_t correct=0;
    static int32_t distanceAtManueverStart=0;
    
    //*****************************************************
    // state data - process inputs                        *
    //*****************************************************
    
    if(state==STOP && !error){
        state=DRIVE;
        correct=0;
    }
    
    else if(state==STOP && error){
        state=REVERSE;
    }
    
    else if(state==DRIVE && (error && correct !=0)){
        correct--;
        speed_left=speed_right= (((correct+1)*1.0)/maxCorrect)*maxSpeed;
    }

    else if(state==DRIVE && !error){
        if(correct!=maxCorrect){
            correct++;
        }
        speed_left=speed_right= (((correct+1)*1.0)/maxCorrect)*maxSpeed;
    }

    else if(state==DRIVE && (correct==0 && error)){
        state=STOP;
    }

    else if(state==REVERSE && !error){
        state=STOP;
    }
    
    //*****************************************************
    // state transition - pause region (highest priority) *
    //*****************************************************
    
    //*************************************
    // state transition - run region      *
    //*************************************
    int32_t distDiff=(netDistance - distanceAtManueverStart);

     else if(state==DRIVE && distDiff >=100){
        if(distanceAtManueverStart >= totalGameDistance){
            state=END;
        }
    }

    else if(state==REVERSE && distDiff < 0){
        if(distanceAtManueverStart<=0){
            state=END:
        }
    }

    
    // else, no transitions are taken

    //*****************
    //* state actions *
    //*****************
    
    switch(state){
    case STOP:
        speed_left=speed_right=0;
        drive_forward(device);
    case REVERSE:
        reverse(device);
        break;
    case END:
        speed_left=speed_right=0;
        playsong(device);
        stop(device);
        break;
    case DRIVE:
        drive_forward(device);
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


 void stop(Serial device){
    device.putc(DriveDirect);
    device.putc(char(0));
    device.putc(char(0));
    device.putc(char(0));
    device.putc(char(0));
 }

 void playsong(Serial device) { 
    device.putc(Song);
    device.putc(char(0));
    device.putc(char(2));
    device.putc(char(64));
    device.putc(char(24));    
    device.putc(char(36));
    device.putc(char(36));
    wait(.2);
    device.putc(PlaySong);
    device.putc(char(0));
}
 
void reverse() {
    device.putc(DriveDirect);
    device.putc(char(((-speed_right)>>8)&0xFF));
    device.putc(char((-speed_right)&0xFF));
    device.putc(char(((-speed_left)>>8)&0xFF));
    device.putc(char((-speed_left)&0xFF));
 
}


