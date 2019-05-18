import improve

from flask_cors import CORS
from flask import Flask,render_template,request
from flask import jsonify
import threading
import os
import time
import json
app = Flask(__name__)
CORS(app, supports_credentials=True)


@app.route('/index',methods=['GET','POST'])
def data_to_ui():
    if request.method == 'POST':
        para = json.loads(request.get_data())
        addr = para["addr"]
        print_num = para["print_num"]
        print_borad = para["print_borad"]
        save_1 = para["save_1"]
        print_ = para["print_"]
        file_dir = para["file_dir"]
        save_2 = para["save_2"]
        save_3 = para["save_3"]


        ui_module = improve.OD_module(addr)
        data = ui_module.read_save_print_output(print_number=print_num, print_borad=print_borad, save_=save_1, print_=print_, file_dir=file_dir)
        data2 = data.copy()
        ui_module.save_OD_raw_value(data=data)
        ui_module.clc_var_ave(save_=save_2)
        data_after_handing = ui_module.data_handing(data=data, save_=save_3)
        real_value = ui_module.clc_real_OD(data_after_handing)
        res_data = ui_module.produce_data(real_value = real_value, data2 = data2)
        print(res_data)

        str = os.getcwd() + '\savefile.txt'
        with open(str, 'a', encoding='utf-8-sig', newline='') as f:
            f.write(json.dumps(data))
            f.write('\n')

        t = time.strftime('%y-%m-%d %H:%M', time.localtime())
        res = jsonify({'data': res_data, 'time': t})
        return res

if __name__=="__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
