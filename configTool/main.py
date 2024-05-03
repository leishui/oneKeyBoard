import serial
import serial.tools.list_ports

from json_config import get_data_send
from colorama import init, Fore, Back, Style

# 初始化 colorama
init(autoreset=True)


def select_serial_port():
    # 获取所有可用的串口
    available_ports = serial.tools.list_ports.comports()

    if len(available_ports) == 0:
        raise Exception("无可用串口")

    print("可用串口列表：")
    for i, port in enumerate(available_ports):
        print(f"{Fore.GREEN}[{i + 1}]: {port}")

    # 让用户选择串口
    selection = input("请选择要连接的串口（输入序号）[1]:")
    if not selection:
        selection = 1
    try:
        selection_index = int(selection) - 1
        if selection_index < 0 or selection_index >= len(available_ports):
            raise ValueError
        selected_port = available_ports[selection_index].device
        return selected_port
    except ValueError:
        print(Fore.RED + "无效的选择，请输入正确的序号。")
        return None


def main():
    selected_port = select_serial_port()
    if selected_port:
        try:
            # 打开选择的串口
            ser = serial.Serial(selected_port, baudrate=9600, timeout=1)
            print(f"{Fore.GREEN}成功连接到串口 {selected_port}")

            # 向串口写入临时配置，未保存则仅本次连接生效
            # 拔出设备后失效
            ser.write(get_data_send())
            # 保存配置，永久生效
            ser.write(b'{999:0}')
            print(Fore.GREEN + "写入配置成功！")

            # 关闭串口
            ser.close()
        except serial.SerialException:
            print(f"{Fore.RED}无法打开串口 {selected_port}")


if __name__ == "__main__":
    main()
