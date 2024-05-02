import serial

from json_config import get_data_send

# 打开串口
ser = serial.Serial('COM15', 9600, timeout=1)

if ser.is_open:
    print("串口已打开")

    ser.write(get_data_send())
    # 向串口写入数据
    ser.write(b'{999:0}')

    # 从串口读取数据
    data = ser.readline().decode('utf-8').strip()
    print("Received data:", data)

    # 关闭串口
    ser.close()
    print("串口已关闭")
else:
    print("无法打开串口")
