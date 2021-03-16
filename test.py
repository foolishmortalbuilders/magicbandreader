
#!/usr/bin/env python
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import time

pygame.mixer.pre_init(44100, -16, 1, 512 )
pygame.mixer.init()
pygame.init()

def playSound(fname):
    print("loading sound")
    pygame.mixer.music.load(fname)
    pygame.mixer.music.set_volume(0.2)
    print("playing sound")
    pygame.mixer.music.play()
    print("sleeping")
    time.sleep(5)


if __name__ == '__main__':
    playSound("ring_sound.wav")
