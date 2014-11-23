#include "mbed.h"

void execute_statechart(bool error,bool correcting,Serial bluetooth,Serial device,const int32_t netAngle);
void drive_forward(Serial device);
void turn_left(Serial device);
void turn_right(Serial device);
void stop(Serial device);
