#include "statechart.h"

typedef enum{
    INACTIVE = 0,
    ACTIVE
} robotState_t

typedef enum{
    FORWARD = 0,
    BACKWARD,
    ABSENT
} direction_t


int speed_left = 0;
int speed_right = 0;

void execute_statechart(bool init, bool drive, bool gameOver, int currSpeed, bool directionForward,  
    Serial device, int16_t gameDistance, const int16_t netDistance){
    static robotState_t state = INACTIVE;
    static direction_t currDirection = ABSENT;
    static int16_t goalDistance = gameDistance;
    static bool victory = false;

    //inputs = 
    // init = boolean
    // drive = boolean
    // gameOver = boolean
    // currSpeed = integer with speed
    // direction  = 8 bit integer which takes on -1,1,0
    //  0 = absent, 1 = forward, -1 = backward


    //*****************************************************
    // state data - process inputs                        *
    //*****************************************************
    
    if(state == INACTIVE && init){
        state=ACTIVE;
        speed_right = speed_left = 0;
        currDirection= FORWARD;
    }

    else if (state == ACTIVE && drive){
        currSpeed = speed;
        if(direction > 0){
            currDirection = FORWARD;
        }
        else if (direction < 0){
            currDirection = BACKWARD;
        }else{
            currDirection = ABSENT;
        }
    }

    else if (state == ACTIVE && (gameOver)){
        state =  INACTIVE;
    }

    //*****************************************************
    // state data - run region                            *
    //*****************************************************

    if(state == ACTIVE && (netDistance) >= goalDistance){
        state = INACTIVE;
        victory = true;
    }

    //*****************************************************
    // state data - default action                        *
    //*****************************************************



    switch(state){
        case INACTIVE:
            speed_left = speed_right = 0;
            if(gameOver || victory){
                //send victory to the bluetooth program
                playsong(device);
                stop(device);
            }
            break;
        case ACTIVE:
            speed_left = speed_right = currSpeed;
            if(currDirection==FORWARD){
                drive_forward(device);
            }
            else if(currDirection==BACKWARD){
                reverse(device);
            }
            break;
        default:
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


