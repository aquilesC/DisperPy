"""
    Arduino Model
    =============
    This is an ad-hoc model for controlling an Arduino Due board, which will in turn control a piezo-mirror, a laser,
    and some LED's.
"""
from multiprocessing import Event
from threading import RLock

import pyvisa
from pyvisa import VisaIOError

from dispertech.models.experiment.nanoparticle_tracking.decorators import make_async_thread

rm = pyvisa.ResourceManager('@py')

from time import sleep

from dispertech.controller.devices.arduino.arduino import Arduino


class ArduinoModel:
    def __init__(self, port=None):
        self._threads = []
        self._stop_temperature = Event()
        self.temp_electronics = 0
        self.temp_sample = 0
        self.query_lock = RLock()

        if not port:
            port = Arduino.list_devices()[0]
        self.driver = rm.open_resource(port, baud_rate=19200)
        sleep(2)
        try:
            self.driver.query("IDN")
        except VisaIOError:
            try:
                self.driver.read()
            except VisaIOError:
                pass

        self.laser_power(0)
        self._laser_led = 0
        self._fiber_led = 0
        self._top_led = 0

    def laser_power(self, power: int):
        """ Changes the laser power. It also switches on or off the laser LED based on the power level set.

        Parameters
        ----------
        power int: Percentage of power (0-100)

        """
        with self.query_lock:
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
        with self.query_lock:
            self.driver.query(f'LED:2:{status}')
            self._laser_led = status

    @property
    def fiber_led(self):
        return self._fiber_led

    @fiber_led.setter
    def fiber_led(self, status):
        with self.query_lock:
            self.driver.query(f'LED:0:{status}')
            self._fiber_led = status

    @property
    def top_led(self):
        return self._top_led

    @top_led.setter
    def top_led(self, status):
        with self.query_lock:
            self.driver.query(f'LED:4:{status}')
            self._top_led = status

    @make_async_thread
    def move_mirror(self, speed: int, direction: int, axis: int):
        """ Moves the mirror connected to the board

        :param int speed: Speed, from 0 to 2^6.
        :param direction: 0 or 1, depending on which direction to move the mirror
        :param axis: 1 or 2, to select the axis
        """
        with self.query_lock:
            binary_speed = '{0:06b}'.format(speed)
            binary_speed = str(direction) + str(1) + binary_speed
            number = int(binary_speed, 2)
            bytestring = number.to_bytes(1, 'big')
            self.driver.query(f"mot{axis}")
            self.driver.write_raw(bytestring)
            ans = self.driver.read()

    @make_async_thread
    def monitor_temperature(self):
        while not self._stop_temperature.is_set():
            with self.query_lock:
                self.temp_electronics = float(self.driver.query("TEM:0"))
                self.temp_sample = float(self.driver.query("TEM:1"))
            sleep(5)

    def finalize(self):
        self._stop_temperature.set()
        self.fiber_led = 0
        self.top_led = 0
        self.laser_power(0)

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
