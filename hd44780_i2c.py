#!/usr/bin/env python

# An attempt to make a LCD API 1.0 compatible (Arduino) library for python/Raspberry Pi for displays
# based on a HD44780 compatible display using a PCF8574 compatible I2C controller. Arduino users use
# the LiquidCrystal_I2C library to support this, and well use that as a reference.
#
# http://playground.arduino.cc/Code/LCDAPI
# https://hmario.home.xs4all.nl/arduino/LiquidCrystal_I2C/

from time import sleep
import RPi.GPIO as GPIO
# TODO: which python I2C library to use?
# pyI2C - http://pyi2c.sourceforge.net/
# smbus - python-smbus package
# quick2wire.i2c - http://quick2wire.com/i2c-python/

# Time is in microseconds
# Wikipedia says max command execution time is 1.52ms
DEFAULT_CMD_DELAY  = 1550
DEFAULT_CHAR_DELAY = 50

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

class hd44780_i2c():
  def _init_pi():
    # This make a big assumtion that GPIO.setmode() hasn't already been called, and
    # that someone really had their heart set on using mode GPIO.BOARD
    # RPi I2C pins are always on GPIO pins 2 (SDA) & 3 (SCL) using BCM mode
    GPIO.setmode(GPIO.BCM)
    GPIO.setup([2,3], GPIO.OUT, initial = GPIO.LOW)

  def _init_display():
    # Per http://web.stanford.edu/class/ee281/handouts/lcd_tutorial.pdf
    # Initialize the display to a known default state. Must send at least a function set
    # command, and optionally send entry mode, display control and clear display commands.
    # This code will:
    #   FUNCTION SET: 8-bit mode, 2 lines with 5x8 characters
    #   ENTRY MODE: L -> R with no display shift
    #   DISPLAY MODE: Turn display and cursor on, no cursor blink
    #
    # Execute the 'Initialize by Instruction' routine specified in the datasheet, since we won't assume
    # the system is supplying the necessary Vcc to trigger the power-on reset logic.  It'll also ensure
    # we're starting from a totally clean slate when we instantiate new instances of this class

    func_set = LCD_CMD_FUNCTIONSET | LCD_8BITMODE | LCD_2LINE | LCD_5x8DOTS
    entry_mode_set = LCD_CMD_ENTRYMODSET | LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECR
    display_control_set = LCD_CMD_DISPLAYCONTROL | LCD_DISPLAYON | LCD_CURSORON | LCD_BLINKOFF

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
    self.clear()

  # Mandatory functions
  def __init__(self, i2c_addr, rows, cols, **kwargs):
    assert(i2c_addr > 0)
    assert(rows > 0)
    assert(cols > 0)

    # Note to self: a 20x4 display may be a 40x2 display
    self.i2c_addr = i2c_addr
    self.rows = rows
    self.cols = cols
    self.test = kwargs.get('test', False)

    if not self.test:
      # TODO: initialize GPIO pins, I2C library and display
      _init_pi()
      _init_display()

    self.set_delay()

  def set_delay(self, **kwargs):
    # Override the default library delays. kwargs can be one of 'cmd', or 'char'
    # to specify setting the delay for LCD commands, or sending characters.
    self.cmd_delay  = kwargs.get('cmd', DEFAULT_CMD_DELAY)
    self.char_delay = kwargs.get('char', DEFAULT_CHAR_DELAY)

# Clash with Python's print()?
#  def print(self, val):
#    # TODO: print the provided value on the display
#    pass

#  def println(self, val):
#    # Call print(), with trailing new line
#    self.print(str(val) + "\n")

  def write(self, val):
    # TODO: raw write value to the display
    pass

  def command(self, val):
    # TODO: Send command to display, for display-specific commands not covered in the API
    sleep(self.cmd_delay / 1000000) # Pause to ensure command is executed
    return bin(val)[2:].zfill(8)

  def clear(self):
    # clear display and return cursor to 0,0
    self.command(LCD_CMD_CLEARDISPLAY)

  def home(self):
    # set cursor position to 0,0 leaving display untouched
    self.command(LCD_CMD_CURSORHOME)

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
    self.command(LCD_CMD_DISPLAYCONTROL | LCD_CURSORON)

  def cursor_off(self):
    # set block cursor off
    self.command(LCD_CMD_DISPLAYCONTROL | LCD_CURSOROFF)

  def blink_on(self):
    # set blinking underline cursor on
    self.command(LCD_CMD_DISPLAYCONTROL | LCD_BLINKON)

  def blink_off(self):
    # set blinking underline cursor off
    self.command(LCD_CMD_DISPLAYCONTROL | LCD_BLINKOFF)

  # Optional functions
  def set_backlight(self, val):
    # TODO: set backlight brightnetss (0-255), where 0 = off
    pass

  def set_contrast(self, val):
    # TODO: set display contrast (0-255)
    pass

  def on(self):
    # turn display on and set backlight to ~ 75%
    self.command(LCD_CMD_DISPLAYCONTROL | LCD_DISPLAYON)
    self.set_backlight(192)

  def off(self):
    # set backlight to 0 and turn display off
    self.set_backlight(0)
    self.command(LCD_CMD_DISPLAYCONTROL | LCD_DISPLAYOFF)

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
  cls = hd44780_i2c(0x37, 20, 4, test = True)
  print(cls.off())
  print(cls.blink_on())
