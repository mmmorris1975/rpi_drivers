#!/usr/bin/env python

# An attempt to make a LCD API 1.0 compatible (Arduino) library for python/Raspberry Pi for displays
# based on a HD44780 compatible display using a PCF8574 compatible I2C controller. Arduino users use
# the LiquidCrystal_I2C library to support this, and well use that as a reference.
#
# http://playground.arduino.cc/Code/LCDAPI
# https://hmario.home.xs4all.nl/arduino/LiquidCrystal_I2C/

# 0x08 - backlight on
# 0x04 - E line high
# 0x02 - R/W line high
# 0x01 - RS line high

from time import sleep
import smbus

# Time is in microseconds
# Wikipedia says max command execution time is 1.52ms
DEFAULT_CMD_DELAY  = 1550
DEFAULT_CHAR_DELAY = 50

# Control status of the Register Select (RS) line
LCD_REG_CMD  = 0x00
LCD_REG_DATA = 0x01

# OR these values with LCD_CMD_SETDDRAMADDR to send the Set DDRAM Address command
LCD_LINE1_ADDR = 0x00
LCD_LINE2_ADDR = 0x40
LCD_LINE3_ADDR = 0x14 # 20 chars into line 1
LCD_LINE4_ADDR = 0x54 # 20 chars into line 2

# Taken from LiquidCrystal_I2C library and Wikipedia page:
# https://en.wikipedia.org/wiki/Hitachi_HD44780_LCD_controller
#
# Commands
LCD_CMD_CLEARDISPLAY = 0x01
LCD_CMD_CURSORHOME   = 0x02
LCD_CMD_ENTRYMODESET = 0x04
LCD_CMD_DISPLAYCONTROL = 0x08
LCD_CMD_CURSORSHIFT  = 0x10
LCD_CMD_FUNCTIONSET  = 0x20
LCD_CMD_SETCGRAMADDR = 0x40
LCD_CMD_SETDDRAMADDR = 0x80

# Entry Mode Flags
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT  = 0x02
LCD_ENTRYSHIFTINCR = 0x01
LCD_ENTRYSHIFTDECR = 0x00

# Display Control Flags
LCD_DISPLAYON  = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON   = 0x02
LCD_CURSOROFF  = 0x00
LCD_BLINKON    = 0x01
LCD_BLINKOFF   = 0x00

# Cursor Shift Flags
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE  = 0x00
LCD_SHIFTRIGHT  = 0x01
LCD_SHIFTLEFT   = 0x00

# Function Set Flags
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS  = 0x00

# flags for backlight control
# Sending 0x08 turns backlight on, any other value where the
# fourth bit is turned off will turn off the backlight
LCD_BACKLIGHT   = 0x08
LCD_NOBACKLIGHT = 0x00

class hd44780_i2c():
  def _init_display(self):
    # Per http://web.stanford.edu/class/ee281/handouts/lcd_tutorial.pdf
    # Initialize the display to a known default state. Must send at least a function set command,
    # and optionally send entry mode, display control and clear display commands. Since 3 of the 8
    # I2C outputs are used for control (RS, R/W and E lines), we need to use 4-bit mode for sending
    # data so we can also specify the necessary control signals on the upper 4 bits of the byte.
    #
    # This code will:
    #   FUNCTION SET: 4-bit mode, 2 lines with 5x8 characters
    #   ENTRY MODE: L -> R with no display shift
    #   DISPLAY MODE: Turn display and cursor on, no cursor blink
    #
    # Execute the 'Initialize by Instruction' routine specified in the datasheet, since we won't assume
    # the system is supplying the necessary Vcc to trigger the power-on reset logic.  It'll also ensure
    # we're starting from a totally clean slate when we instantiate new instances of this class

    func_set = LCD_CMD_FUNCTIONSET | LCD_4BITMODE | LCD_2LINE | LCD_5x8DOTS
    entry_mode_set = LCD_CMD_ENTRYMODESET | LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECR
    display_control_set = LCD_CMD_DISPLAYCONTROL | LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF

    # Wait at least 40ms after Vcc hits 2.7V
    sleep(0.1)
    self.command(0x30)
    sleep(0.01) # Default command delay too short
    self.command(0x30) # Per datasheet, default delay should be adequate here
    self.command(0x30)
    sleep(0.1) # for good measure

    # Reset instructions complete, now initialize
    self.command(func_set)
    self.command(entry_mode_set)
    self.command(display_control_set)
    self.set_backlight(LCD_BACKLIGHT)
    self.clear()

  # Mandatory functions
  def __init__(self, i2c_bus, i2c_addr, rows, cols, **kwargs):
    assert(i2c_bus >= 0)
    assert(i2c_addr > 0)
    assert(rows > 0)
    assert(cols > 0)

    # Note to self: a 20x4 display may be a 40x2 display
    self.i2c_addr = i2c_addr
    self.rows = rows
    self.cols = cols
    self.test = kwargs.get('test', False)
    self.set_delay()
    self.backlight = LCD_NOBACKLIGHT

    if not self.test:
      # initialize I2C library and display, there is no special
      # RPi setup needed other than enabling I2C in the kernel
      self.bus = smbus.SMBus(i2c_bus)
      self._init_display()

  def set_delay(self, **kwargs):
    # Override the default library delays. kwargs can be one of 'cmd', or 'char'
    # to specify setting the delay for LCD commands, or sending characters.
    self.cmd_delay  = kwargs.get('cmd', DEFAULT_CMD_DELAY)
    self.char_delay = kwargs.get('char', DEFAULT_CHAR_DELAY)

  def _write_byte(self, val, mode):
    print("SENDING: " + bin(val)[2:].zfill(8) + ", MODE: " + str(mode))
    high_nib = (val >> 4) << 4
    low_nib  = (val & 0x0F) << 4
    print("  HIGH NIB: " + bin(high_nib | mode)[2:].zfill(8))
    self._i2c_write(high_nib | mode)
    print("  LOW NIB:  " + bin(low_nib | mode)[2:].zfill(8))
    self._i2c_write(low_nib | mode)
    self._pulse(self.backlight)

  def _i2c_write(self, val):
    data = val | self.backlight
    print("    SENDING BYTE: " + bin(data)[2:].zfill(8))
    self.bus.write_byte(self.i2c_addr, data)
    self._pulse(data)

  def _pulse(self, val):
    self.bus.write_byte(self.i2c_addr, val | 0x04)
    sleep(1/1000000)
    self.bus.write_byte(self.i2c_addr, val & 0xFB)
    sleep(50/1000000)

  # To avoid clashing with Python's print(), we'll break API compliance
  def printstr(self, val):
    # print the provided value on the display
    for c in val[:]:
      print("WRITTING: " + c)
      self.write(ord(c))
      sleep(5)

  def println(self, val):
    # Call print(), with trailing new line
    self.printstr(str(val) + "\n")

  def write(self, val):
    # raw write value to the display, callers are reponsible for implementing any delay after calling this method
    if not self.test:
      self._write_byte(val, LCD_REG_DATA)
      sleep(self.char_delay / 1000000)

  def command(self, val):
    # Send command to display, for display-specific commands not covered in the API
    self._write_byte(val, LCD_REG_CMD)
    sleep(self.cmd_delay / 1000000) # Pause to ensure command is executed
    return bin(val)[2:].zfill(8)

  def clear(self):
    # clear display and return cursor to 0,0
    return self.command(LCD_CMD_CLEARDISPLAY)

  def home(self):
    # set cursor position to 0,0 leaving display untouched
    return self.command(LCD_CMD_CURSORHOME)

  def set_cursor(self, row, col):
    # move cursor to indicated position, row and col values falling outside the configured
    # display size will be set to 0 or the rows/colums value provided in the constructor
    if row < 0:
      row = 0

    if col < 0:
      col = 0

    if row > self.rows:
      row = self.rows

    if col > self.cols:
      col = self.cols

    if row == 0 and col == 0:
      self.home()
    else:
      # TODO: move cursor to the indicated position.  Should we send cursor home command and then
      # move, or determine current cursor position and move relative to that?
      pass

  def cursor_on(self):
    # set block cursor on
    return self.command(LCD_CMD_DISPLAYCONTROL | LCD_CURSORON)

  def cursor_off(self):
    # set block cursor off
    return self.command(LCD_CMD_DISPLAYCONTROL | LCD_CURSOROFF)

  def blink_on(self):
    # set blinking underline cursor on
    return self.command(LCD_CMD_DISPLAYCONTROL | LCD_BLINKON)

  def blink_off(self):
    # set blinking underline cursor off
    return self.command(LCD_CMD_DISPLAYCONTROL | LCD_BLINKOFF)

  # Optional functions
  def set_backlight(self, val):
    # TODO: set backlight brightness (0-255), where 0 = off
    # Best I can tell, backlight control is either on or off
    if val > 0:
      self.backlight = LCD_BACKLIGHT
    else:
      self.backlight = LCD_NOBACKLIGHT

    self.bus.write_byte(self.i2c_addr, self.backlight)
    self.backlight

  def set_contrast(self, val):
    # TODO: set display contrast (0-255)
    pass

  def on(self):
    # turn display on and set backlight to ~ 75%
    self.command(LCD_CMD_DISPLAYCONTROL | LCD_DISPLAYON)
    return self.set_backlight(192)

  def off(self):
    # set backlight to 0 and turn display off
    self.set_backlight(0)
    return self.command(LCD_CMD_DISPLAYCONTROL | LCD_DISPLAYOFF)

  def status(self):
    # TODO: return status of the display. API docs say:
    #   Returns the FIFO buffer on the robot-electronics display
    #   Can be used to get r/w status of hardwired displays 
    pass

  # Extended functions left unimplemented:
  #  load_custom_characters(self, char_num, rows)
  #  keypad(self)
  #  printstr(self)
  # These seem like a cool idea, and may implment in the future:
  #  init_bargraph(self, type)
  #  draw_horizontal_graph(row, col, len, end)
  #  draw_vertical_graph(row, col, len, end)

if __name__ == "__main__":
  # cls = hd44780_i2c(1, 0x3f, 20, 4, test = True)
  cls = hd44780_i2c(1, 0x3f, 20, 4)
  print("SLEEPING")
  sleep(3)
  cls.printstr('wad951')
#  print(cls.off())
#  print(cls.clear())
#  print(cls.blink_on())