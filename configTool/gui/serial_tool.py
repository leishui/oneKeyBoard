import serial
import serial.tools.list_ports

from keys import u_keys

config_index = {
    'key_mode': 0,
    'single_key_delay': 1,
    'group_key_delay': 2,
    'key1_start': 9,
    'key1_end': 48,
    'key2_start': 49,
    'key2_end': 88

}


def refresh_serial_port():
    # 获取可用的串口设备列表
    ports = serial.tools.list_ports.comports()

    res = []
    # 打印每个串口设备的信息
    for port in ports:
        res.append(port.device + " - " + port.description)

    return res


def read_config():
    return None


def save_config(config, selected_com):
    try:
        # 打开选择的串口
        ser = serial.Serial(selected_com, baudrate=9600, timeout=1)
        print(f"成功连接到串口 {selected_com}")

        # 向串口写入临时配置，未保存则仅本次连接生效
        # 拔出设备后失效
        # build_config(config)
        ser.write(build_config(config))
        # 保存配置，永久生效
        ser.write(b'{999:0}')
    except serial.SerialException:
        print("保存配置失败：串口传输失败")


def build_config(data):
    config = {
        'key_mode': data['global_config']['key_mode'],
        'single_key_delay': data['global_config']['single_key_delay'],
        'group_key_delay': data['global_config']['group_key_delay'],
        'single_click_input': data['single_click_input'],
        'double_click_input': data['double_click_input']
    }
    data_send = [
        f'{{{config_index["key_mode"]}:{config["key_mode"]}}}',
        f'{{{config_index["single_key_delay"]}:{config["single_key_delay"]}}}',
        f'{{{config_index["group_key_delay"]}:{config["group_key_delay"]}}}'
    ]
    data_send += build_click_config(config['single_click_input'],
                                    config_index['key1_start'],
                                    config_index['key1_end'])
    data_send += build_click_config(config['double_click_input'],
                                    config_index['key2_start'],
                                    config_index['key2_end'])
    str_send = ''
    for i in range(0, len(data_send)):
        str_send += data_send[i]
    print(str_send)
    return str_send.encode('utf-8')


def build_click_config(values, start, end):
    combination = 0
    combination_length = 0
    result = []

    for k1 in range(0, len(values)):
        combination += 1 << 5
        value = values[k1]
        if value['type'] == 'combination':
            combination |= (1 << (4 - k1))
            combination_length += len(value['values']) << (6 * k1)
        else:
            k_len = 0
            for key in value['values']:
                k_len += len(key)
            combination_length += k_len << (6 * k1)

    result.append(f'{{{start}:{combination}}}')
    # print(bin(combination_length))
    start += 1
    for i in range(0, 3):
        result.append(f'{{{start}:{(combination_length >> (8 * (2 - i))) & 255}}}')
        start += 1

    for k1 in range(0, len(values)):
        value = values[k1]
        if value['type'] == 'combination':
            for key in value['values']:
                if len(key) > 1:  # 超过一个字符则视作特殊键
                    result.append(f'{{{start}:{u_keys[key]}}}')
                else:
                    result.append(f'{{{start}:{ord(key)}}}')
                start += 1
        else:
            for key in value['values']:
                for char in key:
                    result.append(f'{{{start}:{ord(char)}}}')
                    start += 1
    for i in range(start, end + 1):
        result.append(f'{{{start}:{0}}}')
        start += 1
    if len(result) > 40:
        raise Exception('超长')
    return result
