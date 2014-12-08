#include "statechart.h"
typedef enum{
    INACTIVE = 0,
    ACTIVE
} robotState_t;

DigitalOut blue(LED3);
DigitalOut green(LED2);
DigitalOut red(LED1);
 
int speed_left = 0;
int speed_right = 0;

void execute_statechart(bool init, bool drive, bool gameOver, int currSpeed, bool directionForward,  
    Serial* device, int16_t gameDistance, const int16_t netDistance){
    static robotState_t state = INACTIVE;
    //static int16_t goalDistance = gameDistance;
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
            //red=0;
//            blue=1;
//            green=1;
            if(gameOver || victory){
                stop(device);
            }
            break;
        case ACTIVE:
            speed_left = speed_right = currSpeed;
            if(!directionForward){
                //green=1;
//                red =1;
//                blue=0;
                reverse(device);
            }else{
          //      green=0;
//                red =1;
//                blue=1;
                forward(device);
            }
            break;
        default:
            speed_left = speed_right = 0;
            break;
    }

}

void forward(Serial* device){
    blue=0;
    red =1;
    green =1;
    (*device).printf("%c%c%c%c%c", DriveDirect, char((speed_right>>8)&0xFF),  char(speed_right&0xFF),  
    char((speed_left>>8)&0xFF),  char(speed_left&0xFF));
 }


 void stop(Serial* device){
   (*device).printf("%c%c%c%c%c", DriveDirect, char(0),  char(0),  char(0),  char(0));
 }
 
void reverse(Serial* device) {
    red=0;
    blue =1;
    green =1;
    (*device).printf("%c%c%c%c%c", DriveDirect, char(((-speed_right)>>8)&0xFF),  char((-speed_right)&0xFF),  
    char(((-speed_left)>>8)&0xFF),  char((-speed_left)&0xFF));
 
}


