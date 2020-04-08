#!/usr/bin/env python
from __future__ import print_function
import argparse
import binascii
import logging
import hashlib
import struct
import ndef
import hmac
import cli
import sys
import os
import time
import board
import neopixel
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

# The number of NeoPixels
ring_pixels = 50 
mickey_pixels = 40 
pixel_pin = board.D18

if sys.version_info.major < 3:
    sys.exit("This script requires Python 3")

log = logging.getLogger('main')

log.setLevel(logging.CRITICAL)

pygame.init()
pygame.mixer.init()
class MagicBand(cli.CommandLineInterface):
    def __init__(self):
        self.ringsound=pygame.mixer.Sound(file="ring_sound.wav") 
        self.whsound=pygame.mixer.Sound(file="justhome.wav")
        self.RING_LIGHT_SIZE=5
        self.total_pixels = ring_pixels+mickey_pixels
        self.ring_pixels = ring_pixels
        self.pixels = neopixel.NeoPixel(pixel_pin, self.total_pixels, brightness=0.5, auto_write=False, pixel_order=neopixel.RGB)
        self.rdwr_commands = { }
        self.do_lights_on((255,255,255))
        time.sleep(.5)
        self.do_lights_off()
        time.sleep(.5)
        self.do_lights_on((255,255,255))
        time.sleep(.5)
        self.do_lights_off()
        time.sleep(.5)
        self.do_lights_on((255,255,255))
        time.sleep(.5)
        self.do_lights_off()
        parser = ArgumentParser(
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description="")
        super(MagicBand, self).__init__(parser, groups="rdwr dbg card clf")

    def on_rdwr_startup(self, targets):
        return targets

    def on_rdwr_connect(self, tag):
        log.info("MagicBandID = {0}".format(binascii.hexlify(tag.identifier)))
        self.ringsound.play() 
        self.do_lights_circle((255,255,255))
        self.whsound.play()
        self.do_lights_on((0,153,153))
        time.sleep(3)
        self.do_lights_off() 
        return  True

    def on_card_startup(self, target):
        # Nothing needed
        log.info("Listening for magicbands")

    def color_chase(self, color, wait):
        size = self.RING_LIGHT_SIZE
        for i in range(self.ring_pixels+size+1):
            for x in range(1, size):
                if (x+i) < self.ring_pixels:
                    self.pixels[x+i] = color
            if (i > size) :
                off = (i-size)-1
                self.pixels[off] = 0
            time.sleep(wait)
            self.pixels.show()
        time.sleep(0.01)

    def do_lights_circle(self,color):
        for i in range(3):
            self.color_chase(color,.01)

    def do_lights_on(self, color):
        for i in range(self.total_pixels):
            self.pixels[i] = color
        self.pixels.show()

    def do_lights_off(self):
        for i in range(self.total_pixels):
            self.pixels[i] = 0
        self.pixels.show()

    def run(self):
        while self.run_once():
            log.info('.')

class ArgparseError(SystemExit):
    def __init__(self, prog, message):
        super(ArgparseError, self).__init__(2, prog, message)

    def __str__(self):
        return '{0}: {1}'.format(self.args[1], self.args[2])

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgparseError(self.prog, message)


if __name__ == '__main__':
    try:
        MagicBand().run()
    except ArgparseError as e:
        print("exception")
        print(e)
        _prog = e.args[1].split()
    else:
        sys.exit(0)

