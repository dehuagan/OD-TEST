# encoding:utf-8
# !/usr/bin/env python
from flask import Flask, render_template
from socket import *
from flask_socketio import SocketIO, emit
import time
from time import sleep
import binascii
from symbol import except_clause
import sys
import threading
from threading import Lock
from _socket import gethostname

from threading import Lock

from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit

import time
from threading import Lock
from flask import Flask, render_template
from flask_socketio import SocketIO

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = threading.Lock()

result_list = []
def getod():
    print('getod is running')
    name = gethostname()
    UDP_sock = socket(AF_INET, SOCK_DGRAM)
    address1 = gethostbyname(name)
    print(address1)

    UDP_sock.bind((address1, 8080))
    while True:
        sleep(1)
        ODrawvalue_ascll = UDP_sock.recvfrom(10000)
        ODrawvalue_ascll = ODrawvalue_ascll[0][2:5].decode('utf-8')
        times = 2
        sums = []
        for items in ODrawvalue_ascll:
            if items.isdecimal():
                number = ord(items) - 48
                number = number * 16 ** times
                sums.append(number)
            else:
                number = ord(items) - 87
                number = number * 16 ** times
                sums.append(number)
            times -= 1
        # sleep(1)
            result_list.append(sum(sums))
        del (ODrawvalue_ascll)
# 后台线程 产生数据，即刻推送至前端
def background_thread():
    count = 0
    print('background is running')
    while True:

        print(result_list)
        # if(result_list):
        # else:
        socketio.sleep(1)
        count += 1
        t = time.strftime('%y-%m-%d %H:%M:%S', time.localtime())
        if(result_list):
            socketio.emit('server_response',
                      {'data': [result_list[-3],result_list[-2],result_list[-1]], 'time': t},
                      namespace='/test')



@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@socketio.on('connect', namespace='/test')
def test_connect():
    t1 = threading.Thread(target=background_thread)
    t2 = threading.Thread(target=getod)
    t2.start()

    t1.start()



if __name__ == '__main__':
    socketio.run(app, debug=True)
