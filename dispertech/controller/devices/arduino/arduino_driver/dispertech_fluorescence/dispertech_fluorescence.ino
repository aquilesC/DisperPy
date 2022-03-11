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
int POWER_STATUS = LOW;
int PROCESSING_STATUS = LOW;
int INITIALISING_STATUS = LOW;
int READY_STATUS = LOW;
int SIDE_STATUS = LOW;
int FIBER_STATUS = LOW;
int TOP_STATUS = LOW;

// Variables and constants for the Piezo movement
byte rx_byte = 0; // Encodes the speed/direction
byte stop_byte = 0; // Used only to stop the movement of the piezo
const int piezo_delay_x_y = 20; // Amount of time before stopping the movement in case it is not a single-step only for the XY mirror
const int piezo_delay_z = 50; // Delay when moving the linear stage
int piezo_delay = 0; // Variable to set either value for the delay.
const int piezo_X = 8;
const int piezo_Y = 4;
const int piezo_Z1 = 5;
const int piezo_Z2 = 6;

SoftwareSerial mySerial(10, 3); // RX, TX

// Variables to setup the DAC and the Laser
const int Select_633 = 7;
const int Select_488 = 10; // This pin is used to enable the DAC
float power;
int output_value;
int dac;
String tempValue;
const int STATUS_pin = 9;


void setup() {
  pinMode(piezo_X, OUTPUT);
  pinMode(piezo_Y, OUTPUT);
  pinMode(piezo_Z1, OUTPUT);
  pinMode(piezo_Z2, OUTPUT);
  pinMode(STATUS_pin, INPUT);
  pinMode(Select_633, OUTPUT);
  pinMode(Select_488, OUTPUT);
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
  digitalWrite(0, HIGH);
  digitalWrite(LED_POWER, HIGH);
  digitalWrite(LED_PROCESSING, HIGH);
  digitalWrite(LED_INITIALISING, HIGH);
  digitalWrite(LED_READY, HIGH);
  digitalWrite(LED_TOP, LOW);
  digitalWrite(LED_SIDE, LOW);
  digitalWrite(LED_FIBER, LOW);

  Serial.begin(115200);
  Serial.flush();
  while (!Serial) { // Wait for serial to become available
  }

  mySerial.begin(19200);
  mySerial.flush();
  SPI.begin();

  digitalWrite(Select_633, HIGH);
  digitalWrite(Select_488, HIGH);

  digitalWrite(LED_POWER, HIGH);
  digitalWrite(LED_PROCESSING, LOW);
  digitalWrite(LED_INITIALISING, LOW);
  digitalWrite(LED_READY, LOW);
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
        piezo_delay = piezo_delay_x_y;
        Serial.print("mot1:");
      }
      else if (Comm.startsWith("mot2")) {
        digitalWrite(piezo_Y, HIGH);
        piezo_delay = piezo_delay_x_y;
        Serial.print("mot2:");
      }
      else if (Comm.startsWith("mot3")) {
        digitalWrite(piezo_Z1, HIGH); // Currently, the only option connected is the SMA cable on the PCB
        piezo_delay = piezo_delay_z;
        Serial.print("mot3:");
      }
      else if (Comm.startsWith("mot4")) {
        digitalWrite(piezo_Z2, HIGH);
        piezo_delay = piezo_delay_z;
        Serial.print("mot4:");
      }
      Serial.println("Waiting motion input");
      while (Serial.available() <= 0 ) {
        delay(1);
      }
      delay(10);
      rx_byte = Serial.read();
      bool is_step = true;
      for (int bits = 5; bits > 0; bits--) {
        if (rx_byte & (1 << bits)) {
          is_step = false;
        }
      }
      if (!(rx_byte & (1 << 0))) {
        is_step = false;
      }

      mySerial.write(rx_byte);
      if (is_step) {
        
        delay(50);
        //        Serial.write("Step");

        if (!(rx_byte & (1 << 7))) { // In one of the directions it must take 2 steps in order to move one at a time
          //          Serial.write("Double Step");
          mySerial.write(rx_byte);
          delay(50);
        }
      }

      else {
        //        Serial.write("Not Step");
        delay(piezo_delay);
        mySerial.write(stop_byte);
        delay(2);
      }
      Serial.println(rx_byte);
      //      Serial.println("Movement OK");
      digitalWrite(piezo_X, LOW);
      digitalWrite(piezo_Y, LOW);
      digitalWrite(piezo_Z1, LOW);
      digitalWrite(piezo_Z2, LOW);
    }
    else if (Comm.startsWith("laser")) {
      for (i = 7; i <= Comm.length(); i++) {
        tempValue += Comm[i];
      }
      power = tempValue.toFloat();
      tempValue = "";
      if (power > 100) {
        Serial.println("ERR:Power exceeds limits");
      }
      else {
        output_value = 4095 * power / 100;
        if (Comm.startsWith("laser1:")){dac = Select_633;}
        else {dac=Select_488;}
        write_dac(output_value, dac);
        Serial.print("LASER:");
        Serial.println(output_value);
      }
    }
    else if(Comm.startsWith("status")){
      Serial.println(digitalRead(STATUS_pin));  
    }
    else if (Comm.startsWith("LED")) {
      int val = Comm.substring(4, 5).toInt();
      int mode = Comm.substring(6, 7).toInt();

      switch (val) {
        case 0:
          digitalWrite(LED_SIDE, mode);
          break;
        case 1:
          digitalWrite(LED_TOP, mode);
          break;
        case 2:
          digitalWrite(LED_FIBER, mode);
          break;
        case 3:
          digitalWrite(LED_POWER, mode);
          break;
        case 4:
          digitalWrite(LED_PROCESSING, mode);
          break;
        case 5:
          digitalWrite(LED_INITIALISING, mode);
          break;
        case 6:
          digitalWrite(LED_READY, mode);
          break;
      }
      Serial.println("LED changed");
    }
    else if (Comm.startsWith("IDN")) {
      Serial.println("Dispertech device 2.0-fluorescence");
    }
    else if (Comm.startsWith("LED")) {
      if (Comm.startsWith("LED:TOP")) {
        digitalWrite(LED_TOP, HIGH);
      }
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

void write_dac(int value, int DAC_Select) {
  digitalWrite(DAC_Select, LOW);
  SPI.beginTransaction(SPISettings(20000000, MSBFIRST, SPI_MODE0));
  byte head = 0b00110000;
  int new_value = value >> 8;
  int new_new_value = value & 0b0000000011111111;
  SPI.transfer(head | new_value);
  SPI.transfer(new_new_value);
  digitalWrite(DAC_Select, HIGH);
  SPI.endTransaction();
}
