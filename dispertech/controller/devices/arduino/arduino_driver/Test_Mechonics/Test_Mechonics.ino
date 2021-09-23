byte rx_byte = 0;        // stores received byte
String serialString;
bool is_data;

void setup() {
  // initialize serial ports
  Serial.begin(19200);    // USB serial port 0
  Serial1.begin(19200);   // serial port 1
  Serial2.begin(19200);
  Serial3.begin(19200);
  Serial.flush();
  Serial1.flush();
  Serial2.flush();
  Serial3.flush();
}

void loop() {
  while (Serial.available() > 0 ) {
    char c = Serial.read();
    serialString += c;
    if (c == '\n') {
      is_data = true;
    }
  }
  if (is_data) {
    is_data = false;
    if (serialString.startsWith("mot")) {
      Serial.println("Waiting for input");
      while (Serial.available() <= 0) {
        delay(1);
      }
      rx_byte = Serial.read();
      delay(1);
      Serial1.write(rx_byte);
      Serial2.write(rx_byte);
      Serial3.write(rx_byte);
      Serial.write(rx_byte);
      Serial.println("OK");
    }
    serialString = "";
  }
  //  Serial.flush();

}
