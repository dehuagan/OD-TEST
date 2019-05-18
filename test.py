#!/usr/bin/env python
# -*- coding: utf-8 -*-
import flask
from flask_cors import *
import random
from flask import Flask
from flask import jsonify
import threading
import time
app = Flask(__name__)
CORS(app, supports_credentials=True)
testarr = []
def geta():
    while True:
        time.sleep(5)
        t = time.strftime('%y-%m-%d %H:%M:%S', time.localtime())

        a = random.randint(1, 100)
        b = a * 10
        c = a * 20
        d = a * 5
        e = a * 1.5
        testarr.append(a)
        print(a)
t1 = threading.Thread(target=geta)
t1.start()
@app.route('/test',methods=['GET','POST'])
def get_result():


    response = jsonify({'data':testarr})
    return response



if __name__ == '__main__':
    app.run(debug=True)