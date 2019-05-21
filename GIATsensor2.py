# -*-coding:utf-8 -*-
import numpy
import queue
import random
import re
import socket
import threading

from math import log10, pow
from time import sleep,time
from flask_cors import *

from flask import Flask
from flask import jsonify


app = Flask(__name__)
CORS(app, supports_credentials=True)
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
    def __init__(self, port = 8080, simulate = False):
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
        self.UDP_sock.close()
        if not self.thread.isAlive():
            print('loop has been terminated')
        else:
            print('Unable to terminate')

    def __call__(self):
        data_and_reception_time = {} #format｛address:{LED_ON:ddd,LED_OFF:ddd,TIME:ddd}｝
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
                '''In fact, it can be done as long as it is more than 42. For example, self. UDP_sock. recvfrom 
                (42), which receives three data at a time instead of one, is explained in detail below.'''
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
                '''It used to be spaced, but now it's changed to send three together, such as 
                "b'0x05:0:0x01a r n0x05:0:0x01c r n0x05:0:0x01c n0x05:0:0x01c r n'
                This is the data sent once, with no time interval between them. Previously, 
                I discussed with Liden that the purpose of doing this is to increase the sampling frequency. 
                However, from the data collected, there is not much difference between the three data, 
                so only the first data can be read. In the code I sent you this time, I improved it.'''
                received_data = self.UDP_sock.recvfrom(1024)

            # analyze received data
            # note: received_data is a tuple, the bytes are in part [0] of the tuple
            #       see https://docs.python.org/3.6/library/socket.html -> socket.recvfrom(...)
            received_data = received_data[0].decode('utf-8')
            # do we need to use regular expression to check if the data has the correct format?
            '''
            The data sent from router follows a fixed data structure. I don't think it's necessary to 
            use regular expressions to detect it. But it's okay to do so.
            '''
            try:
                #0xAA:S:0xDDD\r\n
                received_data_frames = re.findall(r'0x([0-9a-fA-F]{2}):([0-1]):0x([0-9a-fA-F]{3})', received_data)
                #此时接收的数据是received_data_frames=[('03', '1', '714'), ('03', '1', '709'), ('03', '1', '706')]
            except:
                continue # start at the beginning of the loop
            # COMMENT for Yu Ming:
            # removed duplicate code and simplified if-cases:
            raw_value = []
            for (address, state, rawvalue) in received_data_frames:
                address   = int(address, 16)
                state     = 'LED_OFF' if state == '0' else 'LED_ON'
                raw_value.append(int(rawvalue, 16))
                # print("address=", address,"state=", state, 'raw_value=', raw_value)
            raw_value = numpy.average(raw_value)
            if address not in self.data_buffer:
                # create the data buffer if necessary
                #To prevent threads from losing synchronization caused by resource preemption,
                # it is possible that LED_OFF and LED_ON form a list and then put it in the queue.
                self.data_buffer[address] = queue.Queue(maxsize=self.max_queue)#数据格式queue = [[LED_OFF,LED_ON],……]
                data_and_reception_time[address] = {}
                data_and_reception_time[address]['time'] = time()

            '''If there are several modules, the time interval for receiving data will be longer. 
            When testing individual modules, the time interval will be about 0.5s.'''
            if  time() - data_and_reception_time[address]['time']>=len(self.data_buffer)*0.5:
                # print('清chu数据           =',data_and_reception_time,'时间差=',time() - data_and_reception_time[address]['time'])
                data_and_reception_time[address] = {}#清空所有
                # print('清空后进入内部=',data_and_reception_time)
            data_and_reception_time[address]['time'] = time()
            data_and_reception_time[address][state] = raw_value
            # print('清空后=', data_and_reception_time)

            '''Change the original one-after-one data storage mode to one-after-one pair storage mode, 
            and add it to the queue whenever a pair of data is available.'''
            #FIXME
            #we assume that the values for LED_ON and LED_OFF arrive in the correct sequence
            #later we will rely on the sequence of the values only to determine the difference LED_ON-LED_OFF
            #we should make the algorithm more robust by
            # 1) reading LED_ON
            # 2) trying to read LED_OFF for no longer than X seconds
            # 3) if timeout: invalidate LED_ON measurement and try again
            # 4) if both value arrived within timout period: store the (LED_ON, LED_OFF) tuple in the data buffer
            if len(data_and_reception_time[address]) == 3:
                # print('装满一对=',data_and_reception_time[address])
                if self.data_buffer[address].full():
                    # make room for a new value if buffer is full
                    self.data_buffer[address].get()

                    self.data_buffer[address].put([data_and_reception_time[address]['LED_OFF'],
                                                   data_and_reception_time[address]['LED_ON']]
                                                  )
                    del data_and_reception_time[address]['LED_OFF']
                    del data_and_reception_time[address]['LED_ON']
                else:
                    self.data_buffer[address].put([data_and_reception_time[address]['LED_OFF'],
                                                   data_and_reception_time[address]['LED_ON']]
                                                  )
                # print('获取数据=',self.data_buffer[address].get())
                # self.data_buffer[address][state].put(raw_value)
#                 sleep(0.01)
    #FIXME
    #here we can add some code to release the port binding after the loop has been terminated
    '''
        I added some code to the stop_function you wrote earlier.
    '''

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
            for sample_pair in range(sample_number):
                data = self.data_source[self.address].get()
                difference = data[1]-data[0]
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
        '''This is based on the experimental results.For more details,
        please check the original experimental data and ppt I sent to you.'''
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
        '''
        Please see the attached data and ppt I sent you. Ppt was used by me in the report of the Biological Center 
        on May 9, which introduced some computational processes. In short, I did this to make the results as accurate
        as possible. (Maybe this is not the best way)
        '''

        return self.function(self.average_difference)


udp = UDP_Data_Collector(simulate = False)
udp.start()
sleep(2)
# while True:
print('udp.data_buffer=',udp.data_buffer)
    # sleep(1)


@app.route('/initialize',methods=['GET','POST'])
def initialize():


    response = jsonify({'data':list(udp.data_buffer.keys())})
    return response


@app.route('/test',methods=['GET','POST'])
def test():
    return 'test success'



if __name__ == "__main__":
    app.run(debug=True)
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
    # udp = UDP_Data_Collector(simulate = False)
    # udp.start()
    # sleep(2)
    # while True:
    #     print('udp.data_buffer=',udp.data_buffer)
    #     sleep(1)

    # sensor = Sensor(0x03,
    #        Polynomial([-0.00456, 3.743, -1.0704, 2.379], scaling=1713.21153846, inverse=True),
    #        udp.data_buffer
    #        )

    # sensors = []
    # sensors.append(Sensor(0x01,
    #                       lambda x: log10(1023/x),
    #                       udp.data_buffer
    #                       ))
    # sensors.append(Sensor(0x03,
    #                       Polynomial([-0.00456, 3.743, -1.0704, 2.379], scaling=1713.21153846, inverse = True),
    #                       udp.data_buffer
    #                       ))
    # sensors.append(Sensor(0x05,
    #                       YuMingFunction([-0.00456, 3.743, -1.0704, 2.379], blank=1713.21153846),
    #                       udp.data_buffer
    #                       ))

    # while True:
    #     print('Sensor with address <{:02x}>'.format(sensor.address))
    #     sensor.get_differences()
    #     print('raw differences    =', sensor.differences)
    #     print('average difference =', sensor.average_difference)
    #     print('OD estimate        =', sensor.OD)
    #     print('data_buffer=',sensor.data_source)
    # for sensor in sensors:
    #     print('Sensor with address <{:02x}>'.format(sensor.address))
    #     sensor.get_differences()
    #     print('raw differences    =', sensor.differences)
    #     print('average difference =', sensor.average_difference)
    #     print('OD estimate        =', sensor.OD)


    # because this test is based on simulated data, the 3 sensors below have the same
    # address but they use different calibration functions
    # sensors = []
    # sensors.append(Sensor(0x02,
    #                       lambda x: log10(1023/x),
    #                       udp.data_buffer
    #                       ))
    # sensors.append(Sensor(0x03,
    #                       Polynomial([-0.00456, 3.743, -1.0704, 2.379], scaling=1713.21153846, inverse = True),
    #                       udp.data_buffer
    #                       ))
    # sensors.append(Sensor(0x05,
    #                       YuMingFunction([-0.00456, 3.743, -1.0704, 2.379], blank=1713.21153846),
    #                       udp.data_buffer
    #                       ))

    # for sensor in sensors:
    #     print('Sensor with address <{:02x}>'.format(sensor.address))
    #     print('LED_ON queue length = '+str(sensor.data_source[0x02]['LED_ON'].qsize()))
    #     print('LED_ON queue length = '+str(sensor.data_source[0x02]['LED_OFF'].qsize()))
    #     sensor.get_differences()
    #     print('raw differences    =', sensor.differences)
    #     print('average difference =', sensor.average_difference)
    #     print('OD estimate        =', sensor.OD)
    #     print()

    # udp.stop()
