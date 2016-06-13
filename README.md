# rpi_drivers

A collection of drivers for various pieces of hardware to use with the Raspberry Pi

## hd44780_i2c

A driver which provides a class for HD44780-compatible LCD displays using a PCF8574-compatible
I2C controller. This module attempts to conform to the LCD 1.0 API used by Arduino libraries.

## shift_register

A driver that provides classes for shift registers.  Currently 74HC595 type chips are supported
for serial in, parallel out operations.

## simpleADC

A module providing the ability to read a value from an analog device like a photo-resistor, or
thermistor.  The basic idea is that a capacitor in the circuit delays the full voltage being
applied to the configured GPIO, and that delay can be used to take a rough measurement of the
value from the connected device.
