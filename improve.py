#!/usr/bin/env python
# -*- coding: utf-8 -*-
from socket import socket,gethostname,AF_INET,SOCK_DGRAM,gethostbyname
from numpy import var as np_var
from numpy import average as np_average
from math import log10

class OD_module:
    # all_board_address = 0
    # UDP_sock = 0
    # OD_collect
    # OD_sit
    # OD_raw_value_ON_OFF
    value_ON_and_OFF = {}
    def __init__(self,board_addr):

        self.board_address = board_addr
        name = gethostname()
        self.UDP_sock = socket(AF_INET, SOCK_DGRAM)
        address1 = gethostbyname(name)
        self.UDP_sock.bind((address1, 8080))

        self.OD_collect = {}  #to collect address and OD, the format is {address.LED status: [OD value]} eg:｛2.1:2251｝
        self.OD_sit = {}  # to record the change of status, the format is {board_address: LED status} eg:｛2:1｝

        self.OD_raw_value_ON_OFF = {x: [] for x in self.all_board_address}  # to record the value of light_on minus light_off
        # self.value_ON_and_OFF = {}
        self.value_ON_and_OFF.update({str(float(x)): [] for x in self.all_board_address})
        self.value_ON_and_OFF.update({str((x + 0.1)): [] for x in self.all_board_address})

    def read_save_print_output(self, print_number, print_borad, save_, print_, file_dir):
        '''
        read, save and print data
        :param print_number: number of printouts
        :param print_borad: board needed to print
        :save_:save or not
        :print_:print or not
        :file_dir:file directory
        :return: return the data of light_on minus the data of light_off corresponding to each board (dictionary)
        '''
        the_number_of_LED_on = 0
        the_number_of_LED_off = 0
        while True:
            OD_raw_value_ascll = self.UDP_sock.recvfrom(1024)
            OD_raw_value = OD_raw_value_ascll[0][9:12].decode('utf-8')
            times = 2
            sums = []
            for items in OD_raw_value:
                if items.isdecimal():
                    number = ord(items) - 48
                    number = number * 16 ** times
                    sums.append(number)
                else:
                    number = ord(items) - 87
                    number = number * 16 ** times
                    sums.append(number)
                times -= 1
            OD_raw_value = sum(sums)

            board_address = int(OD_raw_value_ascll[0][2:4])
            board_situation = chr(OD_raw_value_ascll[0][5])
            board_address_situation = '.'.join((str(board_address), str(board_situation)))
            if save_ == 'yes':
                if board_address not in self.OD_sit:
                    file_path_name = file_dir + 'BOARD%s_OFF.txt' % board_address
                    with open(file_path_name, 'w') as LED_OFF_FILE:
                        pass
                    file_path_name = file_dir + 'BOARD%s_ON.txt' % board_address
                    with open(file_path_name, 'w') as LED_ON_FILE:
                        pass
            # store the OD value corresponding to board address and status
            if board_address_situation not in self.OD_collect:
                self.OD_collect.update({board_address_situation: [OD_raw_value]})
            else:
                self.OD_collect[board_address_situation].append(OD_raw_value)

            # judge the change of switch on and off status, if change then output
            if board_address not in self.OD_sit:
                self.OD_sit.update({board_address: int(board_situation)})

            else:
                if int(board_situation) - self.OD_sit[board_address] == 1:  # from light on to off
                    self.OD_sit[board_address] = int(board_situation)  # store latest status
                    OD_output = round(sum(self.OD_collect[str(board_address) + '.0']) / \
                                      len(self.OD_collect[str(board_address) + '.0']), 3)
                    self.OD_collect[str(board_address) + '.0'] = []  # clear the data of light off

                    # 接下来计算开灯状态减去关灯状态的值
                    self.value_ON_and_OFF[str(board_address) + '.0'] = OD_output  # record the status of light off
                    if self.value_ON_and_OFF[str(board_address) + '.1'] == [] or self.value_ON_and_OFF[
                                str(board_address) + '.0'] == []:
                        pass
                    else:
                        self.OD_raw_value_ON_OFF[board_address].append(self.value_ON_and_OFF[str(board_address) + '.1'] \
                                                                  - self.value_ON_and_OFF[str(board_address) + '.0'])
                        self.value_ON_and_OFF[str(board_address) + '.0'] = []
                        self.value_ON_and_OFF[str(board_address) + '.1'] = []

                    # store data
                    if save_ == 'yes':
                        file_path_name = file_dir + 'BOARD{num}_OFF.txt'.format(num=board_address)
                        with open(file_path_name, 'a') as LED_OFF_FILE:  # store data in a file correspongding to board
                            LED_OFF_FILE.write(str(OD_output) + '\n')
                    if board_address == print_borad and print_ == 'yes':
                        print('device{a} off  ODrawvalue={b}'.format(a=print_borad, b=OD_output))
                        if the_number_of_LED_on <= print_number:
                            the_number_of_LED_on += 1
                        else:
                            break

                elif int(board_situation) - self.OD_sit[board_address] == -1:  # from light on to off

                    self.OD_sit[board_address] = int(board_situation)  # store the latest status of lights
                    OD_output = round(sum(self.OD_collect[str(board_address) + '.1']) / \
                                      len(self.OD_collect[str(board_address) + '.1']), 3)
                    self.OD_collect[str(board_address) + '.1'] = []  # clear the data of light on
                    # calculate the value of light_on minus light_off
                    self.value_ON_and_OFF[str(board_address) + '.1'] = OD_output  # record the status of light_on
                    if self.value_ON_and_OFF[str(board_address) + '.0'] == [] or self.value_ON_and_OFF[
                                str(board_address) + '.1'] == []:
                        pass
                    else:
                        self.OD_raw_value_ON_OFF[board_address].append(self.value_ON_and_OFF[str(board_address) + '.1'] - \
                                                                       self.value_ON_and_OFF[str(board_address) + '.0'])

                        self.value_ON_and_OFF[str(board_address) + '.0'] = []
                        self.value_ON_and_OFF[str(board_address) + '.1'] = []

                    # store data
                    if save_ == 'yes':
                        file_path_name = file_dir + 'BOARD{num}_ON.txt'.format(num=board_address)
                        with open(file_path_name, 'a') as LED_OFF_FILE:  # store data in a file correspongding to board
                            LED_OFF_FILE.write(str(OD_output) + '\n')
                    if board_address == print_borad and print_ == 'yes':
                        print('device{a} on  ODrawvalue={b}'.format(a=print_borad, b=OD_output))
                        if the_number_of_LED_off <= print_number:
                            the_number_of_LED_off += 1
                            print('number……', the_number_of_LED_off)
                        else:
                            break
                else:  # status doesn't change
                    pass
        self.UDP_sock.close()
        return self.OD_raw_value_ON_OFF

    def save_OD_raw_value(self, data=[], file_dir=r'F:\test\----dif.txt'):
        '''
        store OD raw value(LED_ON-LED_OFF)
        :param data: OD raw value of all boards
        :param file: file for saving data
        '''
        global min_len
        min_len = []
        for board in self.all_board_address:
            min_len.append(len(data[board]))
        min_len = min(min_len)
        min_len = min_len if min_len <= 108 else 108
        print('长度……=', min_len)

        with open(file_dir, 'w')as file:
            for j in range(min_len):
                for i in self.all_board_address:
                    file.write(str(data[i][j]) + '\t')
                file.write('\n')
            for i in range(3):  # enter
                file.write('\n')

    def clc_var_ave(self,file_dir=r'F:\test\----dif.txt', save_='yes'):
        '''
        #calculate the variance and mean
        #If the variance threshold is set at 450, the fermenter is considered to be in the state of agitation
        :param file_dir: directory of file that saves data
        :param save_: save file or not
        '''
        global var, ave
        var = []
        ave = []
        for i in self.all_board_address:
            var.append(np_var(self.OD_raw_value_ON_OFF[i][:min_len]))
            ave.append(np_average(self.OD_raw_value_ON_OFF[i][:min_len]))
        if save_ == 'yes':
            with open(file_dir, 'a') as file:
                for i in var:
                    file.write(str(i) + '\t')
                file.write('\n')
                for i in ave:
                    file.write(str(i) + '\t')
                file.write('\n')
                # print('var',var)
                # print('ave',ave)

    def data_handing(self, data=[], dt_max=0.013, dt_min=0.013, var_threshold=1000, file_dir_=r'F:\test\----dif.txt',
                     save_='no'):
        '''
        处理数据
        :param dt_max: upper limit error
        :param dt_min: lower limit error
        :param data: OD raw value(LED_ON-LED_OFF)
        :file_dir_: directory of file that saves data
        :return: data after processing
        '''
        # determine the minimum length of these lists
        min_len = []
        for board in self.all_board_address:
            min_len.append(len(data[board]))
        min_len = min(min_len)

        # remove the extra points and keep the list the same length
        for i in self.all_board_address:
            data[i] = data[i][:min_len]

        # set the confidence interval and delete some points with large deviation
        for j in self.all_board_address:
            inde = self.all_board_address.index(j)
            if var[inde] <= var_threshold:  # At this point, it is considered to be in a static state, and the point with a larger deviation can be deleted
                print('static state')
                max_lim = ave[inde] + ave[inde] * dt_max  # calculate the upper limit of the confidence interval
                min_lim = ave[inde] - ave[inde] * dt_min  # calculate the lower limit of the confidence interval
                del_data = []  # data that needs to be deleted
                for k in range(min_len):
                    # print('j=',j,'k=',k)
                    if data[j][k] > max_lim or data[j][k] < min_lim:
                        del_data.append(data[j][k])
                if del_data != 0:
                    for i in del_data:
                        data[j].remove(i)
            else:  # At this point in the state of intense agitation, take the maximum
                print('violent agitation')
                data[j] = [max(data[j])]

        # save OD raw value after processing
        if file_dir_ != '' and save_ == 'yes':
            max_len = []
            for board in self.all_board_address:
                max_len.append(len(data[board]))
            max_len = max(max_len)
            with open(file_dir_, 'a')as file:
                for i in range(3):  # enter
                    file.write('\n')
                for j in range(max_len):
                    for i in self.all_board_address:
                        if j < len(data[i]):
                            file.write(str(data[i][j]) + '\t')
                        else:
                            file.write('' + '\t')
                    file.write('\n')
                for i in range(3):  # enter
                    file.write('\n')
        return data

    def clc_real_OD(self, data):
        # calculate the real OD value
        # different boards correspond to different equations
        # fun_data = {2:lambda x:1.7168*x**2+3.0301*x+0.004,
        #             3:lambda x:1.7244*x**2+3.0466*x+0.109,
        #             5:lambda x:2.1218*x**2+2.3649*x+0.0464,
        #             6:lambda x:2.3652*x**2+2.6944*x}

        fun_data = {2: lambda x: 2.379 * x ** 3 - 1.0704 * x ** 2 + 3.743 * x - 0.0045,
                    3: lambda x: 4.258 * x ** 3 - 3.9034 * x ** 2 + 4.9852 * x + 0.0959,  #
                    5: lambda x: 2.5255 * x ** 3 - 1.3582 * x ** 2 + 3.3456 * x - 0.0027,
                    6: lambda x: 1.5857 * x ** 3 + 0.0321 * x ** 2 + 3.3396 * x + 0.0248}

        # different boards correspond to different blank values
        blank_value = {2: 1713.21153846, 3: 2411.63461538, 5: 2444.51923077, 6: 1488.93333333}
        raw_value = {x: 0 for x in self.all_board_address}
        for i in self.all_board_address:
            if i in data:
                average_raw_value = np_average(data[i])
                log10_raw_value = log10(blank_value[i] / average_raw_value)  # definition of OD
                raw_value.update({i: log10_raw_value})

        # print('log10_raw_value',raw_value)
        if len(data) == 1:
            real_value = {}
            i = list(data.keys())[0]
            real_value.update({i: fun_data[i](raw_value[i])})
            # print(real_value)
            return real_value
        else:
            real_value = {x: 0 for x in self.all_board_address}
            for i in self.all_board_address:
                real_value.update({i: fun_data[i](raw_value[i])})
            # print('real_value=',real_value)
            return real_value

    def data_handing_after_handing(self, data={}, dt_max=0.013, dt_min=0.006, var_threshold=1000):
        '''
        process the data after rough OD calculation and return the real OD after calculation
        :param data: the data that needs to be processed has only one key value
        :param dt_max:  confidence interval upper limit parameter
        :param dt_min: confidence interval lower limit parameter
        :param var_threshold: variance threshold
        :return: 返回真实OD
        '''
        if var_threshold == 1000:
            for i in data:
                var_tem = np_var(data[i])
                if var_tem <= 1000:  # static state
                    key = list(data.keys())[0]
                    key = self.all_board_address.index(key)
                    # print('key=',key)
                    # print('ave=',ave)
                    max_lim = ave[key] + ave[key] * dt_max  # calculate the upper limit of confidence interval
                    min_lim = ave[key] - ave[key] * dt_min  # calculate the lower limit of confidence interval
                    for i in data:
                        for j in data[i]:
                            if j > max_lim or j < min_lim:
                                data[i].remove(j)
                    return data
                else:  # status of agitation
                    for i in data:
                        data[i] = [max(data[i])]
                    return data
        else:
            for i in data:
                var_tem = np_var(data[i])
                if var_tem <= 500:  # static status
                    key = list(data.keys())[0]
                    key = self.all_board_address.index(key)
                    max_lim = ave[key] + ave[key] * dt_max  # calculate the upper limit of confidence interval
                    min_lim = ave[key] - ave[key] * dt_min  # calculate the lower limit of confidence interval
                    for i in data:
                        for j in data[i]:
                            if j > max_lim or j < min_lim:
                                data[i].remove(j)
                    return data
                else:  # status of agitation
                    for i in data:
                        data[i] = [max(data[i])]
                    return data

    def produce_data(self, real_value, data2):
        tempera_data_collect = {}  # collect parameters temporarily
        for i in real_value:
            if real_value[i] <= 0.7:
                data_one = self.data_handing_after_handing(data={i: data2[i]}, dt_max=0.005, dt_min=0.006,
                                                      var_threshold=1000)
                tempera_data_collect.update(data_one)  # collect processed parameters temporarily
                real_OD_one = self.clc_real_OD(data_one)
                real_value.update(real_OD_one)
            else:
                if real_value[i] <= 1.3:
                    data_one = self.data_handing_after_handing(data={i: data2[i]}, dt_max=0.005, dt_min=0.006,
                                                          var_threshold=500)
                    tempera_data_collect.update(data_one)  # collect processed parameters temporarily
                    real_OD_one = self.clc_real_OD(data_one)
                    real_value.update(real_OD_one)
                else:
                    data_one = self.data_handing_after_handing(data={i: data2[i]}, dt_max=0.013, dt_min=0.006,
                                                          var_threshold=500)
                    tempera_data_collect.update(data_one)  # collect processed parameters temporarily
                    real_OD_one = self.clc_real_OD(data_one)
                    real_value.update(real_OD_one)

        print('real_value', real_value)
        return real_value