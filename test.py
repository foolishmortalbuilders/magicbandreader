#!/usr/bin/env python
from __future__ import print_function
import pygame
import argparse
import binascii
import logging
import hashlib
import struct
# import ndef
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
from threading import Thread, Event

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

config = configobj.ConfigObj('settings.conf')
print_band_id = bool(config['Settings']['print_band_id'])
reverse_circle = bool(config['Settings']['reverse_circle'])
ring_pixels = int(config['Settings']['ring_pixels'])
mickey_pixels = int(config['Settings']['mickey_pixels'])

COLORS = {
    "red": (0, 255, 0),
    "electricred": (228, 3, 3),
    "orange": (255, 165, 0),
    "dark orange": (255, 140, 0),
    "yellow": (255, 255, 0),
    "canaryyellow": (255, 237, 0),
    "green": (255, 0, 0),
    "lasallegreen": (0, 128, 38),
    "blue": (0, 0, 255),
    "patriarch": (117, 7, 135),
    "lightblue": (153, 204, 255),
    "white": (255, 255, 255),
    "purple": (0, 153, 153),
    "gray": (128, 128, 128),
    "stitch": (0, 39, 144),
    "rainbow": (0, 0, 0),
    "pride": (0, 0, 1),
}
sequences = config['sequences']

# GPIO Pin (Recommend GPIO18) GPIO13 is also a good choice
pixel_pin = board.D18

if sys.version_info.major < 3:
    sys.exit("This script requires Python 3")

log = logging.getLogger('main')

log.setLevel(logging.CRITICAL)

# Pre init helps to get rid of sound lag
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()
pygame.init()


def playLightSequence(magicBandScannedEvent, ringPixels, totalPixels, magicBandObject):
    lightSpeed = .1
    pixelRingArray = list(range(0, ringPixels-1))
    pixels = neopixel.NeoPixel(
        pixel_pin, totalPixels, brightness=1.0, auto_write=False, pixel_order=neopixel.RGB)

    while not True:
        if not magicBandScannedEvent.isSet():
            lightSpeed = .1
        else:
            lightSpeed = lightSpeed * .75

        if lightSpeed < 0.00001:
            if magicBandObject.success == True:
                showAllColored(pixels, COLORS["green"])
                time.sleep(5)
                lightSpeed = .1
        else:
            leadingIndex = pixelRingArray[0]
            fadePixel(true, pixels[leadingIndex])
            trailingIndex = pixelRingArray[4]
            fadePixel(false, pixels[trailingIndex])
            time.sleep(lightSpeed)
            leftRotate(pixelRingArray)


def showAllColored(pixels, color):
    for i in range(self.total_pixels):
            pixels[i] = color

        pixels.show()


def leftRotate(array, d, n):
    for i in range(d):
            leftRotateByOne(array, n)


def leftRotateByOne(array, n):
    temp = array[0]
    for i in range(n-1):
        array[i] = array[i + 1]
    array[n-1] = temp


def fadePixel(out, pixel):
    if out:
        brightness = 1.01
        for x in range(100):
            brightness =- .01
            pixel.brightness = brightness
            pixel.show()
            time.sleep(.001)
    if not out:
        brightness = .01
        for x in range(100):
            brightness =+ .01
            pixels.brightness = brightness
            pixels.show()
            time.sleep(.001)

class MagicBand():
    def __init__(self):
        self.success = true
        self.successSequence = []

class BandScannerAndSound(cli.CommandLineInterface):
    def __init__(self, magicBandObject, scannedEvent):
        self.bandObject = magicBandObject
        self.scannedEvent = scannedEvent

    def on_rdwr_startup(self, targets):
        return targets

    def on_rdwr_connect(self, tag):
        bandid = str(binascii.hexlify(tag.identifier),"utf-8") 
        if print_band_id == True:
            print("MagicBandId = " + bandid)

            self.scannedEvent.set()
            sequences = config['bands'].get(bandid) or config['bands']['unknown']
            if sequences:
                sequences = sequences if type(sequences) == list else [sequences,]
                self.playSound(sequence.get('spin_sound'))

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
        if self.loadSound(fname) == True:
            pygame.mixer.music.load(fname)
            pygame.mixer.music.set_volume(1)
            pygame.mixer.music.play()

    def on_card_startup(self, target):
        # Nothing needed
        log.info("Listening for magicbands")

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
    magicBandScannedEvent = threading.Event()
    magicBandObject = MagicBand()
    
    try:
        lightsThread = Thread(name='lights',
                target=playLightSequence, args=(magicBandScannedEvent, ring_pixels, ring_pixels+mickey_pixels, magicBandObject))

        bandAndSound = BandScannerAndSound(magicBandObject)
        bandThread = Thread(="band",
                        target=bandAndSound.run)

        lightsThread.start()
        lightsThread.join()
    except ArgparseError as e:
        print("exception")
        print(e)
        _prog = e.args[1].split()
    else:
        sys.exit(0)
