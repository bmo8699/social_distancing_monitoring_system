#!/usr/bin/env python
#
# This library is for
#   Grove - mini PIR motion sensor(https://www.seeedstudio.com/Grove-mini-PIR-motion-sensor-p-2930.html)
#   Grove - PIR Mtion Sensor(https://www.seeedstudio.com/Grove-PIR-Motion-Sensor-p-802.html)
#
# This is the library for Grove Base Hat which used to connect grove sensors for raspberry pi.
#

'''
## License

The MIT License (MIT)

Grove Base Hat for the Raspberry Pi, used to connect grove sensors.
Copyright (C) 2018  Seeed Technology Co.,Ltd. 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
import time
from grove.gpio import GPIO
import sys
from grove.button import Button
from grove.grove_ryb_led_button import GroveLedButton
import threading
from gpiozero import Buzzer

usleep = lambda x: time.sleep(x / 1000000.0)

_TIMEOUT1 = 1000
_TIMEOUT2 = 10000

class GroveUltrasonicRanger(object):
    def __init__(self, pin):
        self.dio = GPIO(pin)

    def _get_distance(self):
        self.dio.dir(GPIO.OUT)
        self.dio.write(0)
        usleep(2)
        self.dio.write(1)
        usleep(10)
        self.dio.write(0)

        self.dio.dir(GPIO.IN)

        t0 = time.time()
        count = 0
        while count < _TIMEOUT1:
            if self.dio.read():
                break
            count += 1
        if count >= _TIMEOUT1:
            return None

        t1 = time.time()
        count = 0
        while count < _TIMEOUT2:
            if not self.dio.read():
                break
            count += 1
        if count >= _TIMEOUT2:
            return None

        t2 = time.time()

        dt = int((t1 - t0) * 1000000)
        if dt > 530:
            return None

        distance = ((t2 - t1) * 1000000 / 29 / 2)    # cm

        return distance

    def get_distance(self):
        while True:
            dist = self._get_distance()
            if dist:
                return dist


def main():
    from grove.helper import SlotHelper

    sonar1 = GroveUltrasonicRanger(18)
    sonar2 = GroveUltrasonicRanger(16)
    sonar3 = GroveUltrasonicRanger(5)
    
    
    u1_sensor_flag = False
    u2_sensor_flag = False
    
    is_entering = False
    is_leaving = False

    population = 0
    
    last_left_time = 3
    last_entered_time = 0
    u1_last_triggered_time = 0
    u2_last_triggered_time = 0
    
    button = GroveLedButton(22)
    
    def on_event(index, event, tm):
        nonlocal u1_sensor_flag
        nonlocal u2_sensor_flag
        if event & Button.EV_SINGLE_CLICK:
            u1_sensor_flag = False
            u2_sensor_flag = False
            last_left_time = 0
            u1_last_triggered_time = 0
            u2_last_triggered_time = 0
            print(u1_sensor_flag)
            print(u2_sensor_flag)
    
    button.on_event = on_event
    
    buzzer = Buzzer(26)
    prev_thread = None
    
    def buzz():
        for i in range(3):
            buzzer.on()
            time.sleep(0.3)
            buzzer.off()
            time.sleep(0.3)
        
    while True:
        if not u1_sensor_flag and not u2_sensor_flag and time.time() - last_entered_time > 20:
            button.led.light(True)
        else:
            button.led.light(False)

        u1_reading = sonar1.get_distance()
        if(u1_reading > 30 and u1_reading < 100):
            print(u1_reading)
            sum = 0
            for i in range(5):
                sum = sum + sonar1.get_distance()
            avg = sum / 5
            if 0 <= abs(u1_reading - avg) <= 0.2: 
                print('Ultra 1 detected.')
                if (u2_sensor_flag and time.time() - last_entered_time > 20):
                    print("a person is leaving")
                    leave_file = open('leave.txt', 'w')
                    leave_file.write("1")
                    leave_file.close()
                    u1_sensor_flag = False
                    u2_sensor_flag = False
                    last_left_time = time.time()
                else:
                    if (time.time() - last_left_time > 2 and time.time() - last_entered_time > 20):
                        u1_sensor_flag = True
                    else:
                        u2_sensor_flag = False
                print(u1_sensor_flag)
        
        u2_reading = sonar2.get_distance()
        if (u2_reading > 30 and u2_reading < 100):
            print(u2_reading)
            sum2 = 0
            for i in range(5):
                sum2 = sum2 + sonar2.get_distance()
            avg = sum2/ 5
            if 0 <= abs(u2_reading - avg) <= 0.2:
                print("Ultra 2 detected")
                if (u1_sensor_flag):
                    print("a person is entering")
                    if (not is_entering):
                        enter_file = open('enter.txt', 'w')
                        enter_file.write("1")
                        enter_file.close()
                    is_entering = True
                    u1_sensor_flag = False
                    u2_sensor_flag = False
                    last_entered_time = time.time()
                else:
                    if (time.time() - last_entered_time > 2):
                        u2_sensor_flag = True
                print(u2_sensor_flag)                        
        else:
            if (is_entering and time.time() - last_entered_time > 10):
                enter_file = open('enter.txt', 'w')
                enter_file.write("")
                enter_file.close()
                is_entering = False
        
        u3_reading = sonar3.get_distance()
        if (u3_reading > 30 and u3_reading < 100):
            print(u3_reading)
            sum3 = 0
            for i in range(5):
                sum3 = sum3 + sonar3.get_distance()
            avg = sum3/ 5
            if 0 <= abs(u3_reading - avg) <= 0.2:
                print("Ultra 3 detected")
                authenticated_file = open("authenticated.txt", "r")
                if time.time() - last_entered_time < 20 and not authenticated_file.read():
                    thread = threading.Thread(target=buzz, name='buzz')
                    if not prev_thread or not prev_thread.is_alive():
                        thread.start()
                        prev_thread = thread
                authenticated_file.close()
                
                
                
        time.sleep(0)


if __name__ == '__main__':
    main()




