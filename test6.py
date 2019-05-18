# # encoding:utf-8
# # !/usr/bin/env python
# import random
# import time
# from threading import Lock
# from flask import Flask, render_template
# from flask_socketio import SocketIO
#
# async_mode = None
# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, async_mode=async_mode)
# thread = None
# thread_lock = Lock()
#
# # setsec = 1
# # 后台线程 产生数据，即刻推送至前端
# def background_thread():
#     count = 0
#     while True:
#         socketio.sleep(1)
#         count += 1
#         t = time.strftime('%y-%m-%d %H:%M:%S', time.localtime())
#         # 获取系统时间（只取分:秒）
#         a = random.randint(1,100)
#         b = a*10
#         c = a*20
#         d = a*5
#         e = a*1.5
#         # 获取系统cpu使用率 non-blocking
#         # print([a,b,c,d])
#         # print(time)
#         socketio.emit('server_response',
#                       {'data': [a, b, c,d,e], 'time': t},
#                       namespace='/test')
#         # 注意：这里不需要客户端连接的上下文，默认 broadcast = True
#
#
# @app.route('/')
# def index():
#     return render_template('index.html', async_mode=socketio.async_mode)
#
#
# @socketio.on('my event', namespace='/test')
# def test_message(s):
#     print('reveived ...'+s['data'])
#     setsec = s['data']
#
# @socketio.on('connect', namespace='/test')
# def test_connect():
#     global thread
#     with thread_lock:
#         if thread is None:
#             thread = socketio.start_background_task(target=background_thread)
#
#
# if __name__ == '__main__':
#     socketio.run(app, debug=True)


x = 3
f = 'x+4'
print(eval(f))