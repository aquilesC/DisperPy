// This is the controller for the Thorlabs driver developed at Dispertech. 
// For more information, contact: carattino@dispertech.com 
// This software is provided as-is without warranties of any kind. 
#include <SPI.h>
const int DAC_Select = 7; // This pin is used to enable the DAC


String Comm;
float power;
int output_value;
String tempValue;
int i;
bool isData;

void setup() {
  SPI.begin();
  Serial.begin(115200);
  while(!Serial);
  pinMode(DAC_Select, OUTPUT);
  digitalWrite(DAC_Select, HIGH);
  
}

void loop() {
  while (Serial.available() > 0){
    char value = Serial.read();
    Comm += value;
    if (value == '\n'){
      isData = true;
    }
  }
  if (isData){
    isData = false;
    if (Comm.startsWith("LASER")){
      for (i = 6; i<= Comm.length(); i++){
        tempValue += Comm[i];
      }
      power = tempValue.toFloat();
      tempValue = "";
      if (power>100){
        Serial.println("ERR:Power exceeds limits");  
      }
      else{
        output_value = 4095*power/100;
        write_dac(output_value);
        Serial.print("LASER:");
        Serial.println(output_value);
      }
    }
    else if (Comm.startsWith("IDN")){
      Serial.println("Dispertech Laser Controller. v2021.1");
      }
    else{
      Serial.println("ERR: Command not known");
    }
    
    Comm = "";
  }
}


void write_dac(int value){
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
