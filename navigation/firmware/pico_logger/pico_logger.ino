// Measurement-rig firmware for the Raspberry Pi Pico 2 (Arduino IDE, "Raspberry Pi Pico/RP2040/RP2350"
// board package by Earle Philhower). Reads the ICM-42688-P IMU over SPI at 200 Hz, counts the wheel
// encoder, catches the GNSS PPS pulse, and streams text lines over USB:
//
//   I,<t_us>,<gx>,<gy>,<gz>,<ax>,<ay>,<az>   rad/s and m/s^2, sensor axes
//   E,<t_us>,<ticks>                          encoder count since start, 50 Hz
//   P,<t_us>                                  PPS rising edge
//   S,<text>                                  status
//
// t_us is the Pico's own microsecond clock; the laptop logger (landdvl.rig) maps it onto its clock.
//
// Register addresses and field codes are from the Linux kernel driver (drivers/iio/imu/inv_icm42600,
// inv_icm42600.h). Check them against TDK's ICM-42688-P datasheet before trusting the numbers;
// the SPI read flag (0x80) is the usual InvenSense convention and is NOT verified from that source.

#include <SPI.h>

// ---- pins (change to match your wiring) ----
const int PIN_CS = 17;      // IMU chip select (SPI0: SCK 18, MOSI 19, MISO 16)
const int PIN_ENC_A = 2;    // encoder channel A
const int PIN_ENC_B = 3;    // encoder channel B
const int PIN_PPS = 4;      // GNSS PPS (3.3 V level!)

// ---- ICM-42688-P registers (bank 0) ----
const uint8_t REG_DEVICE_CONFIG = 0x11;  // bit 0: soft reset
const uint8_t REG_ACCEL_DATA_X = 0x1F;   // then Y, Z, then gyro X, Y, Z; 16-bit big-endian
const uint8_t REG_PWR_MGMT0 = 0x4E;      // [3:2] gyro mode, [1:0] accel mode; 3 = low noise
const uint8_t REG_GYRO_CONFIG0 = 0x4F;   // [7:5] full scale, [3:0] output data rate
const uint8_t REG_ACCEL_CONFIG0 = 0x50;  // [7:5] full scale, [3:0] output data rate
const uint8_t REG_WHO_AM_I = 0x75;
const uint8_t WHO_AM_I_ICM42688 = 0x47;

const uint8_t GYRO_FS_250DPS = 3;  // codes: 0 = 2000, 1 = 1000, 2 = 500, 3 = 250 dps
const uint8_t ACCEL_FS_4G = 2;     // codes: 0 = 16, 1 = 8, 2 = 4, 3 = 2 g
const uint8_t ODR_1KHZ = 6;        // sensor runs at 1 kHz; we read every 5 ms

const float GYRO_SCALE = (250.0f / 32768.0f) * (PI / 180.0f);  // rad/s per LSB
const float ACCEL_SCALE = (4.0f / 32768.0f) * 9.80665f;        // m/s^2 per LSB

const uint32_t IMU_PERIOD_US = 5000;   // 200 Hz
const uint32_t ENC_PERIOD_US = 20000;  // 50 Hz

SPISettings imuSpi(8000000, MSBFIRST, SPI_MODE0);
volatile int32_t encTicks = 0;
volatile uint64_t ppsTime = 0;
volatile bool ppsNew = false;

uint8_t readReg(uint8_t reg) {
  SPI.beginTransaction(imuSpi);
  digitalWrite(PIN_CS, LOW);
  SPI.transfer(reg | 0x80);
  uint8_t v = SPI.transfer(0);
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
  return v;
}

void writeReg(uint8_t reg, uint8_t value) {
  SPI.beginTransaction(imuSpi);
  digitalWrite(PIN_CS, LOW);
  SPI.transfer(reg & 0x7F);
  SPI.transfer(value);
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
}

void readBurst(uint8_t reg, uint8_t *buf, int n) {
  SPI.beginTransaction(imuSpi);
  digitalWrite(PIN_CS, LOW);
  SPI.transfer(reg | 0x80);
  for (int i = 0; i < n; i++) buf[i] = SPI.transfer(0);
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
}

// Quadrature decoding: called on every edge of A and B.
void encoderIsr() {
  static uint8_t last = 0;
  static const int8_t table[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};
  uint8_t now = (digitalRead(PIN_ENC_A) << 1) | digitalRead(PIN_ENC_B);
  encTicks += table[(last << 2) | now];
  last = now;
}

void ppsIsr() {
  ppsTime = time_us_64();
  ppsNew = true;
}

void setup() {
  Serial.begin(921600);  // USB: the number doesn't matter
  pinMode(PIN_CS, OUTPUT);
  digitalWrite(PIN_CS, HIGH);
  SPI.begin();
  delay(100);

  writeReg(REG_DEVICE_CONFIG, 0x01);  // soft reset
  delay(10);
  uint8_t who = readReg(REG_WHO_AM_I);
  while (!Serial) delay(10);
  Serial.printf("S,pico_logger v1, WHO_AM_I=0x%02X (expect 0x47)\n", who);
  writeReg(REG_GYRO_CONFIG0, (GYRO_FS_250DPS << 5) | ODR_1KHZ);
  writeReg(REG_ACCEL_CONFIG0, (ACCEL_FS_4G << 5) | ODR_1KHZ);
  writeReg(REG_PWR_MGMT0, (3 << 2) | 3);  // gyro and accel in low-noise mode
  delay(50);                              // the gyro needs a moment to start

  pinMode(PIN_ENC_A, INPUT_PULLUP);
  pinMode(PIN_ENC_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_A), encoderIsr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_B), encoderIsr, CHANGE);
  pinMode(PIN_PPS, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_PPS), ppsIsr, RISING);
}

void loop() {
  static uint64_t nextImu = time_us_64();
  static uint64_t nextEnc = time_us_64();
  uint64_t now = time_us_64();

  if (now >= nextImu) {
    nextImu += IMU_PERIOD_US;
    uint8_t b[12];
    readBurst(REG_ACCEL_DATA_X, b, 12);
    uint64_t t = time_us_64();
    int16_t raw[6];
    for (int i = 0; i < 6; i++) raw[i] = (int16_t)((b[2 * i] << 8) | b[2 * i + 1]);
    // raw[0..2] accel x, y, z; raw[3..5] gyro x, y, z
    Serial.printf("I,%llu,%.6f,%.6f,%.6f,%.5f,%.5f,%.5f\n", t, raw[3] * GYRO_SCALE,
                  raw[4] * GYRO_SCALE, raw[5] * GYRO_SCALE, raw[0] * ACCEL_SCALE,
                  raw[1] * ACCEL_SCALE, raw[2] * ACCEL_SCALE);
  }
  if (now >= nextEnc) {
    nextEnc += ENC_PERIOD_US;
    noInterrupts();
    int32_t ticks = encTicks;
    interrupts();
    Serial.printf("E,%llu,%ld\n", now, (long)ticks);
  }
  if (ppsNew) {
    noInterrupts();
    uint64_t t = ppsTime;
    ppsNew = false;
    interrupts();
    Serial.printf("P,%llu\n", t);
  }
}
