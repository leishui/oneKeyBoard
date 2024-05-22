import copy
import json
import sys

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QComboBox, QLineEdit, QVBoxLayout, QWidget, QCheckBox, \
    QPushButton, QHBoxLayout, QMessageBox, QDialog, QFrame, QRadioButton, QButtonGroup, QFileDialog, QMenu
from serial_tool import refresh_serial_port, save_config
from keys import u_keys, all_keys


class CustomDialog(QDialog):
    def __init__(self, parent=None, selections=None):
        super().__init__(parent)

        if selections is None:
            selections = []

        self.setWindowTitle("组合键")

        self.layout = QVBoxLayout()

        # label = QLabel("按键1", self)
        # self.layout.addWidget(label)

        self.comboBoxes = []
        # combobox = QComboBox(self)
        # combobox.addItems(all_keys)
        # self.comboBoxes.append(combobox)
        # self.layout.addWidget(combobox)
        if len(selections) > 0:
            for selection in selections:
                self.init(selection)
        else:
            self.init()
        bottom_layout = QHBoxLayout()
        button_box = QPushButton("OK", self)
        button_box.clicked.connect(self.accept)
        button_add = QPushButton("add", self)
        button_add.clicked.connect(self.add)
        bottom_layout.addWidget(button_box)
        bottom_layout.addWidget(button_add)
        self.layout.addLayout(bottom_layout)

        self.setLayout(self.layout)

    def init(self, option=None):
        combobox = QComboBox(self)
        combobox.addItems(all_keys)

        if option is not None:
            combobox.setCurrentText(option)

        self.comboBoxes.append(combobox)

        label = QLabel(self)
        label.setText("按键" + str(len(self.comboBoxes)))

        self.layout.addWidget(label)
        self.layout.addWidget(combobox)

    def add(self):
        combobox = QComboBox(self)
        combobox.addItems(all_keys)

        self.comboBoxes.append(combobox)

        label = QLabel(self)
        label.setText("按键" + str(len(self.comboBoxes)))

        self.layout.insertWidget(self.layout.count() - 1, label)
        self.layout.insertWidget(self.layout.count() - 1, combobox)


class MainWindow(QMainWindow):
    def __init__(self, init_data=None):
        super().__init__()

        if init_data is None:
            init_data = {}
        self.init_data = init_data
        print(init_data)
        self.serial_ports = refresh_serial_port()
        self.com_device_select = None
        self.lineEdits = []
        self.comboButtons = []
        self.radioGroups = []
        self.setWindowTitle("配置")
        self.setMinimumWidth(300)
        self.layout = QVBoxLayout()

        if self.init_data != {} and len(self.init_data["single_click_input"]) > 0:
            self.init_widgets()
        else:
            self.create_widgets()

        self.refresh_com_devices()

        # 设置窗口中央的widget
        self.centralWidget = QWidget(self)
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if fileName:
            try:
                with open(fileName, 'r') as file:
                    data = json.load(file)
                QMessageBox.information(self, "File Opened", f"Successfully opened {fileName}")
                # 在这里可以处理JSON数据，比如显示在界面上
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def init_widgets(self):
        # 创建布局
        self.create_head_layout()

        for data in self.init_data["single_click_input"]:
            label = QLabel("组合:" + str(len(self.comboButtons) + 1), self)
            # self.layout.insertWidget(self.layout.count() - 1, label)
            group_layout = QHBoxLayout()
            group_layout.addWidget(label)

            combo_button = QPushButton(self)
            # self.layout.insertWidget(self.layout.count() - 1, combo_button)
            group_layout.addWidget(combo_button, stretch=1)
            combo_button.hide()
            combo_button.setToolTip("点击设置组合键")
            combo_button.clicked.connect(self.open_popup)
            self.comboButtons.append(combo_button)
            line_edit = QLineEdit(self)

            self.lineEdits.append(line_edit)
            # self.layout.insertWidget(self.layout.count() - 1, line_edit)
            group_layout.addWidget(line_edit, stretch=1)
            self.layout.addLayout(group_layout)
            radio_group = QButtonGroup(self)
            radio_text = QRadioButton("文本模式", self)
            radio_combo = QRadioButton("组合键模式", self)

            if data["type"] == "combination":
                text = ""
                for keys in data["values"]:
                    text += (keys + "\n")
                combo_button.setText(text[:-1])
                line_edit.setVisible(False)
                combo_button.setVisible(True)
                radio_combo.setChecked(True)
            else:
                combo_button.setText("设置组合键")
                line_edit.setText(data["values"][0])
                radio_text.setChecked(True)

            chl = QHBoxLayout(self)
            chl.addWidget(radio_text)
            chl.addWidget(radio_combo)
            radio_group.addButton(radio_text)
            radio_group.addButton(radio_combo)
            self.layout.addLayout(chl)
            radio_group.buttonClicked.connect(self.on_radio_changed)
            self.radioGroups.append(radio_group)

        self.add_button_layout = QVBoxLayout()
        self.add_button = QPushButton("添加", self)
        self.add_button.setToolTip("点击添加组合")
        self.add_button.clicked.connect(self.add_widgets)
        self.add_button_layout.addStretch()
        self.add_button_layout.addWidget(self.add_button)
        self.layout.addLayout(self.add_button_layout)

        if len(self.comboButtons) > 4:
            self.add_button.setToolTip("最多添加5个组合")
            self.add_button.setText("最多添加5个组合")
            self.add_button.setDisabled(True)

    def create_widgets(self):
        # 创建布局
        self.create_head_layout()

        label = QLabel("组合1:", self)
        # self.layout.addWidget(label)
        group_layout = QHBoxLayout()
        group_layout.addWidget(label)

        combo_button = QPushButton(self)
        # self.layout.addWidget(combo_button)
        group_layout.addWidget(combo_button, stretch=1)
        combo_button.hide()
        combo_button.setText("设置组合键")
        combo_button.setToolTip("点击设置组合键")
        combo_button.clicked.connect(self.open_popup)
        self.comboButtons.append(combo_button)
        line_edit = QLineEdit(self)

        self.lineEdits.append(line_edit)
        # self.layout.addWidget(line_edit)
        group_layout.addWidget(line_edit, stretch=1)
        self.layout.addLayout(group_layout)
        radio_group = QButtonGroup(self)
        radio_text = QRadioButton("文本模式", self)
        radio_text.setChecked(True)
        radio_combo = QRadioButton("组合键模式", self)
        chl = QHBoxLayout(self)
        chl.addWidget(radio_text)
        chl.addWidget(radio_combo)
        radio_group.addButton(radio_text)
        radio_group.addButton(radio_combo)
        self.layout.addLayout(chl)
        self.radioGroups.append(radio_group)

        radio_group.buttonClicked.connect(self.on_radio_changed)

        self.add_button_layout = QVBoxLayout()
        self.add_button = QPushButton("添加", self)
        self.add_button.setToolTip("点击添加组合")
        self.add_button.clicked.connect(self.add_widgets)
        self.add_button_layout.addStretch()
        self.add_button_layout.addWidget(self.add_button)
        self.layout.addLayout(self.add_button_layout)
        # checkbox_combo.stateChanged.connect(self.on_checkbox_changed)

    def on_save_config(self):
        if self.com_device_select is None or self.com_device_select.currentText() == "":
            return
        configData = {
            "global_config": {
                "key_mode": 2,
                "single_key_delay": 100,
                "group_key_delay": 255
            },
            "single_click_input": [],
            "double_click_input": []
        }
        for i, lineEdit in enumerate(self.lineEdits):
            if lineEdit.isVisible():
                if lineEdit.text() == "":
                    continue
                text = lineEdit.text().replace("\\n", "\n")
                configData["single_click_input"].append({"type": "text", "values": [text]})
            else:
                if self.comboButtons[i].text() == "" or self.comboButtons[i].text() == "设置组合键":
                    continue
                values = []
                parts = self.comboButtons[i].text().split("\n")
                for part in parts:
                    if part == "无":
                        continue
                    if part == "(Space)":
                        part = " "
                    values.append(part)
                configData["single_click_input"].append({"type": "combination", "values": values})

        print(configData)
        with open('config.json', 'w') as file:
            json.dump(configData, file)
        # save_config(configData, self.com_device_select.currentText().split(" - ")[0])

    def create_head_layout(self):
        head_layout = QVBoxLayout()

        h_line = QFrame()
        h_line.setFrameShape(QFrame.Shape.HLine)
        h_line.setFrameShadow(QFrame.Shadow.Sunken)

        button_import = QPushButton("导入配置")
        button_read = QPushButton("读取配置")
        button_save = QPushButton("保存配置")

        # button_import.clicked.conect(import_config)
        # button_read.clicked.conect(read_config)
        button_save.clicked.connect(self.on_save_config)

        inner_h_layout0 = QHBoxLayout()
        inner_h_layout0.addWidget(button_import)
        inner_h_layout0.addWidget(button_read)
        inner_h_layout0.addWidget(button_save)
        head_layout.addLayout(inner_h_layout0)

        head_layout.addWidget(h_line)

        label = QLabel("选择设备:")
        self.com_device_select = QComboBox()
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_com_devices)

        inner_h_layout = QHBoxLayout()
        inner_h_layout.addWidget(label)
        inner_h_layout.addWidget(self.com_device_select, stretch=1)
        inner_h_layout.addWidget(refresh_button)
        head_layout.addLayout(inner_h_layout)

        h_line = QFrame()
        h_line.setFrameShape(QFrame.Shape.HLine)
        h_line.setFrameShadow(QFrame.Shadow.Sunken)
        head_layout.addWidget(h_line)
        self.layout.addLayout(head_layout)

    def refresh_com_devices(self):
        self.com_device_select.clear()
        self.serial_ports = refresh_serial_port()
        for serial_port in self.serial_ports:
            self.com_device_select.addItem(str(serial_port))

    def add_widgets(self):
        # 创建布局

        label = QLabel("组合:" + str(len(self.comboButtons) + 1), self)
        # self.layout.insertWidget(self.layout.count() - 1, label)
        group_layout = QHBoxLayout()
        group_layout.addWidget(label)

        combo_button = QPushButton(self)
        # self.layout.insertWidget(self.layout.count() - 1, combo_button)
        group_layout.addWidget(combo_button, stretch=1)
        combo_button.hide()
        combo_button.setText("设置组合键")
        combo_button.setToolTip("点击设置组合键")
        combo_button.clicked.connect(self.open_popup)
        self.comboButtons.append(combo_button)
        line_edit = QLineEdit(self)
        self.lineEdits.append(line_edit)
        # self.layout.insertWidget(self.layout.count() - 1, line_edit)
        group_layout.addWidget(line_edit, stretch=1)
        self.layout.insertLayout(self.layout.count() - 1, group_layout)
        radio_group = QButtonGroup(self)
        radio_text = QRadioButton("文本模式", self)
        radio_text.setChecked(True)
        radio_combo = QRadioButton("组合键模式", self)
        chl = QHBoxLayout(self)
        chl.addWidget(radio_text)
        chl.addWidget(radio_combo)
        radio_group.addButton(radio_text)
        radio_group.addButton(radio_combo)
        self.layout.insertLayout(self.layout.count() - 1, chl)
        radio_group.buttonClicked.connect(self.on_radio_changed)
        self.radioGroups.append(radio_group)

        if len(self.comboButtons) > 4:
            self.add_button.setToolTip("最多添加5个组合")
            self.add_button.setText("最多添加5个组合")
            self.add_button.setDisabled(True)

    def on_radio_changed(self, button):
        # print(self.sender(), button)
        for i, radioGroup in enumerate(self.radioGroups):
            if radioGroup == self.sender():
                if button.text() == "组合键模式":
                    self.lineEdits[i].hide()
                    self.comboButtons[i].show()
                else:
                    self.comboButtons[i].hide()
                    self.lineEdits[i].show()

    def open_popup(self):
        current_index = self.comboButtons.index(self.sender())
        current_button = self.comboButtons[current_index]
        dialog = CustomDialog(
            selections=[] if current_button.text() == "设置组合键" else current_button.text().split("\n"))
        # current_button.setText("处理中")
        selected_keys = ""
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for comboBox in dialog.comboBoxes:
                if comboBox.currentText() != "无":
                    selected_keys += comboBox.currentText()
                    selected_keys += "\n"
                    # print("Selected option:", comboBox.currentText())
            if selected_keys == "":
                current_button.setText("设置组合键")
            else:
                current_button.setText(selected_keys[:-1])


def main():
    app = QApplication(sys.argv)

    # window = MainWindow()

    try:
        with open("config.json", 'r') as file:
            data = json.load(file)
            # print(data)
            window = MainWindow(init_data=data)
        # 在这里可以处理JSON数据，比如显示在界面上
    except Exception as e:
        print(e)
        window = MainWindow()

    # window = MainWindow()

    # 创建添加按钮
    # add_button = QPushButton("Add Widget", window)
    # add_button.clicked.connect(window.add_widgets)
    #
    # # 添加按钮和伸缩空间，确保按钮位于底部
    # window.layout.addWidget(add_button)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
