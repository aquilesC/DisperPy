from PyQt5.QtWidgets import QApplication

from dispertech.controller.devices.arduino.arduino import Arduino
from dispertech.view.focusing_window import FocusingWindow
from dispertech.models.electronics.arduino import ArduinoModel


dev = Arduino.list_devices()[0]
arduino = ArduinoModel(dev)
arduino.laser_power(50)
app = QApplication([])
fw = FocusingWindow(arduino=arduino)
fw.show()
app.exec()
