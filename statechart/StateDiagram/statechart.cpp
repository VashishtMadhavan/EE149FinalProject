#include "statechart.h"
typedef enum{
    INACTIVE = 0,
    ACTIVE
} robotState_t;
 
int speed_left = 0;
int speed_right = 0;

void execute_statechart(bool init, bool drive, bool gameOver, int currSpeed, bool directionForward,  
    Serial* device) {
    static robotState_t state = INACTIVE;
    static bool victory = false;
   
    if (state == INACTIVE && init){
        state = ACTIVE;
        speed_right = speed_left = 0;
    }

    else if (state == ACTIVE && drive){
        speed_right = speed_left = currSpeed;
    }

    else if (state == ACTIVE && (gameOver)){
        state =  INACTIVE;
    }

    switch(state){
        case INACTIVE:
            speed_left = speed_right = 0;
            if(gameOver || victory){
                stop(device);
            }
            break;
        case ACTIVE:
            speed_left = speed_right = currSpeed;
            if(!directionForward){
                reverse(device);
            } else{
                forward(device);
            }
            break;
        default:
            speed_left = speed_right = 0;
            break;
    }
}

void forward(Serial* device){
    device->printf("%c%c%c%c%c", DriveDirect, char((speed_right>>8)&0xFF),  char(speed_right&0xFF),  
    char((speed_left>>8)&0xFF),  char(speed_left&0xFF));
 }


 void stop(Serial* device){
   device->printf("%c%c%c%c%c", DriveDirect, char(0),  char(0),  char(0),  char(0));
 }
 
void reverse(Serial* device) {
    device->printf("%c%c%c%c%c", DriveDirect, char(((-speed_right)>>8)&0xFF),  char((-speed_right)&0xFF),  
    char(((-speed_left)>>8)&0xFF),  char((-speed_left)&0xFF));
 
}

