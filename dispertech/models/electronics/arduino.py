"""
    Arduino Model
    =============
    This is an ad-hoc model for controlling an Arduino Due board, which will in turn control a piezo-mirror, a laser,
    and some LED's.
"""
import pyvisa
from pyvisa import VisaIOError

rm = pyvisa.ResourceManager('@py')

from time import sleep

from dispertech.controller.devices.arduino.arduino import Arduino


class ArduinoModel:
    def __init__(self, port):
        self.driver = rm.open_resource(port, baud_rate=19200)
        sleep(2)
        try:
            self.driver.query("IDN")
        except VisaIOError:
            try:
                self.driver.read()
            except VisaIOError:
                pass
        self.driver.query("OUT:0")
        self._laser_led = 0
        self._fiber_led = 0

    def laser_power(self, power: int):
        """ Changes the laser power. It also switches on or off the laser LED based on the power level set.

        Parameters
        ----------
        power int: Percentage of power (0-100)

        """
        out_power = round(power/100*4095)
        if out_power < 100:
            self.laser_led = 0
        else:
            self.laser_led = 1
        self.driver.query(f'OUT:{out_power}')

    @property
    def laser_led(self):
        return self._laser_led

    @laser_led.setter
    def laser_led(self, status: int):
        self.driver.query(f'LED:2:{status}')
        self._laser_led = status

    @property
    def fiber_led(self):
        return self._fiber_led

    @fiber_led.setter
    def fiber_led(self, status):
        self.driver.query(f'LED:0:{status}')
        self._fiber_led = status


    def move_mirror(self, speed: int, direction: int, axis: int):
        """ Moves the mirror connected to the board

        :param int speed: Speed, from 0 to 2^6.
        :param direction: 0 or 1, depending on which direction to move the mirror
        :param axis: 1 or 2, to select the axis
        """

        binary_speed = '{0:06b}'.format(speed)
        binary_speed = str(direction) + str(1) + binary_speed
        number = int(binary_speed, 2)
        bytestring = number.to_bytes(1, 'big')
        self.driver.query(f"mot{axis}")
        self.driver.write_raw(bytestring)
        ans = self.driver.read()
        if not ans is "OK":
            print('Error with motor')
            print(ans)

if __name__ == "__main__":
    dev = Arduino.list_devices()[0]
    ard = ArduinoModel(dev)
    ard.laser_power(50)
    ard.move_mirror(60, 1, 1)
    sleep(2)
    ard.move_mirror(60,0,1)
    ard.laser_power(100)
    sleep(2)
    ard.laser_power(1)

