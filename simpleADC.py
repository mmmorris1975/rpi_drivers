#!/usr/bin/env python

# Simple circuit diagram:
#
#            GPIO
#              |
# + == device === capacitor == - (ground)
#
# Where 'device' may be some analog device like a thermistor or
# photo-resistor.  The basic premise being that the capacitor will regulate the
# time it takes to tickle the GPIO input high level, depending on how much
# voltage 'device' allows to pass.  This will allow you to provide an uncalibrated,
# approximate measurement from 'device'.  It'll be up to you to convert it to
# a meaningful value based on the the type of device and capacitor in use.

import RPi.GPIO as GPIO
from time import sleep

def read_value(pin):
  reading = 0

  # Not sure why we don't setup as an input right off the bat, I assume the
  # examples on the internet had a good reason for doing this
  GPIO.setup(pin, GPIO.OUT, initial = GPIO.LOW)
  sleep(0.5)
  GPIO.setup(pin, GPIO.IN)

  while (GPIO.input(pin) == GPIO.LOW):
    reading += 1

  return reading
