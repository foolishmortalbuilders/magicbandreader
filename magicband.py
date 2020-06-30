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
import configobj
from json import dumps
from httplib2 import Http

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

config = configobj.ConfigObj('settings.conf')
print_band_id = bool(config['Settings']['print_band_id'])
reverse_circle = bool(config['Settings']['reverse_circle'])
ring_pixels = int(config['Settings']['ring_pixels'])
mickey_pixels = int(config['Settings']['mickey_pixels'])

COLORS = {
    "red" : (0,255,0),
    "electricred" : (228,3,3),
    "orange" : (255,165,0),
    "dark orange" : (255,140,0),
    "yellow" : (255,255,0),
    "canaryyellow" : (255,237,0),
    "green": (255,0,0),
    "lasallegreen" : (0,128,38),
    "blue" : (0,0,255),
    "patriarch" : (117,7,135),
    "lightblue" : (153,204,255),
    "white" : (255,255,255),
    "purple" : (0,153,153),
    "gray" : (128,128,128),
    "stitch" : (0,39,144),
    "rainbow" : (0,0,0),
    "pride" : (0,0,1),
}
sequences = config['sequences']

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

    # rainbow stuff
    @staticmethod
    def wheel(pos):
        if pos < 85:
             return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
             pos -= 85
             return (255 - pos * 3, 0, pos * 3)
        else:
             pos -= 170
             return (0, pos * 3, 255 - pos * 3)

    # play startup sequence
    def playStartupSequence(self):
        for x in range(0,3):
            self.do_lights_on(COLORS["white"])
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
    # New "unknown" value in settings.conf overrides this  
    def lookupBand(self, bandid):
        if bandid in sequences:
            return sequences.get(bandid)

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

        sequences = config['bands'].get(bandid) or config['bands']['unknown']
        if sequences:
            sequences = sequences if type(sequences) == list else [sequences,]
            self.playSequence(config['sequences'][random.choice(sequences)])

    def playSequence(self, sequence):
        ringSoundFound = self.loadSound(sequence.get('spin_sound')) 
        soundFound = self.loadSound(sequence.get('sound'))
        if ringSoundFound == True:
            self.playSound(sequence.get('spin_sound'))

        self.do_lights_circle(COLORS[sequence.get('color_ring')], reverse_circle)

        if soundFound == True:
            self.playSound(sequence.get('sound')) 

        webhooks = sequence.get('webhooks', [])
        if webhooks:
            webhooks = webhooks if type(webhooks) == list else [webhooks,]
        for hook in webhooks:
           message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
           http_obj = Http()
           response = http_obj.request(
              uri=hook,
              method='POST',
              headers=message_headers,
           )
           print(response)

        # All lights on
        self.do_lights_on_fade(COLORS[sequence.get('color_mouse')])
        time.sleep(int(sequence.get('hold_seconds')))
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

    def rainbowCycle(self, wait_ms, iterations):
        size = self.RING_LIGHT_SIZE
        for j in range(256*iterations):
            for i in range(self.ring_pixels):
                self.pixels[i] = self.wheel((int(i * 256 / self.ring_pixels) + j) & 255)
                #print(self.wheel((int(i * 256 / self.ring_pixels) + j) & 255))
            self.pixels.show()
            time.sleep(wait_ms/1000)

    def theaterChase(self, wait_ms=20, iterations=5):
        for j in range(256*iterations):
            for i in range(self.ring_pixels):
                if (i + j) % 3 == 0 :
                    self.pixels[i] = (255,0,0)
                else:
                    self.pixels[i] = (0,255,0)
            self.pixels.show()
            time.sleep(wait_ms/1000)

    def do_lights_circle(self,color, reverse):
        if color == COLORS['rainbow']:
            self.rainbowCycle(1,1)
        elif color == COLORS['pride']:
            self.color_chase((228,3,3),.001, reverse)
            self.color_chase((255,140,0),.0001, reverse)
            self.color_chase((255,237,0),.0001, reverse)
            self.color_chase((0,128,38),.0001, reverse)
            self.color_chase((0,77,255),.0001, reverse)
            self.color_chase((117,7,135),.0001, reverse)
        else:
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
