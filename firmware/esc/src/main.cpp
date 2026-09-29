// SprayRover hub-motor ESC firmware (B-G431B-ESC1 + SimpleFOC).
//
// Placeholder. Phase 0 (see documentation/system-architecture.md, section 8) replaces this
// with a closed-loop velocity controller for one hoverboard hub motor using its Hall sensors,
// commanded over UART by the navigation MCU.

#include <Arduino.h>
#include <SimpleFOC.h>

void setup() {
    Serial.begin(115200);
    Serial.println("SprayRover ESC: firmware skeleton");
}

void loop() {}
