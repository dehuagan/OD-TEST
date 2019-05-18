# -*-coding:utf-8 -*-
import numpy
import queue
import random
import re
import socket
import threading

from math import log10, pow
from time import sleep

class UDP_Data_Collector():
    ''''
    An instance of this class can listen on a specified port and collect
    sensor data that arrives as b'0xAA:S:0xDDD\r\n' with 
    AA=sensor address, 
    S=sensor state (0=LED+OFF, 1=LED_ON) and 
    DDD=sensor raw data.

    Data for both states is stored in a data_buffer, 
    a maximum on self.queue_length values is kept. 
    '''
    def __init__(self, port = 8000, simulate = False):
        # the data buffer maps the sensor address to the last received data:
        # {address: {'LED_ON': queue with values, 'LED_OFF': queue with values}}
        self.data_buffer = {}  
        self.PC_name     = socket.gethostname()
        self.PC_address  = socket.gethostbyname(self.PC_name)
        self.port        = port
        self.simulate    = simulate
        self.is_running  = False

        self.max_queue   = 14

    def start(self):
        self.UDP_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDP_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.UDP_sock.bind((self.PC_address, self.port))
        self.thread  = threading.Thread(target=self, group=None, daemon=True)
        self.is_running = True
        print('loop has been started')
        self.thread.start()

    def stop(self):
        self.is_running = False

    def __call__(self):
        while self.is_running:
            if self.simulate:
                # toggle or initialize simulated state
                try: 
                    simulated_state = abs(simulated_state - 1) 
                except:
                    simulated_state = 0
                # simulate 10, 20 for LED_OFF and 1000, 1020 for LED_ON on sensor with address 0x01
                simulated_string = '0x01:{:d}:0x{:03x}\r\n0x01:{:d}:0x{:03x}\r\n'.format(
                                    simulated_state, 
                                    10+simulated_state*990,
                                    simulated_state, 
                                    20+simulated_state*1000,
                                    )
                received_data    = (bytes(simulated_string.encode('utf-8')), None)
            else:
                #FIXME: why are we reading 1024 bytes at a time?
                #       shouldn't we read 14 bytes at a time?
                #       '0xAA:S:0xDDD'+'\r\n'
                #FIXME: the sample data Yuming sent has 3 measurements for each sensor, e.g.:
                #       0x05:0:0x01d
                #       0x05:0:0x01f
                #       0x05:0:0x01f
                #       0x03:0:0x061
                #       0x03:0:0x062
                #       0x03:0:0x062
                #       0x02:0:0x02c
                #       0x02:0:0x02d
                #       0x02:0:0x02d
                #       ...
                #       are those 3 readings received at the same time or after a time delay?
                received_data = self.UDP_sock.recvfrom(1024)

            # analyze received data
            # note: received_data is a tuple, the bytes are in part [0] of the tuple
            #       see https://docs.python.org/3.6/library/socket.html -> socket.recvfrom(...)
            received_data = received_data[0].decode('utf-8')
            # FIXME
            # do we need to use regular expression to check if the data has the correct format?
            try: 
                received_data_frames = re.findall(r'0x([0-9a-fA-F]{2}):([0-1]):0x([0-9a-fA-F]{3})', received_data)
            except:
                continue # start at the beginning of the loop
            # COMMENT for Yu Ming:
            # removed duplicate code and simplified if-cases: 
            for (address, state, raw_value) in received_data_frames:
                address   = int(address, 16)
                state     = 'LED_OFF' if state == '0' else 'LED_ON'
                raw_value = int(raw_value, 16)
                if address not in self.data_buffer:
                    # create the data buffer if necessary
                    self.data_buffer[address] = {'LED_OFF': queue.Queue(maxsize=self.max_queue), 
                                                'LED_ON' : queue.Queue(maxsize=self.max_queue)
                                                }
                if self.data_buffer[address][state].full():
                    # make room for a new value if buffer is full
                    self.data_buffer[address][state].get()

                #FIXME
                #we assume that the values for LED_ON and LED_OFF arrive in the correct sequence
                #later we will rely on the sequence of the values only to determine the difference LED_ON-LED_OFF
                #we should make the algorithm more robust by 
                # 1) reading LED_ON
                # 2) trying to read LED_OFF for no longer than X seconds
                # 3) if timeout: invalidate LED_ON measurement and try again
                # 4) if both value arrived within timout period: store the (LED_ON, LED_OFF) tuple in the data buffer
                self.data_buffer[address][state].put(raw_value)
                sleep(0.01)
        
        #FIXME
        #here we can add some code to release the port binding after the loop has been terminated
        print('loop has been terminated')

class Polynomial():
    '''
    Instances of this class implement a polynomial function 
    f(x) = a0 + a1*X(x) + a2*X(x)^2 + .... an*X(x)^n
    X(x) = x/scaling  for inverse = False
    X(x) = scaling/x  for inverse = True
    '''

    def __init__(self, coeffs = None, scaling = 1, inverse = False):
        self.coeffs  = [0, 1] if coeffs is None else coeffs
        self.scaling = scaling
        self.inverse = inverse

    def __call__(self, x):
        x = x / self.scaling
        if self.inverse:
            x = 1/x
        return sum(coefficient*pow(x, i) for i, coefficient in enumerate(self.coeffs))

class YuMingFunction():
    '''
    Implements a rather complex curve fitting function suggested by Yuming:
    log10(blank/x) is also additionally processed by a polynomial fitting function.
    '''
    def __init__(self, coeffs = None, blank=4095):
        self.coeffs = [0, 1] if coeffs is None else coeffs
        self.blank  = blank

    def __call__(self, x):
        X = log10(self.blank/x)
        return sum(coefficient*pow(X, i) for i, coefficient in enumerate(self.coeffs))

class Sensor:
    '''
    An instance of the Sensor class will get the required number of measurements from the data source
    and then use a calibration function to convert the raw values to a measure in the required units, e.g. as OD. 
    '''
    def __init__(self, address, function, data_source):
        self.address     = address
        self.function    = function
        self.differences = []
        self.data_source = data_source

    def get_differences(self, sample_number=5):
        '''
        read a number of measurements from the data_source's raw value buffer
        and calculate the differences LED_ON-LED_OFF
        '''
        self.differences = []
        try:
            for _ in range(sample_number):
                difference = self.data_source[self.address]['LED_ON'].get()-self.data_source[self.address]['LED_OFF'].get()
                self.differences.append(difference)
        except:
            pass
        return self.differences

    @property
    def average_difference(self):
        return numpy.average(self.differences)

    @property
    def variance(self):
        return numpy.var(self.differences)

    @property
    def OD(self):
        #FIXME:
        #why did you choose 1.3% as threshold?
        limit = 0.013
        max_limit = self.average_difference*(1+limit)
        min_limit = self.average_difference*(1-limit)

        # remove outliers from the set of differences:
        # note: because we are using self.differences, the @property functions now
        #       automatically work on the filtered differences!
        self.differences = list(filter(lambda x: x > min_limit and x < max_limit, self.differences))

        # FIXME:
        # I have removed the follwing code
        #
        # if rough_OD small:
        #    if variance small:
        #        filter again (why do we filter again?)
        #    else (variance high because of stirring):
        #        use maximum value instead of average
        # else (roughOD is large):
        #    if variance small:
        #        filter again (why do we filter again?)
        #    else (variance high because of stirring):
        #        use maximum value instead of average
        #
        # Please explain what you are trying to do here ... do you have raw data or a digram to 
        # explain why handle these cases diferently? Why did you filter the values 2 times?

        return self.function(self.average_difference)

if __name__ == "__main__":

    # test the calibration functions
    f1 = Polynomial(coeffs=[5,1.5,10], scaling=100, inverse=False)
    assert f1(0)  == 5 + 1.5*0 + 10*0*0, 'something is wrong with f1(0)'
    assert f1(200)== 5 + 1.5*2 + 10*2*2, 'something is wrong with f1(200)'  

    f2 = Polynomial(coeffs=[5,1.5,10], scaling=10, inverse=True)
    assert f2(100) == 5 + 1.5*0.1 + 10*0.1*0.1, 'something is wrong with f2(100)'
    assert f2(1)   == 5 + 1.5*10 + 10*10*10   , 'something is wrong with f2(1)'  

    f3 = YuMingFunction(coeffs=[1,3,7], blank=1000)
    assert f3(100) == 1 + 3*1 + 7*1*1, 'something is wrong with f3(100)' # note 1 = LOG10(1000/100)
    assert f3(10)  == 1 + 3*2 + 7*2*2, 'something is wrong with f3(10)'  # note 2 = LOG10(1000/10)

    # test the 
    udp = UDP_Data_Collector(simulate = True)
    udp.start()
    sleep(2)

    # because this test is based on simulated data, the 3 sensors below have the same
    # address but they use different calibration functions
    sensors = []
    sensors.append(Sensor(0x01, 
                          lambda x: log10(1023/x), 
                          udp.data_buffer
                          ))
    sensors.append(Sensor(0x01, 
                          Polynomial([-0.00456, 3.743, -1.0704, 2.379], scaling=1713.21153846, inverse = True),
                          udp.data_buffer
                          ))
    sensors.append(Sensor(0x01, 
                          YuMingFunction([-0.00456, 3.743, -1.0704, 2.379], blank=1713.21153846),
                          udp.data_buffer
                          ))

    for sensor in sensors:
        print('Sensor with address <{:02x}>'.format(sensor.address))
        print('LED_ON queue length = '+str(sensor.data_source[0x01]['LED_ON'].qsize()))
        print('LED_ON queue length = '+str(sensor.data_source[0x01]['LED_OFF'].qsize()))
        sensor.get_differences()
        print('raw differences    =', sensor.differences)
        print('average difference =', sensor.average_difference)
        print('OD estimate        =', sensor.OD)
        print()

    udp.stop()