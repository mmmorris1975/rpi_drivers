#!/usr/bin/env python

# An attempt to make a LCD API 1.0 compatible (Arduino) library for python/Raspberry Pi for displays
# based on a HD44780 compatible display using a PCF8574 compatible I2C controller. Arduino users use
# the LiquidCrystal_I2C library to support this, and well use that as a reference.
#
# http://playground.arduino.cc/Code/LCDAPI
# https://hmario.home.xs4all.nl/arduino/LiquidCrystal_I2C/

import RPi.GPIO as GPIO
# TODO: which python I2C library to use?
# pyI2C - http://pyi2c.sourceforge.net/
# smbus - python-smbus package
# quick2wire.i2c - http://quick2wire.com/i2c-python/

DEFAULT_CMD_DELAY  = -1
DEFAULT_CHAR_DELAY = -1

class hd44780_i2c():
  # Mandatory functions
  def __init__(i2c_addr, rows, cols, **kwargs):
    # Initialize the display, set cursor to pos 0,0 + other setup stuff
    # RPi I2C pins are always on GPIO pins 2 (SDA) & 3 (SCL) using BCM mode,
    # so we'll initialize those ourself
    pass

  def set_delay(self, **kwargs):
    # Override the default library delays. kwargs can be one of 'cmd', or 'char'
    # to specify setting the delay for LCD commands, or sending characters.
    pass

  def print(self, val):
    # print the provided value on the display
    pass

  def println(self, val):
    # Call print(), with trailing new line
    self.print(str(val) + "\n")

  def write(self, val):
    # raw write value to the display
    pass

  def command(self, val):
    # Send command to display, for display-specific commands not covered in the API
    pass

  def clear(self):
    # clear display and return cursor to 0,0
    pass

  def home(self):
    # set cursor position to 0,0 leaving display untouched
    pass

  def set_cursor(self, row, col):
    # move cursor to indicated position, row and col values should be validated
    # so they fall within 0 - self.(row|col)
    pass

  def cursor_on(self):
    # set block cursor on
    pass

  def cursor_off(self):
    # set block cursor off
    pass

  def blink_on(self):
    # set blinking underline cursor on
    pass

  def blink_off(self):
    # set blinking underline cursor off
    pass

  # Optional functions
  def set_backlight(self, val):
    # set backlight brightnetss (0-255), where 0 = off
    pass

  def set_contrast(self, val):
    # set display contrast (0-255)
    pass

  def on(self):
    # turn display on by setting backlight to ~ 75%
    self.set_backlight(192)

  def off(self):
    # turn display off by setting backlight to 0
    self.set_backlight(0)

  def status(self):
    # return status of the display. API docs say:
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
