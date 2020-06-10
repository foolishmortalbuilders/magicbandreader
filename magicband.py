#!/usr/bin/env python
from __future__ import print_function
import argparse
import binascii
import logging
import hashlib
import struct
#import ndef
import hmac
import cli
import sys
import os
import time
import board
import neopixel
import time
import os.path
from os import path
import random 
import configparser

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

# print band ids when read  set to True to see band ids on command line
#print_band_id = False

# Reverse the circle lights direction
#reverse_circle = True

# The number of NeoPixels
#ring_pixels = 50 
#mickey_pixels = 40 

config = configparser.ConfigParser()
config.read('settings.conf')
print_band_id = config.get('Settings', 'print_band_id')
reverse_circle = config.get('Settings', 'reverse_circle')
ring_pixels = config.get('Settings', 'ring_pixels')
mickey_pixels = config.get('Settings', 'mickey_pixels')

#COLOR_GREEN = (255,0,0) 
#COLOR_RED   = (0,255,0)
#COLOR_BLUE  = (0,0,255)
#COLOR_WHITE = (255,255,255)
#COLOR_PURPLE = (0,153,153)
COLOR_GREEN = config.get('Settings', 'COLOR_GREEN')
COLOR_RED = config.get('Settings', 'COLOR_RED')
COLOR_BLUE = config.get('Settings', 'COLOR_BLUE')
COLOR_WHITE = config.get('Settings', 'COLOR_WHITE')
COLOR_PURPLE = config.get('Settings', 'COLOR_PURPLE')

# Sequence Definitions
#
sequences = { 
          'any1' : { 'color_ring' : COLOR_GREEN,
                    'color_mouse': COLOR_GREEN,
                    'spin_sound' : '',
                    'hold_seconds': 1.5,
                    'sound' : 'magicband_fastpass.mp3'},

          'any2' : { 'color_ring' : COLOR_BLUE,
                    'color_mouse': COLOR_BLUE,
                    'spin_sound' : 'ring_sound.wav',
                    'hold_seconds': 1.5,
                    'sound' : 'magicband_fastpass.mp3'},

           # fastpass sound
           '044d63b27c5c80': { 'color_ring' : COLOR_GREEN,
                               'color_mouse': COLOR_GREEN,
                               'spin_sound' :'',
                               'hold_seconds': 1.5,
                               'sound' : 'magicband_fastpass.mp3'},
         
           # dvc welcome home
           '044d63b27c5c80': { 'color_ring' : COLOR_PURPLE,
                               'color_mouse': COLOR_PURPLE,
                               'spin_sound' : 'ring_sound.wav',
                               'hold_seconds': 1.5,
                               'sound' : 'justhome.wav'}
}



# GPIO Pin (Recommend GPIO18)
pixel_pin = board.D18


######### DON'T EDIT BELOW THIS LINE ##########################

if sys.version_info.major < 3:
    sys.exit("This script requires Python 3")

log = logging.getLogger('main')

log.setLevel(logging.CRITICAL)

# Pre init helps to get rid of sound lag
pygame.mixer.pre_init(44100, -16, 1, 512 )
pygame.mixer.init()
pygame.init()

class MagicBand(cli.CommandLineInterface):
    def __init__(self):
        self.RING_LIGHT_SIZE = 4
        self.total_pixels = ring_pixels+mickey_pixels
        self.ring_pixels = ring_pixels
        self.pixels = neopixel.NeoPixel(pixel_pin, self.total_pixels, brightness=1.0, auto_write=False, pixel_order=neopixel.RGB)
        self.rdwr_commands = { }
        self.playStartupSequence() 
        parser = ArgumentParser(
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description="")
        super(MagicBand, self).__init__(parser, groups="rdwr dbg card clf")

    def on_rdwr_startup(self, targets):
        return targets

    # play startup sequence
    def playStartupSequence(self):
        for x in range(0,3):
            self.do_lights_on(COLOR_WHITE)
            time.sleep(.5)
            self.do_lights_off()
            time.sleep(.5)

    # Preload sound
    def loadSound(self, fname):
        if fname == '':
            return False
        if not path.exists(fname):
            print("Missing sound file :" + fname)
            return False
        return True

    # play sound
    def playSound(self, fname):
        pygame.mixer.music.load(fname)
        pygame.mixer.music.play()
     

    # Returns bandid values if that bandid exists, otherwise returns random 'any*'  
    def lookupBand(self, bandid):
        if bandid in sequences:
            return sequences.get(bandid)

        # bandid not found, return a random sound that begins with 'any'
        lst = [] 
        for key,ele in sequences.items():
            if key.startswith('any'):
                lst.append(ele)
        randomsound = random.choice(lst)
        return randomsound 

    def on_rdwr_connect(self, tag):
        bandid = str(binascii.hexlify(tag.identifier),"utf-8") 
        if print_band_id == True:
            print("MagicBandId = " + bandid)
        sequence = self.lookupBand(bandid)
        self.playSequence(sequence)


    def playSequence(self, sequence):
        ringSoundFound = self.loadSound(sequence.get('spin_sound')) 
        soundFound = self.loadSound(sequence.get('sound'))
        if ringSoundFound == True:
            self.playSound(sequence.get('spin_sound'))

        self.do_lights_circle(sequence.get('color_ring'), reverse_circle)

        if soundFound == True:
            self.playSound(sequence.get('sound')) 
  
        # All lights on
        self.do_lights_on_fade(sequence.get('color_mouse'))
        time.sleep(sequence.get('hold_seconds'))
        self.do_lights_off_fade() 
        self.pixels.brightness = 1.0
        return True

    def on_card_startup(self, target):
        # Nothing needed
        log.info("Listening for magicbands")

    def color_chase(self, color, wait, reverse):
        size = self.RING_LIGHT_SIZE
        for i in range(self.ring_pixels+size+1):
            for x in range(1, size):
                if (x+i) <= self.ring_pixels:
                    pixelNum = x + i
                    if reverse == True:
                        pixelNum = self.ring_pixels- (pixelNum - 1)
                    self.pixels[pixelNum] = color
            if (i > size) :
                off = (i-size)
                if reverse == True:
                    off = self.ring_pixels- (off - 1)
                self.pixels[off] = 0
            self.pixels.show()
            time.sleep(wait)

    def do_lights_circle(self,color, reverse):
        #self.color_chase(color,.01, reverse)
        self.color_chase(color,.01, reverse)
        self.color_chase(color,.001, reverse)
        self.color_chase(color,.0001, reverse)
        self.color_chase(color,.0001, reverse)

    def do_lights_on(self, color):
        for i in range(self.total_pixels):
            self.pixels[i] = color
        self.pixels.show()

    def do_lights_on_fade(self, color):
        for i in range(self.total_pixels):
            self.pixels[i] = color
        j = .01
        for x in range(100):
            j = j + .01
            self.pixels.brightness = j
            self.pixels.show()
            time.sleep(.001)

    def do_lights_off_fade(self):
        j = 1.01
        for x in range(100):
            j = j - .01
            self.pixels.brightness = j
            self.pixels.show()
            time.sleep(.0005)
        self.do_lights_off()

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

