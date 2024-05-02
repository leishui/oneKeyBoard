#ifndef USER_USB_RAM
#error "This example needs to be compiled with a USER USB setting"
#endif

#include "src/userUsbHidKeyboard/USBCDC.h"
#include "src/userUsbHidKeyboard/USBHIDKeyboard.h"

#define BUTTON_PIN 15  // 按键监听引脚
// 键盘使用模式
enum KeyboardMode {
  ONLY_SINGLE_CLICK,  // 只能单击触发
  CAN_DOUBLE_CLICK    // 可以双击触发
};

enum InputMode {
  TEXT_INPUT_MODE,        // 文字输入模式
  COMBINATION_INPUT_MODE  // 组合键输入模式
};

// 串口接收状态
enum State {
  IDLE,
  WAITING_OPEN_BRACKET,
  READING_KEY,
  WAITING_COLON,
  READING_VALUE,
  WAITING_CLOSE_BRACKET
};

// config 索引
enum {
  CONFIG_INDEX_KEY_MODE,               // 键盘使用模式，对应上面ONLY_SINGLE_CLICK，CAN_DOUBLE_CLICK两种
  CONFIG_INDEX_SINGLE_KEY_DELAY,       // 普通按键间隔
  CONFIG_INDEX_COMBINATION_KEY_DELAY,  // 组合键之后的间隔
  CONFIG_INDEX_KEY1_START = 9,         // KEY1 开始
  CONFIG_INDEX_KEY1_END = 48,          // KEY1 结束
  CONFIG_INDEX_KEY2_START,             // KEY2 开始
  CONFIG_INDEX_KEY2_END = 88,          // KEY2 结束
  CONFIG_INDEX_LAST                    // 结束占位
};

__xdata uint8_t config[CONFIG_INDEX_LAST];

// 函数声明
void handle_single_click();
void handle_double_click();
void handle_key_state(bool key_state, bool is_double_click);
void eeprom_write(uint8_t addr, uint8_t value);
void config2eeprom();
void eeprom2config();
void handle_serial_input();
void handle_serial_input_kv(uint16_t key, uint16_t value);
void do_input(uint8_t type, uint8_t start, uint8_t end);

void setup() {
  USBInit();

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  eeprom2config();

  // 等待按键松开
  while (!digitalRead(BUTTON_PIN))
    ;
}

void loop() {
  // 处理串口输入
  handle_serial_input();

  // 按键处理
  if (config[CONFIG_INDEX_KEY_MODE] == 2) {
    handle_double_click();
  } else {
    handle_single_click();
  }
}

void handle_single_click() {
  static bool buttonPressPrev = false;
  bool buttonPress = !digitalRead(BUTTON_PIN);
  unsigned long currentTime = millis();
  static unsigned long debounceTime = 0;

  if (buttonPress != buttonPressPrev && currentTime - debounceTime > 10) {
    debounceTime = currentTime;
    buttonPressPrev = buttonPress;
    handle_key_state(buttonPress, false);  // 按键处理函数
  }
}

void handle_double_click() {
  // 使用第一次按下与第二次按下的时间差区分单击和双击
  // 第一次按下时，开始 {timeDiff}ms 延迟触发单击按下和释放事件，
  // 如果期间内再次按下则取消计时器，马上触发双击按下事件，然后抬起时触发双击释放事件
  // 优化使用体验, 动态调节 timeDiff 的值, 如果上次为单击则 timeDiffMin，如果上次为双击则 timeDiffMax
  static uint16_t timeDiff = 200;
  const uint16_t timeDiffMin = 200;
  const uint16_t timeDiffMax = 350;

  // 单击按下事件定时
  static unsigned long startTimer1 = 0;
  // 双击释放事件定时
  static unsigned long startTimer2 = 0;

  static bool buttonPressPrev = false;
  bool buttonPress = !digitalRead(BUTTON_PIN);
  unsigned long currentTime = millis();
  static unsigned long debounceTime = 0;

  if (buttonPress != buttonPressPrev && currentTime - debounceTime > 10) {
    buttonPressPrev = buttonPress;
    debounceTime = currentTime;

    if (buttonPress) {
      if (startTimer1 == 0 && startTimer2 == 0) {
        // 这时说明按钮第一次按下
        // 开始延迟触发单击按下和释放事件
        startTimer1 = currentTime + timeDiff;
        startTimer2 = currentTime + timeDiff;
      } else if (startTimer1 != 0 && startTimer2 != 0) {
        // 这时说明按钮第二次按下, 并且单击按下和释放事件都未触发
        // 取消单击定时器，马上触发双击按下事件
        startTimer1 = 0;
        startTimer2 = 0;
        // 在此处理双击按下事件
        handle_key_state(true, true);
      }
    } else {
      if (startTimer2 != 0) {
        // 这时说明单击按下事件已经触发，单击释放事件还没触发
        // 使它能够在下面的定时器判断中立即触发单击释放事件
        startTimer2 = currentTime;
      } else {
        // 在此处理双击释放事件
        handle_key_state(false, true);
        timeDiff = timeDiffMax;
      }
    }
  } else {
    if (buttonPress && startTimer2 != 0) {
      // 这时说明在一直按住的状态，并且还没触发单击释放定时器
      // 把释放事件定时器推迟, 防止本次loop内触发单击释放事件
      startTimer2 = currentTime + 1;
    }
  }

  // 单击按下计时器
  if (startTimer1 != 0 && currentTime >= startTimer1) {
    startTimer1 = 0;
    // 在此处理单击按下事件
    handle_key_state(true, false);
  }
  // 单击释放计时器
  if (startTimer1 == 0 && startTimer2 != 0 && currentTime >= startTimer2) {
    startTimer2 = 0;
    // 在此处理单击释放事件
    handle_key_state(false, false);
    timeDiff = timeDiffMin;
  }
}

void handle_key_state(bool key_state, bool is_double_click) {

  if (key_state) {
    uint8_t start_index = is_double_click ? CONFIG_INDEX_KEY2_START : CONFIG_INDEX_KEY1_START;
    uint8_t combination_config = config[start_index];
    uint8_t combination_count = combination_config >> 5;  // combination_config高3位代表组合个数最多5个
    // USBSerial_print("combination_config:");
    // USBSerial_print(combination_config);
    // USBSerial_print("\n");
    // USBSerial_flush();
    uint8_t combination_type;
    uint8_t combination_length;
    // 接下来的3个字节合并为一个，代表前四个组合的长度，每个组合长度占六位
    uint32_t first = config[++start_index];
    uint32_t second = config[++start_index];
    uint32_t combination_length_config = (first << 16) + (second << 8) + config[++start_index];
    ++start_index;
    // USBSerial_print("first:");
    // USBSerial_print(first);
    // USBSerial_print("second:");
    // USBSerial_print(second);
    // USBSerial_print("combination_length_config:");
    // USBSerial_print(combination_length_config);
    // USBSerial_print("\n");
    // USBSerial_flush();
    for (uint8_t i = 0; i < combination_count; i++) {
      Keyboard_releaseAll();
      // combination_config后5位对应了组合类型
      //0-TEXT_INPUT_MODE 文字输入模式
      //1-COMBINATION_INPUT_MODE 组合键输入模式
      combination_type = (combination_config >> (4 - i)) & 1;
      //combination_length_config从低到高位，每6位代表一个组合长度
      combination_length = (combination_length_config >> (i * 6)) & 0b111111;
      do_input(combination_type, start_index, start_index + combination_length - 1);
      start_index = start_index + combination_length;
    };
  }
}

void do_input(uint8_t type, uint8_t start, uint8_t end) {
  // USBSerial_print("type:");
  // USBSerial_print(type);
  // USBSerial_print(",start:");
  // USBSerial_print(start);
  // USBSerial_print(",end");
  // USBSerial_print(end);
  // USBSerial_print("\n");
  // USBSerial_flush();
  uint8_t single_key_delay = config[CONFIG_INDEX_SINGLE_KEY_DELAY];
  uint8_t combination_key_delay = config[CONFIG_INDEX_COMBINATION_KEY_DELAY];
  switch (type) {
    case COMBINATION_INPUT_MODE:  // 组合键模式 顺序按下接着倒序释放
      for (uint8_t i = start; i <= end; i++) {
        Keyboard_press(config[i]);
        delay(single_key_delay);
      }
      for (uint8_t i = end; i >= start; i--) {
        Keyboard_release(config[i]);
      }
      break;
    case TEXT_INPUT_MODE:  // 输入文本模式
      for (uint8_t i = start; i <= end; i++) {
        Keyboard_write(config[i]);
        delay(single_key_delay);
      }
      break;
  }
  delay(combination_key_delay);
}

void eeprom_write(uint8_t addr, uint8_t value) {
  if (eeprom_read_byte(addr) == value)
    return;
  eeprom_write_byte(addr, value);

  // USBSerial_print_s("EEPROM w");
  // USBSerial_println(addr);
  // USBSerial_flush();
}

void config2eeprom() {
  for (uint8_t i = 0; i < CONFIG_INDEX_LAST; i++) {
    eeprom_write(i, config[i]);
  }
}

void eeprom2config() {
  for (uint8_t i = 0; i < CONFIG_INDEX_LAST; i++) {
    config[i] = eeprom_read_byte(i);
  }
}

bool is_digit(char c) {
  return c >= '0' && c <= '9';
}

void handle_serial_input() {
  static enum State currentState = IDLE;
  static uint16_t key = 0;
  static uint16_t value = 0;

  while (USBSerial_available()) {
    char serialChar = USBSerial_read();

    switch (currentState) {
      case IDLE:
        if (serialChar == '{') {
          currentState = WAITING_OPEN_BRACKET;
        }
        break;

      case WAITING_OPEN_BRACKET:
        if (is_digit(serialChar)) {
          key = serialChar - '0';
          currentState = READING_KEY;
        }
        break;

      case READING_KEY:
        if (is_digit(serialChar)) {
          key = key * 10 + (serialChar - '0');
        } else if (serialChar == ':') {
          currentState = WAITING_COLON;
        }
        break;

      case WAITING_COLON:
        if (is_digit(serialChar)) {
          value = serialChar - '0';
          currentState = READING_VALUE;
        }
        break;

      case READING_VALUE:
        if (is_digit(serialChar)) {
          value = value * 10 + (serialChar - '0');
        } else if (serialChar == '}') {
          currentState = IDLE;
          // 处理接收完整的消息
          handle_serial_input_kv(key, value);
        }
        break;
    }
  }
}

void handle_serial_input_kv(uint16_t key, uint16_t value) {
  // 写入配置
  if (key < CONFIG_INDEX_LAST && value <= 255) {
    config[key] = value;
    return;
  }
  // 命令
  if (key == 999) {
    switch (value) {
      case 0:  // 保存 config 到 eeprom
        config2eeprom();
        break;
      case 1:  // 打印 config 数组
        for (uint8_t i = 0; i < CONFIG_INDEX_LAST; i++) {
          USBSerial_print_c(i == 0 ? '[' : ',');
          USBSerial_print(config[i]);
        }
        USBSerial_print_c(']');
        USBSerial_flush();
        break;
    }
  }
}
