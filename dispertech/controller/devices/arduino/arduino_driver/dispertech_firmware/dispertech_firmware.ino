#include <SPI.h>
#include <SoftwareSerial.h>

// Generic variables for the entire program
bool isData;
String Comm = "";
String serialString;
int i;


// Variables to control the LEDs
const int LED_POWER = 14;
const int LED_CARTRIDGE = 17;
const int LED_SAMPLE = 15;
const int LED_MEASURING = 16;
const int LED_SIDE = 18;
const int LED_FIBER = 20;
const int LED_TOP = 19;
int POWER_STATUS = LOW;
int PROCESSING_STATUS = LOW;
int INITIALISING_STATUS = LOW;
int READY_STATUS = LOW;
int SIDE_STATUS = LOW;
int FIBER_STATUS = LOW;
int TOP_STATUS = LOW;
const int register_select = 6;

// Variables and constants for the Piezo movement
byte rx_byte = 0; // Encodes the speed/direction
byte stop_byte = 0; // Used only to stop the movement of the piezo
const int piezo_delay_x_y = 20; // Amount of time before stopping the movement in case it is not a single-step only for the XY mirror
const int piezo_delay_z = 2000; // Delay when moving the linear stage
int piezo_delay = 0; // Variable to set either value for the delay.
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

// Variables for the shift register (that controls LED's)
byte shift_status = 0;

const int RTD_Select = 10;

const int POWER_PIN = 17;
const int POWER_PIN = 17;
void setup() {
  pinMode(POWER_PIN, INPUT);
  pinMode(piezo_X, OUTPUT);
  pinMode(piezo_Y, OUTPUT);
  pinMode(piezo_Z1, OUTPUT);
  pinMode(piezo_Z2, OUTPUT);
  pinMode(STATUS_pin, INPUT);
  pinMode(DAC_Select, OUTPUT);
  pinMode(LED_POWER, OUTPUT);
  pinMode(LED_CARTRIDGE, OUTPUT);
  pinMode(LED_SAMPLE, OUTPUT);
  pinMode(LED_MEASURING, OUTPUT);
  pinMode(LED_SIDE, OUTPUT);
  pinMode(LED_FIBER, OUTPUT);
  pinMode(LED_TOP, OUTPUT);

  digitalWrite(piezo_X, LOW);
  digitalWrite(piezo_Y, LOW);
  digitalWrite(piezo_Z1, LOW);
  digitalWrite(piezo_Z2, LOW);
  digitalWrite(0, HIGH);
  digitalWrite(LED_POWER, HIGH);
  digitalWrite(LED_MEASURING, HIGH);
  digitalWrite(LED_SAMPLE, HIGH);
  digitalWrite(LED_CARTRIDGE, HIGH);
  digitalWrite(LED_TOP, LOW);
  digitalWrite(LED_SIDE, LOW);
  digitalWrite(LED_FIBER, LOW);

  Serial.begin(115200);
  Serial.flush();
  while (!Serial) { // Wait for serial to become available
  }
  Serial.flush();

  mySerial.begin(19200);
  mySerial.flush();
  SPI.begin();

  digitalWrite(DAC_Select, HIGH);
  write_shift(0);
  // Only for testing
  bitSet(shift_status, 4);
  bitSet(shift_status, 1);
  bitSet(shift_status, 3);
  bitSet(shift_status, 6);
  write_shift(shift_status);
  // End testing
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
      //output_value = digitalRead(STATUS_pin);
      //Serial.print("Status:");
      //Serial.print(output_value);
      //Serial.print(",");
      for (i = 6; i <= Comm.length(); i++) {
        tempValue += Comm[i];
      }
      power = tempValue.toInt();
      tempValue = "";
      //if (power > 100) {
      //  Serial.println("ERR:Power exceeds limits");
      //}
      //else {
      //output_value = 4095 * power / 100;
      write_dac(power);
      Serial.print("LASER:");
      Serial.println(power);
      //}
    }
    else if (Comm.startsWith("LED")) {
      int start_led = Comm.indexOf(":") + 1;
      int end_led = Comm.lastIndexOf(":");
      String LED = Comm.substring(start_led, end_led);
      int mode = Comm.substring(end_led+1, Comm.length()).toInt();
      Serial.println(start_led);
      Serial.println(end_led);
      Serial.println(LED);
      Serial.println(Comm.substring(end_led+1, Comm.length()));
      if (LED == "SIDE") {
        digitalWrite(LED_SIDE, mode);
      }
      else if (LED == "TOP") {
        digitalWrite(LED_TOP, mode);
      }
      else if (LED == "FIBER") {
        digitalWrite(LED_FIBER, mode);
      }
      else if (LED == "POWER") {
        bitClear(shift_status, 0);
        bitClear(shift_status, 1);
        if (mode == 1){
          bitSet(shift_status, 1);
          }
          else if (mode == 2){
            bitSet(shift_status, 0);
          }
        write_shift(shift_status);
      }
      else if (LED == "CARTRIDGE") {
        bitClear(shift_status, 2);
        bitClear(shift_status, 3);
        if (mode == 1){
          bitSet(shift_status, 3);
          }
          else if (mode == 2){
            bitSet(shift_status, 2);
          }
        write_shift(shift_status);
      }
      else if (LED == "SAMPLE") {
       bitClear(shift_status, 4);
        bitClear(shift_status, 5);
        if (mode == 1){
          bitSet(shift_status, 5);
          }
          else if (mode == 2){
            bitSet(shift_status, 4);
          }
        write_shift(shift_status);
      }
      else if (LED == "MEASURING") {
        bitClear(shift_status, 6);
        bitClear(shift_status, 7);
        if (mode == 1){
          bitSet(shift_status, 7);
          }
          else if (mode == 2){
            bitSet(shift_status, 6);
          }
        write_shift(shift_status);
      }
      Serial.print(LED);
      Serial.print(" changed mode to ");
      Serial.println(mode);
    }
    else if (Comm.startsWith("IDN")) {
      Serial.println("Dispertech device 2.0-scattering");
    }
    else if (Comm.startsWith("LED")) {
      if (Comm.startsWith("LED:TOP")) {
        digitalWrite(LED_TOP, HIGH);
      }
    }
    else if (Comm.startsWith("SHIFT")) {
      for (i = 6; i <= Comm.length(); i++) {
        tempValue += Comm[i];
      }
      int val = tempValue.toInt();
      tempValue = "";
      Serial.println(val);
      write_shift(val);
    }
    else if (Comm.startsWith("PWR")){
      Serial.println(digitalRead(POWER_PIN));
      }
    else if (Comm.startsWith("INI")) {
      digitalWrite(LED_CARTRIDGE, LOW);
      digitalWrite(LED_SAMPLE, LOW);
      digitalWrite(LED_MEASURING, LOW);
      digitalWrite(piezo_X, LOW);
      digitalWrite(piezo_Y, LOW);
      digitalWrite(piezo_Z1, LOW);
      digitalWrite(piezo_Z2, LOW);
      delay(2);
      mySerial.write(stop_byte);
      delay(2);
      Serial.println("Initialized");
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

void write_shift(byte value) {
  digitalWrite(register_select, LOW);
  SPI.beginTransaction(SPISettings(20000000, MSBFIRST, SPI_MODE0));
  SPI.transfer(value);
  SPI.endTransaction();
  digitalWrite(register_select, HIGH);
//  Serial.println(value);
}

void write_dac(int value) {
  digitalWrite(DAC_Select, LOW);
  SPI.beginTransaction(SPISettings(20000000, MSBFIRST, SPI_MODE0));
  bitClear(value, 15); // The most significant bit must be 0 to write to the DAC register
  bitSet(value, 13); //  Setting gain to 1 (max Vout = 2.048V)
  bitSet(value, 12); //  Active mode operation. Vout is available
  SPI.transfer(value >> 8);  //  Need to split the message in two 8-bit words, starting by the most-significant bit (bit 15)
  SPI.transfer(value);

  digitalWrite(DAC_Select, HIGH);
  SPI.endTransaction();
}
