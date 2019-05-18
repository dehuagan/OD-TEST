# from socket import *
# import threading
# from numpy import var as np_var
# from numpy import average as np_average
#
#
# collect_addr = []
# LED_ON = {}
# LED_OFF = {}
# def get_OD_rawvalue():
#
#     UDP_sock = socket(AF_INET,SOCK_DGRAM)
#     name = gethostname()
#     address1 = gethostbyname(name)
#     UDP_sock.bind((address1,8080))
#
#     the_number_of_LED_on = 0
#     the_number_of_LED_off = 0
#     while True:
#         OD_raw_value_ascll = UDP_sock.recvfrom(1024)
#         OD_raw_value = OD_raw_value_ascll[0][9:12].decode('utf-8')
#         times = 2
#         sums = []
#         for items in OD_raw_value:
#             if items.isdecimal():
#                 number = ord(items)-48
#                 number = number*16**times
#                 sums.append(number)
#             else:
#                 number = ord(items)-87
#                 number = number*16**times
#                 sums.append(number)
#             times-=1
#         OD_raw_value = sum(sums)
#
#         board_address = int(OD_raw_value_ascll[0][2:4])
#         board_situation = chr(OD_raw_value_ascll[0][5])
#         board_address_situation = '.'.join((str(board_address), str(board_situation)))
#
#         if board_address not in collect_addr:
#             collect_addr.append(board_address)
#             LED_ON[board_address] = []
#             LED_OFF[board_address] = []
#             if board_situation == '0':
#                 LED_OFF[board_address].append(OD_raw_value)
#             else:
#                 LED_ON[board_address].append(OD_raw_value)
#         else:
#             if board_situation == '0':
#                 if len(LED_OFF[board_address]) == 100:
#                     LED_OFF[board_address].pop(0)
#                 LED_OFF[board_address].append(OD_raw_value)
#             else:
#                 if len(LED_ON[board_address]) == 100:
#                     LED_ON[board_address].pop(0)
#                 LED_ON[board_address].append(OD_raw_value)
#
#
#         print('addr',collect_addr)
#         print('on',LED_ON)
#         print('off',LED_OFF)
#         print('situation', board_address_situation)
#         print('============================================')
#
#
# t1 = threading.Thread(target=get_OD_rawvalue)
x = 2
b = 'x+3-2'
print(eval(b))


# class OD_MODULE:
#     def __init__(self, board_address):
#         self.board = board_address
#
#     def get_on_minus_off_value(self):
#         res = []
#         for i in range(len(LED_ON[self.board])):
#             res.append(LED_ON[self.board][i] - LED_OFF[self.board][i])
#         return res
#
#
#     def calculate_var_ave(self,on_minus_off):
#         var = np_var(on_minus_off)
#         ave = np_average(on_minus_off)
#
#
#     def clc_var_ave(file_dir=r'F:\test\----dif.txt', save_='yes'):
#         '''
#         #计算方差、平均值
#         #初步将方差阈值订在450，超过这个数，则认为发酵罐处于搅动状态
#         :param file_dir: 保存数据的文件路径
#         :param save_: 是否需要保存文件
#         '''
#         global var, ave
#         var = []
#         ave = []
#         for i in all_board_address:
#             var.append(numpy.var(OD_raw_value_ON_OFF[i][:min_len]))
#             ave.append(numpy.average(OD_raw_value_ON_OFF[i][:min_len]))
#         if save_ == 'yes':
#             with open(file_dir, 'a') as file:
#                 for i in var:
#                     file.write(str(i) + '\t')
#                 file.write('\n')
#                 for i in ave:
#                     file.write(str(i) + '\t')
#                 file.write('\n')
