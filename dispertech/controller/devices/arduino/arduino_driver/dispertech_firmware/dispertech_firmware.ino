#include <SoftwareSerial.h>

// Generic variables for the entire program
bool isData;
String Comm = "";
String serialString;


// Variables and constants for the Piezo movement
byte rx_byte = 0; // Encodes the speed/direction
const int piezo_delay = 200; // Amount of time before stopping the movement in case it is not a single-step
const int piezo_X = 8;
const int piezo_Y = 4;
const int piezo_Z1 = 5;
const int piezo_Z2 = 6;

SoftwareSerial mySerial(10, 3); // RX, TX

void setup() {
  pinMode(piezo_X, OUTPUT);
  pinMode(piezo_Y, OUTPUT);
  pinMode(piezo_Z1, OUTPUT);
  pinMode(piezo_Z2, OUTPUT);
  digitalWrite(piezo_X, LOW);
  digitalWrite(piezo_Y, LOW);
  digitalWrite(piezo_Z1, LOW);
  digitalWrite(piezo_Z2, LOW);
  Serial.begin(19200);
  Serial.flush();
  while (!Serial) { // Wait for serial to become available

  }


  mySerial.begin(19200);
  mySerial.flush();
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
      }
      else if (Comm.startsWith("mot2")) {
        digitalWrite(piezo_Y, HIGH);
      }
      else if (Comm.startsWith("mot3")) {
        digitalWrite(piezo_Z2, HIGH); // Currently, the only option connected is the SMA cable on the PCB
      }
      Serial.println("Waiting motion input");
      while (Serial.available() <= 0 ) {
        delay(1);
      }
      rx_byte = Serial.read();
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
        delay(piezo_delay / 2);
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
