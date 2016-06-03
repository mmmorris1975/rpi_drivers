#!/usr/bin/env python

from time import sleep
import RPi.GPIO as GPIO
import logging

# As read from Left -> Right
BIT_ORDER_LSB_FIRST = 0x00
BIT_ORDER_MSB_FIRST = 0x01

DEFAULT_HOLD_USECS = 1000

class py74hc595:
  # Datasheet: http://pdf.datasheetcatalog.com/datasheet/NXP_Semiconductors/74HC_HCT595.pdf

  def __init__(self, **kwargs):
    """
    Initialize an instance of this object.  We're going to assume that you've already initialized the RPi.GPIO module with the appropriate
    mode and other settings for your use case.  You can specify the following kwargs in order to setup for your particular configuration:
      data_pin: The GPIO pin the DS line is connected to.
      shift_clk_pin: The GPIO pin the clock/SHCP (shift register clock) input is connected to.
                     With MR line high, low to high (pulse) transition of this pin will shift value on DS line to register.
      store_clk_pin: The GPIO pin the latch/STCP (store register clock) input is connected to.
                     With MR line high, low to high (pulse) transition of this pin will send contents of shift register to output pins.
    """
    self.test = False

    if 'test' in kwargs and kwargs['test']:
      print("UNDER TEST")
      self.test = True
      self.shift_clk_pin = -1
      self.store_clk_pin = -1
    else:
      self.data_pin = kwargs['data_pin']
      self.shift_clk_pin = kwargs['shift_clk_pin']
      self.store_clk_pin = kwargs['store_clk_pin']

      # Ensure data, shift and store clock pins are setup for output and low logic level
      GPIO.setup([self.data_pin, self.shift_clk_pin, self.store_clk_pin], GPIO.OUT, initial = GPIO.LOW)

  def send_nibble(self, data, hi_lo, **kwargs):
    """
    Send a 4 bit nibble to the chip, you must specify if this is the high, or low, 4 bits of the data to send.
    If this is the high 4 bits, then the provided value will be left-shifted 4 bits and zero-padded to a total
    length of 8 bits.  A low nibble is zero-padded to the full 8 bits.  Optional kwargs can be provided to control
    output hold time and bit ordering.

    >>> c.send_nibble(0x05, True)
    '01010000'
    >>> c.send_nibble(0x05, True, order = BIT_ORDER_LSB_FIRST)
    '00001010'
    >>> c.send_nibble(0x05, False)
    '00000101'
    >>> c.send_nibble(0x05, False, order = BIT_ORDER_LSB_FIRST)
    '10100000'
    """
    bits  = data
    hold  = kwargs.get('hold', DEFAULT_HOLD_USECS)
    order = kwargs.get('order', BIT_ORDER_MSB_FIRST)

    if hi_lo:
      bits = bits << 4

    return self._send_data(bits, order, hold)

  def send_byte(self, data, **kwargs):
    """
    Send a 8 bit byte to the chip.  Provided values will be zero-padded to the full 8 bit width.
    Optional kwargs can be provided to control output hold time and bit ordering.

    >>> c.send_byte(0x07)
    '00000111'
    >>> c.send_byte(0x07, order = BIT_ORDER_LSB_FIRST)
    '11100000'
    >>> c.send_byte(0xFF)
    '11111111'
    >>> c.send_byte(0xFF, order = BIT_ORDER_LSB_FIRST)
    '11111111'
    >>> c.send_byte(0x07 << 4 ^ 0x05)
    '01110101'
    >>> c.send_byte(0x07 << 4 ^ 0x05, order = BIT_ORDER_LSB_FIRST)
    '10101110'
    """
    hold  = kwargs.get('hold', DEFAULT_HOLD_USECS)
    order = kwargs.get('order', BIT_ORDER_MSB_FIRST)

    return self._send_data(data, order, hold)

  def _send_data(self, data, order = BIT_ORDER_MSB_FIRST, hold = DEFAULT_HOLD_USECS):
    """
    (API Private) Send the byte to the chip, per the specified bit order (default is MSB first).
    Returns the binary string of data sent.

    >>> c._send_data(73)
    '01001001'
    >>> c._send_data(73, order = BIT_ORDER_LSB_FIRST)
    '10010010'
    """
    bitstr = ""

    if order == BIT_ORDER_MSB_FIRST:
      # Don't need to do some fancy bit-reversing logic, just reverse the range
      # we're applying for the state determination logic for
      rng = range(7,-1,-1)
    else:
      rng = range(0,8)

    for b in rng:
      state = data & (1 << b) > 0
      bitstr += str(int(state))

      if not self.test:
        GPIO.output(self.data_pin, state)

      self._pulse(self.shift_clk_pin)

    self._pulse(self.store_clk_pin, hold)

    return bitstr

  def _pulse(self, pin, usecs = 1000):
    """
    (API Private) Pulse the provided pin.  Set pin HIGH, sleep for a few microsecs, then set pin LOW. 
    Can optionally provide a sleep argument specifying the number of microseconds to wait between state transitions.
    Sleep time default value is a pretty safe (but possibly slow), 1 millisecond
    """
    if self.test:
      sleep(usecs / 1000000.0)
    else:
      GPIO.output(pin, GPIO.HIGH)
      sleep(usecs / 1000000.0)
      GPIO.output(pin, GPIO.LOW)

if __name__ == "__main__":
  import doctest
  doctest.testmod(extraglobs={'c': py74hc595(test = 1)})
