#include <SPI.h>
#include <SoftwareSerial.h>

// Generic variables for the entire program
bool isData;
String Comm = "";
String serialString;
int i;


// Variables to control the LEDs
const int LED_POWER = 14;
const int LED_PROCESSING = 15;
const int LED_INITIALISING = 16;
const int LED_READY = 17;
const int LED_SIDE = 18;
const int LED_FIBER = 19;
const int LED_TOP = 20;

// Variables and constants for the Piezo movement
byte rx_byte = 0; // Encodes the speed/direction
const int piezo_delay = 200; // Amount of time before stopping the movement in case it is not a single-step
const int piezo_X = 8;
const int piezo_Y = 4;
const int piezo_Z1 = 5;
const int piezo_Z2 = 6;

SoftwareSerial mySerial(10, 3); // RX, TX

// Variables to setup the DAC and the Laser
const int DAC_Select = 7; // This pin is used to enable the DAC
float power;
int output_value;
String tempValue;
const int STATUS_pin = 9;


void setup() {
  pinMode(piezo_X, OUTPUT);
  pinMode(piezo_Y, OUTPUT);
  pinMode(piezo_Z1, OUTPUT);
  pinMode(piezo_Z2, OUTPUT);
  pinMode(STATUS_pin, INPUT);
  pinMode(DAC_Select, OUTPUT);
  pinMode(LED_POWER, OUTPUT);
  pinMode(LED_PROCESSING, OUTPUT);
  pinMode(LED_INITIALISING, OUTPUT);
  pinMode(LED_READY, OUTPUT);
  pinMode(LED_SIDE, OUTPUT);
  pinMode(LED_FIBER, OUTPUT);
  pinMode(LED_TOP, OUTPUT);
  
  digitalWrite(piezo_X, LOW);
  digitalWrite(piezo_Y, LOW);
  digitalWrite(piezo_Z1, LOW);
  digitalWrite(piezo_Z2, LOW);
  digitalWrite(LED_POWER, HIGH);
  digitalWrite(LED_PROCESSING, HIGH);
  digitalWrite(LED_INITIALISING, HIGH);
  digitalWrite(LED_READY, HIGH);
  digitalWrite(LED_TOP, HIGH);
  digitalWrite(LED_SIDE, HIGH);
  digitalWrite(LED_FIBER, HIGH);
  
  Serial.begin(115200);
  Serial.flush();
  while (!Serial) { // Wait for serial to become available
  }

  mySerial.begin(19200);
  mySerial.flush();
  SPI.begin();

  digitalWrite(DAC_Select, HIGH);
}

void loop() {
  while (Serial.available() > 0) {
    char value = Serial.read();
    Comm += value;
    if (value == '\n') {
      isData = true;
    }
  }
  if (isData) {
    isData = false;
    if (Comm.startsWith("mot")) {
      if (Comm.startsWith("mot1")) {
        digitalWrite(piezo_X, HIGH);
        Serial.print("mot1:");
      }
      else if (Comm.startsWith("mot2")) {
        digitalWrite(piezo_Y, HIGH);
        Serial.print("mot2:");
      }
      else if (Comm.startsWith("mot3")) {
        digitalWrite(piezo_Z1, HIGH); // Currently, the only option connected is the SMA cable on the PCB
        Serial.print("mot3:");
      }
      else if (Comm.startsWith("mot4")) {
        digitalWrite(piezo_Z2, HIGH);
        Serial.print("mot4:");
      }
      Serial.println("Waiting motion input");
      while (Serial.available() <= 0 ) {
        delay(1);
      }
      rx_byte = Serial.read();
     // Serial.println(rx_byte, BIN);
      mySerial.write(rx_byte);
      bool is_step = true;
      for (int bits = 5; bits > 0; bits--) {
        if (rx_byte & (1 << bits)) {
          is_step = false;
        }
      }
      if (!(rx_byte & (1 << 0))) {
        is_step = false;
      }
      if (!(rx_byte & (1 << 7)) && is_step) { // In one of the directions it must take 2 steps in order to move one at a time
        delay(piezo_delay);
        mySerial.write(rx_byte);
      }
      if (!is_step) {
        delay(piezo_delay);
        rx_byte = 0;
        mySerial.write(rx_byte);
      }
      Serial.println("Movement OK");
      digitalWrite(piezo_X, LOW);
      digitalWrite(piezo_Y, LOW);
      digitalWrite(piezo_Z1, LOW);
      digitalWrite(piezo_Z2, LOW);
    }
    else if (Comm.startsWith("laser")) {
      output_value = digitalRead(STATUS_pin);
      Serial.print("Status:");
      Serial.print(output_value);
      Serial.print(",");
      for (i = 6; i <= Comm.length(); i++) {
        tempValue += Comm[i];
      }
      power = tempValue.toFloat();
      tempValue = "";
      if (power > 100) {
        Serial.println("ERR:Power exceeds limits");
      }
      else {
        output_value = 4095 * power / 100;
        write_dac(output_value);
        Serial.print("LASER:");
        Serial.println(output_value);
      }
    }
    else if (Comm.startsWith("IDN")) {
      Serial.println("Dispertech device 2.0-scattering");
    }
    else {
      Serial.println("Command not known");
    }
    Serial.flush();
    mySerial.flush();
    Comm = "";
  }
  delay(2);
  }

void write_dac(int value) {
  digitalWrite(DAC_Select, LOW);
  SPI.beginTransaction(SPISettings(20000000, MSBFIRST, SPI_MODE0));
  byte head = 0b00010000;
  int new_value = value >> 8;
  int new_new_value = value & 0b0000000011111111;
  SPI.transfer(head | new_value);
  SPI.transfer(new_new_value);
  digitalWrite(DAC_Select, HIGH);
  SPI.endTransaction();
}
