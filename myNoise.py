import pygame
import threading
import prctl

''' we use pygame for playback, because vlc does not handle gapless playback '''

pygame.mixer.init(channels=1, buffer=8192) # high buffer should prevent stutter when loading files
pygame.mixer.set_num_channels(8)

channel = pygame.mixer.find_channel()

def setVolume(volume):
  volume = volume / 100 # method requires a value 0.0-1.0
  volume = volume * 0.05 # tune the noise down, because it is just VEEEERY loud
  channel.set_volume(volume)

setVolume(0)
sound = pygame.mixer.Sound(file="./35291__jace__continuous-static.wav")
channel.play(sound, loops=-1)
