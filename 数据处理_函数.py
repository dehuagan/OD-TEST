# -*- coding: utf-8 -*-
from socket import *
import numpy
from math import log10
import flask

from flask_cors import *
from flask import Flask,render_template
from flask import jsonify
import threading
import os
import time
import json

app = Flask(__name__)
CORS(app, supports_credentials=True)


def initialization(board_address):#初始化
    global all_board_address,UDP_sock,OD_collect,OD_sit,OD_raw_value_ON_OFF,value_ON_and_OFF

    all_board_address = board_address
    name = gethostname()
    UDP_sock = socket(AF_INET,SOCK_DGRAM)
    address1 = gethostbyname(name)
    UDP_sock.bind((address1,8080))

    OD_collect = {}#用于收集地址及OD，格式为｛地址.LED状态：[OD值]｝如｛2.1:2251｝
    OD_sit = {}#用于记录状态的变化，格式为｛板子地址：LED状态｝如｛2:1｝

    OD_raw_value_ON_OFF = {x:[] for x in all_board_address}#用于记录板子开灯减关灯的值
    value_ON_and_OFF = {}
    value_ON_and_OFF.update({str(float(x)):[]for x in all_board_address})
    value_ON_and_OFF.update({str((x+0.1)):[]for x in all_board_address})

def read_save_print_output(print_number=110,print_borad=3,save_='yes',print_='yes',file_dir='F:\\test\\'):
    '''
    用于读取，保存和打印数据
    :param print_number: 打印出来的个数
    :param print_borad: 需要打印出来的板子
    :save_:是否需要保存
    :print_:是否需要打印
    :file_dir:保存文件所在的文件夹
    :return:返回每个板子对应的开灯数据减去关灯数据，字典
    '''
    the_number_of_LED_on = 0
    the_number_of_LED_off = 0
    while True:
        OD_raw_value_ascll = UDP_sock.recvfrom(1024)
        OD_raw_value = OD_raw_value_ascll[0][9:12].decode('utf-8')
        times = 2
        sums = []
        for items in OD_raw_value:
            if items.isdecimal():
                number = ord(items)-48
                number = number*16**times
                sums.append(number)
            else:
                number = ord(items)-87
                number = number*16**times
                sums.append(number)
            times-=1
        OD_raw_value = sum(sums)

        board_address = int(OD_raw_value_ascll[0][2:4])
        board_situation = chr(OD_raw_value_ascll[0][5])
        board_address_situation = '.'.join((str(board_address), str(board_situation)))
        if save_== 'yes':
            if board_address not in OD_sit:
                file_path_name = file_dir+'BOARD%s_OFF.txt' % board_address
                with open(file_path_name, 'w') as LED_OFF_FILE:
                    pass
                file_path_name = file_dir+'BOARD%s_ON.txt' % board_address
                with open(file_path_name, 'w') as LED_ON_FILE:
                    pass
        #存储与板子地址及状态对应的OD值
        if board_address_situation not in OD_collect:
            OD_collect.update({board_address_situation:[OD_raw_value]})
        else:
            OD_collect[board_address_situation].append(OD_raw_value)

        # 判断板子的开关灯状态变化,状态发生改变则输出
        if board_address not in OD_sit:
            OD_sit.update({board_address: int(board_situation)})

        else:
            if int(board_situation) - OD_sit[board_address] == 1:  # 从关灯到开灯
                OD_sit[board_address] = int(board_situation)  # 存储最新的灯的状态
                OD_output = round(sum(OD_collect[str(board_address) + '.0']) / \
                                       len(OD_collect[str(board_address) + '.0']), 3)
                OD_collect[str(board_address) + '.0'] = []  # 清除关灯状态的数据

                #接下来计算开灯状态减去关灯状态的值
                value_ON_and_OFF[str(board_address) + '.0'] = OD_output#记录关灯的状态
                if value_ON_and_OFF[str(board_address) + '.1'] == [] or value_ON_and_OFF[str(board_address) + '.0'] == []:
                    pass
                else:
                    OD_raw_value_ON_OFF[board_address].append(value_ON_and_OFF[str(board_address) + '.1']\
                                                         -value_ON_and_OFF[str(board_address) + '.0'])
                    value_ON_and_OFF[str(board_address) + '.0'] = []
                    value_ON_and_OFF[str(board_address) + '.1'] = []

                #存储数据
                if save_ == 'yes':
                    file_path_name = file_dir+'BOARD{num}_OFF.txt'.format(num=board_address)
                    with open(file_path_name, 'a') as LED_OFF_FILE:  # 把数据存储到对应的板子的文件
                        LED_OFF_FILE.write(str(OD_output) + '\n')
                if board_address == print_borad and print_=='yes':
                    print('设备{a} 关灯  ODrawvalue={b}'.format(a=print_borad, b=OD_output))
                    if the_number_of_LED_on <= print_number:
                        the_number_of_LED_on += 1
                    else:
                        break

            elif int(board_situation) - OD_sit[board_address] == -1:  # 从开灯到关灯

                OD_sit[board_address] = int(board_situation)  # 存储最新的灯的状态
                OD_output = round(sum(OD_collect[str(board_address) + '.1']) / \
                                  len(OD_collect[str(board_address) + '.1']), 3)
                OD_collect[str(board_address) + '.1'] = []  # 清除开灯状态的数据
                # 接下来计算开灯状态减去关灯状态的值
                value_ON_and_OFF[str(board_address) + '.1'] = OD_output#记录开灯的状态
                if value_ON_and_OFF[str(board_address) + '.0'] == [] or value_ON_and_OFF[str(board_address) + '.1'] == []:
                    pass
                else:
                    OD_raw_value_ON_OFF[board_address].append(value_ON_and_OFF[str(board_address) + '.1']- \
                                                              value_ON_and_OFF[str(board_address) + '.0'])

                    value_ON_and_OFF[str(board_address) + '.0'] = []
                    value_ON_and_OFF[str(board_address) + '.1'] = []

                #存储数据
                if save_ == 'yes':
                    file_path_name = file_dir+'BOARD{num}_ON.txt'.format(num=board_address)
                    with open(file_path_name, 'a') as LED_OFF_FILE:  # 把数据存储到对应的板子的文件
                        LED_OFF_FILE.write(str(OD_output) + '\n')
                if board_address == print_borad and print_=='yes':
                    print('设备{a} 开灯  ODrawvalue={b}'.format(a=print_borad, b=OD_output))
                    if the_number_of_LED_off <= print_number:
                        the_number_of_LED_off += 1
                        print('数量……', the_number_of_LED_off)
                    else:
                        break
            else:  # 状态没有改变
                pass
    UDP_sock.close()
    return OD_raw_value_ON_OFF

def save_OD_raw_value(data=[],file_dir=r'F:\test\----dif.txt'):
    '''
    用于保存OD raw value(LED_ON-LED_OFF)
    :param data: 所有板子的OD raw value
    :param file: 保存数据的文件
    '''
    global min_len
    min_len=[]
    for board in all_board_address:
        min_len.append(len(data[board]))
    min_len = min(min_len)
    min_len = min_len if min_len <= 108 else 108
    print('长度……=',min_len)

    with open(file_dir,'w')as file:
        for j in range(min_len):
            for i in all_board_address:
                file.write(str(data[i][j])+'\t')
            file.write('\n')
        for i in range(3):#多空几行
            file.write('\n')

def clc_var_ave(file_dir=r'F:\test\----dif.txt',save_='yes'):
    '''
    #计算方差、平均值
    #初步将方差阈值订在450，超过这个数，则认为发酵罐处于搅动状态
    :param file_dir: 保存数据的文件路径
    :param save_: 是否需要保存文件
    '''
    global var,ave
    var = []
    ave = []
    for i in all_board_address:
        var.append(numpy.var(OD_raw_value_ON_OFF[i][:min_len]))
        ave.append(numpy.average(OD_raw_value_ON_OFF[i][:min_len]))
    if save_ == 'yes':
        with open(file_dir,'a') as file:
            for i in var:
                file.write(str(i)+'\t')
            file.write('\n')
            for i in ave:
                file.write(str(i) + '\t')
            file.write('\n')
    # print('var',var)
    # print('ave',ave)

def data_handing(data=[],dt_max=0.013,dt_min=0.013,var_threshold=1000,file_dir_=r'F:\test\----dif.txt',save_='no'):
    '''
    处理数据
    :param dt_max: 上限误差
    :param dt_min: 下限误差
    :param data: OD raw value(LED_ON-LED_OFF)
    :file_dir_: 保存数据的文件路径
    :return:处理后的数据data
    '''
    #确定这些列表的最小长度
    min_len = []
    for board in all_board_address:
        min_len.append(len(data[board]))
    min_len = min(min_len)

    # 删除多余的点,保证列表同样的长度
    for i in all_board_address:
        data[i] = data[i][:min_len]

    #设置置信区间，删除一些偏差较大的点
    for j in all_board_address:
        inde = all_board_address.index(j)
        if var[inde]<=var_threshold:#此时认为它处于静止状态，删除偏离较大的点即可
            print('静止状态')
            max_lim = ave[inde]+ave[inde]*dt_max  #求置信区间的上限
            min_lim = ave[inde]-ave[inde]*dt_min  #求置信区间的下限
            del_data = []#需要被删除的数据
            for k in range(min_len):
                # print('j=',j,'k=',k)
                if data[j][k]>max_lim or data[j][k]<min_lim:
                    del_data.append(data[j][k])
            if del_data != 0:
                for i in del_data:
                    data[j].remove(i)
        else:#此时处于剧烈搅动状态，取最大值
            print('剧烈搅动')
            data[j] = [max(data[j])]

    #保存处理后的OD raw value
    if file_dir_ != '' and save_ == 'yes':
        max_len=[]
        for board in all_board_address:
            max_len.append(len(data[board]))
        max_len = max(max_len)
        with open(file_dir_,'a')as file:
            for i in range(3):#多空几行
                file.write('\n')
            for j in range(max_len):
                for i in all_board_address:
                    if j < len(data[i]):
                        file.write(str(data[i][j])+'\t')
                    else:
                        file.write('' + '\t')
                file.write('\n')
            for i in range(3):#多空几行
                file.write('\n')
    return data

def clc_real_OD(data):
    #计算真实的OD值
    #不同的板子对应不同的方程
    # fun_data = {2:lambda x:1.7168*x**2+3.0301*x+0.004,
    #             3:lambda x:1.7244*x**2+3.0466*x+0.109,
    #             5:lambda x:2.1218*x**2+2.3649*x+0.0464,
    #             6:lambda x:2.3652*x**2+2.6944*x}

    fun_data = {2: lambda x: 2.379*x**3 - 1.0704*x**2 + 3.743*x - 0.0045,
                3: lambda x: 4.258*x**3 - 3.9034*x**2 + 4.9852*x + 0.0959,#
                5: lambda x: 2.5255*x**3 - 1.3582*x**2 + 3.3456*x - 0.0027,
                6: lambda x: 1.5857*x**3 + 0.0321*x**2 + 3.3396*x + 0.0248}

    #不同板子对应不同的空白值
    blank_value = {2:1713.21153846,3:2411.63461538,5:2444.51923077,6:1488.93333333}
    raw_value = {x:0 for x in all_board_address}
    for i in all_board_address:
        if i in data:
            average_raw_value = numpy.average(data[i])
            log10_raw_value = log10(blank_value[i]/average_raw_value)#OD的定义
            raw_value.update({i:log10_raw_value})

    # print('log10_raw_value',raw_value)
    if len(data) == 1:
        real_value = {}
        i = list(data.keys())[0]
        real_value.update({i:fun_data[i](raw_value[i])})
        # print(real_value)
        return real_value
    else:
        real_value = {x:0 for x in all_board_address}
        for i in all_board_address:
            real_value.update({i:fun_data[i](raw_value[i])})
        # print('real_value=',real_value)
        return real_value

def data_handing_after_handing(data={},dt_max=0.013,dt_min=0.006,var_threshold=1000):
    '''
    用于处理粗略计算OD后数据，返回计算后的真实OD
    :param data: 需要处理的数据，只有一个键值
    :param dt_max: 置信区间上限参数
    :param dt_min: 置信区间下限参数
    :param var_threshold: 方差阈值
    :return: 返回真实OD
    '''
    if var_threshold == 1000:
        for i in data:
            var_tem = numpy.var(data[i])
            if var_tem <=1000:#静止状态
                key = list(data.keys())[0]
                key = all_board_address.index(key)
                # print('key=',key)
                # print('ave=',ave)
                max_lim = ave[key] + ave[key] * dt_max  # 求置信区间的上限
                min_lim = ave[key] - ave[key] * dt_min  # 求置信区间的下限
                for i in data:
                    for j in data[i]:
                        if j > max_lim or j< min_lim:
                            data[i].remove(j)
                return  data
            else:#搅动状态
                for i in data:
                    data[i] = [max(data[i])]
                return data
    else:
        for i in data:
            var_tem = numpy.var(data[i])
            if var_tem <=500:#静止状态
                key = list(data.keys())[0]
                key = all_board_address.index(key)
                max_lim = ave[key] + ave[key] * dt_max  # 求置信区间的上限
                min_lim = ave[key] - ave[key] * dt_min  # 求置信区间的下限
                for i in data:
                    for j in data[i]:
                        if j > max_lim or j< min_lim:
                            data[i].remove(j)
                return  data
            else:#搅动状态
                for i in data:
                    data[i] = [max(data[i])]
                return data




def produce_data():

    initialization(2)
    data = read_save_print_output(print_number=10, print_borad=2, save_='no', print_='yes', file_dir='F:\\test\\')
    data2 = data.copy()  # 复制一个,因为后面对data做了改变
    save_OD_raw_value(data=data)
    # 接下来粗略的计算一遍OD及板子的状态
    clc_var_ave(save_='no')
    data_after_handing = data_handing(data=data, save_='no')

    real_value = clc_real_OD(data_after_handing)
    # 上面这一步得到粗略计算后的OD。之前的实验一采用这种方法计算，后
    # 来分析实验结果发现这种方法不够精确,因此再此基础上添加了后续代码）

    # 接下来，查看哪些板子的OD超过了0.7
    tempera_data_collect = {}  # 用于临时收集参数
    for i in real_value:
        if real_value[i] <= 0.7:
            data_one = data_handing_after_handing(data={i: data2[i]}, dt_max=0.005, dt_min=0.006, var_threshold=1000)
            tempera_data_collect.update(data_one)  # 临时收集一下处理后的参数
            real_OD_one = clc_real_OD(data_one)
            real_value.update(real_OD_one)
        else:
            if real_value[i] <= 1.3:
                data_one = data_handing_after_handing(data={i: data2[i]}, dt_max=0.005, dt_min=0.006, var_threshold=500)
                tempera_data_collect.update(data_one)  # 临时收集一下处理后的参数
                real_OD_one = clc_real_OD(data_one)
                real_value.update(real_OD_one)
            else:
                data_one = data_handing_after_handing(data={i: data2[i]}, dt_max=0.013, dt_min=0.006, var_threshold=500)
                tempera_data_collect.update(data_one)  # 临时收集一下处理后的参数
                real_OD_one = clc_real_OD(data_one)
                real_value.update(real_OD_one)

    print('real_value', real_value)
    return real_value




@app.route('/home')
def home():
    return render_template(
        'index.html'
    )
@app.route('/test',methods=['GET','POST'])
def get_result():

    data = produce_data()
    str = os.getcwd()+'\savefile.txt'
    with open(str, 'a', encoding='utf-8-sig', newline='') as f:
        f.write(json.dumps(data))
        f.write('\n')

    t = time.strftime('%y-%m-%d %H:%M',time.localtime())
    res = jsonify({'data':data,'time':t})
    return res













if __name__=="__main__":
    app.run(debug=True)
















