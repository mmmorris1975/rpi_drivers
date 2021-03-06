#!/usr/bin/env python

# An attempt to make a LCD API 1.0 compatible (Arduino) library for python/Raspberry Pi for displays
# based on a HD44780 compatible display using a PCF8574 compatible I2C controller. Arduino users use
# the LiquidCrystal_I2C library to support this, and well use that as a reference.
#
# http://playground.arduino.cc/Code/LCDAPI
# https://hmario.home.xs4all.nl/arduino/LiquidCrystal_I2C/

# control lines
# 0x08 - backlight on
# 0x04 - E line high
# 0x02 - R/W line high
# 0x01 - RS line high
# upper 4 bits of the byte are for char/cmd data

from time import sleep
import smbus

# Time is in microseconds (per docs, max command exec time is 1.52ms)
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
LCD_LINE_ADDR_LIST = [ LCD_LINE1_ADDR, LCD_LINE2_ADDR, LCD_LINE3_ADDR, LCD_LINE4_ADDR ]

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
    # data so we can also specify the necessary control signals on the other 4 bits of the byte.
    #
    # This code will:
    #   FUNCTION SET: 4-bit mode, with 5x8 characters, num display lines auto-detected
    #   ENTRY MODE: L -> R with no display shift
    #   DISPLAY MODE: Turn display and cursor on, no cursor blink
    #
    # Execute the 'Initialize by Instruction' routine specified in the datasheet, since we won't assume
    # the system is supplying the necessary Vcc to trigger the power-on reset logic.  It'll also ensure
    # we're starting from a totally clean slate when we instantiate new instances of this class.  With
    # the display I use, connected to a 3.3V Vcc, I am unable to get the contrast (set via a trim pot)
    # necessary to make the text readable (it's visible, but very dim).

    # This can't be changed after initialization
    lines = LCD_1LINE
    if self.rows > 1:
      lines = LCD_2LINE

    func_set = LCD_CMD_FUNCTIONSET | LCD_4BITMODE | lines | LCD_5x8DOTS

    # These can
    self.entry_mode_set = LCD_CMD_ENTRYMODESET | LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECR
    self.display_control_set = LCD_CMD_DISPLAYCONTROL | LCD_DISPLAYON | LCD_CURSORON | LCD_BLINKOFF

    # Wait at least 40ms after Vcc hits 2.7V
    sleep(0.1)

    if not self.test:
      # Need to raw _i2c_write(val) to set 4-bit mode before sending commands
      self._i2c_write(0x0)
      sleep(0.01)
      self._i2c_write(0x30)
      sleep(0.01)
      self._i2c_write(0x30)
      sleep(0.01)
      self._i2c_write(0x30)
      sleep(0.01)
      self._i2c_write(0x20)
      sleep(0.1) # for good measure

      # Reset instructions complete, now initialize
      self.command(func_set)
      self.command(self.entry_mode_set)
      self.command(self.display_control_set)
      self.set_backlight(LCD_BACKLIGHT)
      self.clear()

  # Mandatory functions
  def __init__(self, i2c_bus, i2c_addr, rows, cols, **kwargs):
    """
    Initialize an instance of this class. The i2c_bus, i2c_addr, rows, and cols prameters are required and are
    hopefully self-explanatory. No special RPi setup is required other then ensuring I2C is enabled in the kernel
    (no GPIOs need to be configured).  An optional boolean kwarg named 'test' can be provided to enable test mode
    of this class, basically no I2C operations are performed.
    """
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
      # RPi setup needed, other than enabling I2C in the kernel.
      self.bus = smbus.SMBus(i2c_bus)
    else:
      print("UNDER TEST")

    self._init_display()

  def set_delay(self, **kwargs):
    """
    Override the default driver delays for command or data operations to the display.  Supply kwargs
    of 'cmd' or 'char' to override the default delay values for command and data operations, respectivly.
    Values provided are converted to microseconds.

    >>> c.set_delay(cmd=1)
    >>> c.cmd_delay
    1e-06
    >>> c.set_delay(char=5)
    >>> c.char_delay
    5e-06
    >>> c.set_delay(char=6, cmd=7)
    >>> c.cmd_delay
    7e-06
    >>> c.char_delay
    6e-06
    """
    self.cmd_delay  = kwargs.get('cmd', DEFAULT_CMD_DELAY) / 1000000.0
    self.char_delay = kwargs.get('char', DEFAULT_CHAR_DELAY) / 1000000.0

  def _write_byte(self, val, mode):
    """
    (API PRIVATE) Write the value of the byte to the display via the I2C bus as 2 4-bit nibbles
    """
    #print("SENDING: " + bin(val)[2:].zfill(8) + ", MODE: " + str(mode))
    high_nib = val >> 4
    low_nib  = val & 0x0F

    #print("  HIGH NIB: " + bin(high_nib)[2:].zfill(4))
    #print("  LOW NIB:  " + bin(low_nib)[2:].zfill(4))

    self._i2c_write((high_nib << 4) | mode)
    self._i2c_write((low_nib << 4) | mode)

  def _i2c_write(self, val):
    """
    (API PRIVATE) Perform the necessary signalling to send the data via I2C
    """
    data = val | self.backlight
    #print("    SENDING BYTE: " + bin(data)[2:].zfill(8) + " (" + hex(data) + ")")
    self.bus.write_byte(self.i2c_addr, data)
    self._pulse()

  def _pulse(self):
    """
    (API PRIVATE) Pulse the E (enable) line on the display so it will accept the data we've sent it
    """    
    # We are curiously losing the backlight bit when doing the read back
    enable_on  = self.bus.read_byte(self.i2c_addr) | 0x04 | self.backlight
    enable_off = self.bus.read_byte(self.i2c_addr) & ~0x04 | self.backlight

    #print("      STROBING: " + bin(enable_on)[2:].zfill(8) + " (" + hex(enable_on) + ")")
    #print("      STROBING: " + bin(enable_off)[2:].zfill(8) + " (" + hex(enable_off) + ")")

    self.bus.write_byte(self.i2c_addr, enable_on)
    sleep(1/1000000)
    self.bus.write_byte(self.i2c_addr, enable_off)

  # To avoid clashing with Python's print(), we'll need to break API compliance
  def printstr(self, val):
    """
    Write the given string to the display.  Each character (c) in the string will be sent to the
    display as 'ord(c)', so it will not correctly handle raw bytes, use write() for that.
    """
    for c in val[:]:
      #print("WRITTING: " + c)
      self.write(ord(c))

  def println(self, val):
    """
    Call print() and then shift the cursor to the next line, first column.
    If cursor is on the last line, it will be shifted back to line 1, first column.
    """
    self.printstr(val)

    if not self.test:
      cur_line = self.get_cursor_line()
      if cur_line >= self.rows - 1:
        self.set_cursor(0, 0)
      else:
        self.set_cursor(cur_line + 1, 0)

  def write(self, val):
    """
    Write a raw byte to the display.  This is what print() delegates to, and would be useful
    for printing non-printing characters or other glyphs.
    """
    if not self.test:
      self._write_byte(val, LCD_REG_DATA)

    sleep(self.char_delay)

  def command(self, val):
    """
    Send a command byte to the display, for display-specific commands that don't
    have methods available in this library.  Returns the bit-string of the command
    sent in order to make the operation testable.

    >>> c.command(0xD5)
    '11010101'
    """
    if not self.test:
      self._write_byte(val, LCD_REG_CMD)

    sleep(self.cmd_delay) # Pause to ensure command is executed
    return bin(val)[2:].zfill(8)

  def clear(self):
    """
    Clear the display and return cursor to position 0,0

    >>> c.clear()
    '00000001'
    """
    return self.command(LCD_CMD_CLEARDISPLAY)

  def home(self):
    """
    Return cursor to 0,0 position, but leave displayed data untouched

    >>> c.home()
    '00000010'
    """
    # set cursor position to 0,0 leaving display untouched
    return self.command(LCD_CMD_CURSORHOME)

  def set_cursor(self, row, col):
    """
    Move cursor to indicated, absolute position (zero based), row and col values falling outside the
    configured display size will be set to 0 or the max rows/cols configured via the constructor.
    Returns the address of the cursor position.

    >>> c.set_cursor(0,5)
    5
    >>> c.set_cursor(1,12)
    76
    >>> c.set_cursor(2,0)
    20
    >>> c.set_cursor(3,20)
    103
    >>> c.set_cursor(-1,5)
    5
    >>> c.set_cursor(0,1000)
    19
    """
    # move cursor to indicated position (absolute, zero based), row and col values falling outside the
    # configured display size will be set to 0 or max rows/colums value provided in the constructor
    addr = LCD_LINE_ADDR_LIST[0] # 0,0

    if row < 0:
      row = 0

    if col < 0:
      col = 0

    if row >= self.rows:
      row = self.rows - 1

    if col >= self.cols:
      col = self.cols - 1

    if row == 0 and col == 0:
      self.home()
    else:
      addr = col + LCD_LINE_ADDR_LIST[row]
      self.command(LCD_CMD_SETDDRAMADDR | addr)

    return addr

  def is_busy(self):
    """
    Read the busy flag which is returnd as the 8th bit on the data returned from get_cursor_addr().
    Returns non-zero value if true.

    >>> c.get_cursor_addr()
    214
    """
    # The ddram/cursor location read also returns the busy state on the 8th bit
    return (self.get_cursor_addr() & 0x80)

  def get_cursor_addr(self):
    """
    Get the address of the cursor position.

    >>> c.get_cursor_addr()
    214
    """
    # Docs indicate that we need to do the read when RS is low, and R/W and E are high
    # this means it won't work via command() or any of the methods it calls.
    nibs = []

    if not self.test:
      # Set data pins for input, and set RS low, and R/W high
      self.bus.write_byte(self.i2c_addr, 0xF0)
      self.bus.write_byte(self.i2c_addr, 0xF0 | 0x02)
      sleep(0.001)

      for i in range(0,2):
        self.bus.write_byte(self.i2c_addr, 0xF0 | 0x02 | 0x04)
        nibs.append(self.bus.read_byte(self.i2c_addr))
        self.bus.write_byte(self.i2c_addr, 0xF0 | 0x02 & ~0x04)

      self.bus.write_byte(self.i2c_addr, 0x00)
    else:
      # Mock value = 0xD6 (busy flag on + address = 0x56 [row 3, col 2])
      nibs.append(0xDF)
      nibs.append(0x6F)

    high_nib = (nibs[0] >>4) <<4
    low_nib  = nibs[1] >>4
    return high_nib | low_nib

  def get_cursor_line(self):
    """
    Get the line number for the current cursor position by translating the cursor address returned from get_cursor_addr()
    to a line number.  Value returned will be a zero-based value.

    >>> c.get_cursor_line()
    3
    """
    line = 0
    sorted_list = sorted(LCD_LINE_ADDR_LIST, reverse = True)
    addr = self.get_cursor_addr()

    for l in sorted_list:
      if addr >= l:
        line = LCD_LINE_ADDR_LIST.index(l)
        break

    return line

  def cursor_on(self):
    """
    Turns the underline cursor on.

    >>> c.cursor_on()
    '00001111'
    """
    self.display_control_set |= LCD_CURSORON
    return self.command(self.display_control_set)

  def cursor_off(self):
    """
    Turn the underline cursor off

    >>> c.cursor_off()
    '00001101'
    """
    self.display_control_set &= ~LCD_CURSORON
    return self.command(self.display_control_set)

  def blink_on(self):
    """
    Turn on the blinking block cursor.

    >>> c.blink_on()
    '00001111'
    """
    self.display_control_set |= LCD_BLINKON
    return self.command(self.display_control_set)

  def blink_off(self):
    """
    Turn off the blinking block cursor.

    >>> c.blink_off()
    '00001110'
    """
    self.display_control_set &= ~LCD_BLINKON
    return self.command(self.display_control_set)

  # Optional functions
  def set_backlight(self, val):
    """
    Set backlight intensity. Currently only supports either full on or full off intensity.
    Values supplied to this method larger than 1 will be interpreted as backlight on, and
    a values less than 1 will be interpreted as backlight off. Value returned is the value
    of the backlight attribute for the instance of the object.

    >>> c.set_backlight(1)
    8
    >>> c.set_backlight(0)
    0
    >>> c.set_backlight(255)
    8
    >>> c.set_backlight(-4)
    0
    """
    # TODO: set backlight brightness (0-255), where 0 = off
    # Best I can tell, backlight control is either on or off
    if val > 0:
      self.backlight = LCD_BACKLIGHT
    else:
      self.backlight = LCD_NOBACKLIGHT

    if not self.test:
      self.bus.write_byte(self.i2c_addr, self.backlight)

    return self.backlight

  def set_contrast(self, val):
    """
    Set display contrast. Currently a no-op as the display I have doesn't support this
    """
    # TODO: set display contrast (0-255)
    pass

  def on(self):
    """
    Turn the display on.  This implementation will send the 'display on' command to the
    device, as well as turning on the backlight.

    >>> c.on()
    '00001111'
    """
    # turn display on and set backlight to ~ 75%
    self.set_backlight(192)
    self.display_control_set |= LCD_DISPLAYON
    return self.command(self.display_control_set)

  def off(self):
    """
    Turn the display off. This implementation will send the 'display off' command to the
    display, and turn off the backlight.

    >>> c.off()
    '00001011'
    """
    self.set_backlight(0)
    self.display_control_set &= ~LCD_DISPLAYON
    return self.command(self.display_control_set)

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
  # For personal reference, my display is running ROM code A00
  import doctest
  doctest.testmod(extraglobs={'c': hd44780_i2c(1, 1, 4, 20, test = 1)})
