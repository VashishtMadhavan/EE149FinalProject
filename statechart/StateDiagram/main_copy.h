#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>
#include "statechart.h"

// Bluetooth Commands
const char         Initialize = 19;
const char         IsGameOver = 23;
const char         SpeedControl = 31;
const char         DriveID = 34;

/* Global variables with sensor packet info */
char bluetooth_byte_count = 0;
char bluetooth_Data_Byte = 0;
char bluetooth_ID = 0;
char bluetooth_byte = 0; // byte from the bluetooth protocol that gets written into by the BlueSMIRF

char device_num_bytes = 0;
char device_packet_id=0;
char device_data_byte =0;
char device_checksum=0;
char device_byte_count = 0;
char star_char =0;
char device_byte=0;

int16_t sensorDistance = 0;

int checksum = 0;

//DECLARING ALL VARIABLES FOR USE IN THE STATECHART
bool init = false;
bool drive = false;
bool gameOver = false;
int currSpeed = 0;
bool directionForward = false;

//temp copies for vars
bool initTemp;
bool driveTemp;
bool gameOverTemp;
int currSpeedTemp;
bool directionForwardTemp;

void start();
void read_bluetooth();
bool getDriveDirection(char input);
int getSpeed(char input);
void saveVarsToTemp();
void restoreVarsToTemp();
void sendGameOver();
