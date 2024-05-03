import json
import os.path

# 判断配置文件是否存在
# if not os.path.exists('config.json'):
#     with open('config.json', 'w') as init_config:
#         init_config.write('')
# 从文件中读取 JSON 数据
with open('config.json', 'r') as file:
    data = json.load(file)


# 非字母
u_keys = {
    "KEY_LEFT_CTRL": 0x80,
    "KEY_LEFT_SHIFT": 0x81,
    "KEY_LEFT_ALT": 0x82,
    "KEY_LEFT_GUI": 0x83,
    "KEY_RIGHT_CTRL": 0x84,
    "KEY_RIGHT_SHIFT": 0x85,
    "KEY_RIGHT_ALT": 0x86,
    "KEY_RIGHT_GUI": 0x87,

    "KEY_UP_ARROW": 0xDA,
    "KEY_DOWN_ARROW": 0xD9,
    "KEY_LEFT_ARROW": 0xD8,
    "KEY_RIGHT_ARROW": 0xD7,
    "KEY_BACKSPACE": 0xB2,
    "KEY_TAB": 0xB3,
    "KEY_RETURN": 0xB0,
    "KEY_ESC": 0xB1,
    "KEY_INSERT": 0xD1,
    "KEY_DELETE": 0xD4,
    "KEY_PAGE_UP": 0xD3,
    "KEY_PAGE_DOWN": 0xD6,
    "KEY_HOME": 0xD2,
    "KEY_END": 0xD5,
    "KEY_CAPS_LOCK": 0xC1,
    "KEY_F1": 0xC2,
    "KEY_F2": 0xC3,
    "KEY_F3": 0xC4,
    "KEY_F4": 0xC5,
    "KEY_F5": 0xC6,
    "KEY_F6": 0xC7,
    "KEY_F7": 0xC8,
    "KEY_F8": 0xC9,
    "KEY_F9": 0xCA,
    "KEY_F10": 0xCB,
    "KEY_F11": 0xCC,
    "KEY_F12": 0xCD,
    "KEY_F13": 0xF0,
    "KEY_F14": 0xF1,
    "KEY_F15": 0xF2,
    "KEY_F16": 0xF3,
    "KEY_F17": 0xF4,
    "KEY_F18": 0xF5,
    "KEY_F19": 0xF6,
    "KEY_F20": 0xF7,
    "KEY_F21": 0xF8,
    "KEY_F22": 0xF9,
    "KEY_F23": 0xFA,
    "KEY_F24": 0xFB,
}

config_index = {
    'key_mode': 0,
    'single_key_delay': 1,
    'group_key_delay': 2,
    'key1_start': 9,
    'key1_end': 48,
    'key2_start': 49,
    'key2_end': 88

}
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


def read_config(values, start, end):
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


data_send += read_config(config['single_click_input'],
                         config_index['key1_start'],
                         config_index['key1_end'])
data_send += read_config(config['double_click_input'],
                         config_index['key2_start'],
                         config_index['key2_end'])


# print(data_send)


def get_data_send():
    str_send = ''
    for i in range(0, len(data_send)):
        str_send += data_send[i]
    print(str_send)
    return str_send.encode('utf-8')
