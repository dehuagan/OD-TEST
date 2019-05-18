# -*-coding:utf-8 -*-
import socket
import numpy
from math import log10
import threading
import queue
from time import sleep
from flask_cors import CORS
from flask import Flask,render_template,request
from flask import jsonify
import time
import json
import os
app = Flask(__name__)
CORS(app, supports_credentials=True)
class Creat_UDP_Connect(threading.Thread):

    def __init__(self):
        self.collect_addr = []
        self.board_address_and_LED_situation = {}  # {address：[[LED_OFF],[LED_ON]]}
        self.PC_name = socket.gethostname()
        self.UDP_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.PC_address = socket.gethostbyname(self.PC_name)
        self.UDP_sock.bind((self.PC_address, 8080))
        threading.Thread.__init__(self)

    def run(self):
        while True:
            self.OD_raw_value_ascii = self.UDP_sock.recvfrom(1024)

            self.OD_raw_value = self.OD_raw_value_ascii[0][9:12].decode('utf-8')
            self.times = 2
            self.sums = []
            for items in self.OD_raw_value:
                if items.isdecimal():
                    self.number = ord(items) - 48
                    self.number = self.number * 16 ** self.times
                    self.sums.append(self.number)
                else:
                    self.number = ord(items) - 87
                    self.number = self.number * 16 ** self.times
                    self.sums.append(self.number)
                self.times -= 1
            self.OD_raw_value = sum(self.sums)
            self.get_board_address = int(self.OD_raw_value_ascii[0][2:4])
            self.get_board_situation = int(chr(self.OD_raw_value_ascii[0][5]))

            if self.get_board_address not in self.board_address_and_LED_situation:
                self.collect_addr.append(self.get_board_address)
                self.board_address_and_LED_situation[self.get_board_address] = \
                    [queue.Queue(maxsize=100), queue.Queue(maxsize=100)]

                # print('self.board_address_and_LED_situation=',self.board_address_and_LED_situation)
                # print('self.get_board_situation=',self.get_board_situation)
                self.board_address_and_LED_situation[self.get_board_address] \
                    [self.get_board_situation].put(self.OD_raw_value)

            else:  # 此时需要判断队列是否装满
                if self.board_address_and_LED_situation[self.get_board_address] \
                        [self.get_board_situation].full():
                    self.board_address_and_LED_situation[self.get_board_address] \
                        [self.get_board_situation].get()
                    self.board_address_and_LED_situation[self.get_board_address] \
                        [self.get_board_situation].put(self.OD_raw_value)
                else:
                    self.board_address_and_LED_situation[self.get_board_address] \
                        [self.get_board_situation].put(self.OD_raw_value)
            # print(self.board_address_and_LED_situation)


class Sensor:
    def __init__(self, board_name, polynomial_fun, blank_value,data_source):
        self.board_name = board_name
        self.polynomial_fun = polynomial_fun
        self.blank_value = blank_value
        self.raw_value = []
        self.data_source = data_source

    def get_raw_value(self, sample_number=5):
        self.raw_value = []
        self.sample_number = sample_number
        for i in range(self.sample_number):
            self.LED_ON_mi_LED_OFF = self.data_source[self.board_name][1].get() - \
                                     self.data_source[self.board_name][0].get()
            self.raw_value.append(self.LED_ON_mi_LED_OFF)
        return self.raw_value

    @property
    def get_average_raw_value(self):
        self.average_raw_value = numpy.average(self.raw_value)
        return self.average_raw_value

    @property
    def get_var_raw_value(self):
        print(self.raw_value)
        self.var_raw_value = numpy.var(self.raw_value)
        return self.var_raw_value

    @property
    def get_real_OD(self):
        self.var = self.get_var_raw_value
        self.average = self.get_average_raw_value
        self.max_limit = self.average+self.average * 0.013
        self.min_limit = self.average-self.average * 0.013

        self.raw_value = filter(lambda x: x > self.min_limit and x < self.max_limit, self.raw_value)
        self.raw_value = list(self.raw_value)
        self.average = numpy.average(self.raw_value)

        self.log10_I0_div_Ia = log10(self.blank_value / self.average)

        x = self.log10_I0_div_Ia
        self.rough_OD = eval(self.polynomial_fun)
        if self.rough_OD < 0.7:
            if self.var <= 1000:  # steady
                # print('进入此处111')
                self.max_limit = self.average+self.average * 0.006
                self.min_limit = self.average-self.average * 0.013
                self.raw_value = filter(lambda x: x > self.min_limit and x < self.max_limit, self.raw_value)
                self.raw_value = list(self.raw_value)

                self.average = numpy.average(self.raw_value)
                self.log10_I0_div_Ia = log10(self.blank_value / self.average)
                x = self.log10_I0_div_Ia
                self.OD = eval(self.polynomial_fun)
                return self.OD
            else:  # stir
                # print('进入此处222')
                self.max = max(self.raw_value)
                self.log10_I0_div_Ia = log10(self.blank_value / self.max)
                x = self.log10_I0_div_Ia
                self.OD = eval(self.polynomial_fun)
                return self.OD

        else:
            if self.var <= 500:  # steady
                # print('进入此处333')
                self.max_limit = self.average+self.average * 0.006
                self.min_limit = self.average-self.average * 0.013

                self.raw_value = filter(lambda x: x > self.min_limit and x < self.max_limit, self.raw_value)
                self.raw_value = list(self.raw_value)

                self.average = numpy.average(self.raw_value)
                self.log10_I0_div_Ia = log10(self.blank_value / self.average)
                x = self.log10_I0_div_Ia
                self.OD = eval(self.polynomial_fun)
                return self.OD
            else:  # stir
                # print('进入此处444')
                self.max = max(self.raw_value)
                self.log10_I0_div_Ia = log10(self.blank_value / self.max)
                x = self.log10_I0_div_Ia
                self.OD = eval(self.polynomial_fun)
                return self.OD


@app.route('/update_chart',methods=['GET','POST'])
def update_chart():
    if request.method == 'POST':
        para = json.loads(request.get_data())
        board_name = para["board_name"]
        polynomial_fun = para["polynomial_fun"]
        blank_value = para["blank_value"]



        data = {}

        for i in range(len(board_name)):
            s = Sensor(board_name[i],polynomial_fun[i],blank_value[i],a.board_address_and_LED_situation)
            v = s.get_raw_value()
            data[i] = s.get_real_OD

        str = os.getcwd() + '\savefile.txt'
        with open(str, 'a', encoding='utf-8-sig', newline='') as f:
            f.write(json.dumps(data))
            f.write('\n')
        print('data=====>',data)
        t = time.strftime('%y-%m-%d %H:%M', time.localtime())
        res = jsonify({'data': data, 'time': t})
        return res


@app.route('/initialize',methods=['GET','POST'])
def initialize():
    return a.collect_addr










if __name__ == "__main__":
    a = Creat_UDP_Connect()
    a.start()
    sleep(2)

    app.run(debug=True)

