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
import threading

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
    pixels = neopixel.NeoPixel(pixel_pin, totalPixels, brightness=1.0, auto_write=False, pixel_order=neopixel.RGB)
    print("Playing light sequence")

    while True:
        if not magicBandScannedEvent.isSet():
            lightSpeed = .1
        else:
            lightSpeed = lightSpeed * .95

        if lightSpeed < 0.00001:
            if magicBandObject.success == True:
                showAllColored(pixels, COLORS["green"], totalPixels)
                time.sleep(2)
                magicBandScannedEvent.clear()
                doLightFadeOff(pixels, totalPixels)
                pixels.brightness = 1.0
                lightSpeed = .1
        else:
            leadingIndex = pixelRingArray[4]
            trailingIndex = pixelRingArray[0]
            #print("fadePixel in", leadingIndex)
            pixels[leadingIndex] = fadePixel(False, pixels[leadingIndex])
            pixels[trailingIndex] = fadePixel(True, pixels[trailingIndex])
            #pixels[trailingIndex] = 0
            #print("fadePixel out", trailingIndex)
            pixels.show()
            time.sleep(lightSpeed)
            pixelRingArray = rotateArray(pixelRingArray, len(pixelRingArray), 1)

def doLightFadeOff(pixels, totalPixels):
    brightness = 1.01
    for x in range(100):
        brightness = brightness - .01
        pixels.brightness = brightness
        pixels.show()
        time.sleep(.0005)
    doLightsOff(pixels, totalPixels)

def doLightsOff(pixels, totalPixels):
    for i in range(totalPixels):
        pixels[i] = 0 
    pixels.show()

def showAllColored(pixels, color, total):
    for i in range(total):
        pixels[i] = color

    pixels.show()

def rotateArray(arr, n, d):
    temp = []
    i = 0
    while (i < d):
        temp.append(arr[i])
        i = i + 1
    i = 0
    while (d < n):
        arr[i] = arr[d]
        i = i + 1
        d = d + 1
    arr[:] = arr[: i] + temp
    return arr

def printArray(arr,size):
    for i in range(size):
        print ("%d"% arr[i],end=" ")


def fadePixel(out, pixel):
    if out:
        return (0, 0, 0)
    if not out:
        return COLORS["white"]

class MagicBand():
    def __init__(self):
        self.success = True
        self.successSequence = []

class BandScannerAndSound(cli.CommandLineInterface):
    def __init__(self, magicBandObject, scannedEvent):     
        print("Started Scanner")
        self.bandObject = magicBandObject
        self.scannedEvent = scannedEvent
        self.rdwr_commands = { }

        parser = ArgumentParser(
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description="")
        super(BandScannerAndSound, self).__init__(parser, groups="rdwr dbg card clf")

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
            sequence = config['sequences'][random.choice(sequences)]
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
            pygame.mixer.music.set_volume(0.5)
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
        lightsThread = threading.Thread(name='lights',
                target=playLightSequence, args=(magicBandScannedEvent, ring_pixels, ring_pixels+mickey_pixels, magicBandObject), daemon = True)

        lightsThread.start()
        bandAndSound = BandScannerAndSound(magicBandObject, magicBandScannedEvent)
        bandAndSound.run()
        lightsThread.join()

    except ArgparseError as e:
        print("exception")
        print(e)
        _prog = e.args[1].split()
    else:
        sys.exit(0)
