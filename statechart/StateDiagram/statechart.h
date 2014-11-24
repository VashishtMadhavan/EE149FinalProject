#include "mbed.h"
#include <stdint.h>

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


void execute_statechart(bool error,char bluetooth_byte, Serial device,const int32_t netDistance);
void drive_forward(Serial device);
void stop(Serial device);
void playsong(Serial device);
void reverse(Serial device);
