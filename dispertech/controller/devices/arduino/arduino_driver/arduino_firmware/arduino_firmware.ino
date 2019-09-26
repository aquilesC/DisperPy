#include "DHT.h"
#define DHTTYPE DHT22
const int DHTPin = 6;
DHT dht(DHTPin, DHTTYPE);

String Comm = "";

int output = DAC0;
int input;
int val;
String inData;
String tempValue;
String channel;
int sensorPin = A0;    // select the input pin for the potentiometer
int sensorValue;
bool isData = false;
int i = 0;
int Laser_LED = 24;
int Fiber_LED = 26;
int Power_LED = 30;
int Top_LED = 42;
int Measure_LED = 44;
byte rx_byte = 0;        // stores received byte
bool is_data;



void setup() {
  for (i = 2; i <= 13; i++) {
    pinMode(i, OUTPUT);
  }
  for (i = 22; i <= 53; i++) {
    pinMode(i, OUTPUT);
  }
  digitalWrite(Measure_LED, HIGH);
  digitalWrite(Power_LED, HIGH);
  digitalWrite(Laser_LED, HIGH);
  dht.begin();
  Serial.begin(19200);
  Serial1.begin(19200);   // serial port 1
  Serial2.begin(19200);   // serial port 2
  while (!Serial);

  analogWriteResolution(12);
  analogWrite(DAC0, 0);
  analogWrite(DAC1, 0);
  digitalWrite(Laser_LED, LOW);

  Serial.flush();
  Serial1.flush();
  Serial2.flush();
  digitalWrite(Measure_LED, LOW);
  for (i = 0; i < 5; i++) {
    digitalWrite(Power_LED, HIGH);
    delay(500);
    digitalWrite(Power_LED, LOW);
    delay(500);
  }
  digitalWrite(Power_LED, HIGH);
}

void loop() {
  while (Serial.available() > 0 ) {
    char value = Serial.read();
    Comm += value;
    if (value == '\n') {
      isData = true;
    }
  }
  if (isData) {
    isData = false;
    if (Comm.startsWith("ON")) {
      digitalWrite(Fiber_LED, HIGH);
      digitalWrite(Measure_LED, HIGH);
      digitalWrite(Laser_LED, HIGH);
      digitalWrite(Power_LED, HIGH);
      digitalWrite(Top_LED, HIGH);
      Serial.println("ON");
    }
    else if (Comm.startsWith("OFF")) {
      digitalWrite(Fiber_LED, LOW);
      digitalWrite(Measure_LED, LOW);
      digitalWrite(Laser_LED, LOW);
      digitalWrite(Power_LED, LOW);
      digitalWrite(Top_LED, LOW);
      Serial.println("OFF");
    }
    else if (Comm.startsWith("mot1")) {
      Serial.println("Waiting for input mot 1");
      while (Serial.available() <= 0) {
        delay(1);
      }
      rx_byte = Serial.read();
      Serial1.write(rx_byte);
      Serial.println("OK");
    }
    else if (Comm.startsWith("mot2")) {
      Serial.println("Waiting for input mot 2");
      while (Serial.available() <= 0) {
        delay(1);
      }
      rx_byte = Serial.read();
      Serial2.write(rx_byte);
      Serial.println("OK");
    }
    else if (Comm.startsWith("OUT")) {
      for (i = 4; i <= Comm.length(); i++) {
        tempValue += Comm[i];
      }
      val = tempValue.toInt();
      tempValue = "";
      analogWrite(DAC0, val);
      Serial.println(val);
    }
    else if (Comm.startsWith("DHT")) {
      float h = dht.readHumidity();
      float t = dht.readTemperature();
      if (isnan(h) || isnan(t)) {
        Serial.println("Failed to read from DHT sensor!");
      }
      Serial.print(h);
      Serial.print(",");
      Serial.println(t);
    }
    Comm = "";
  }
  delay(20);
}
