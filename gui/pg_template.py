#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
sys.path.insert(0, os.environ.get('LEAPMOTION_SDK'))
import pygame, random, sys
from pygame import sprite, image, QUIT

import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

class Hand(sprite.DirtySprite):
  def __init__(self):
    super(Hand, self).__init__()

    self.image = self.load_image()
    print self.image
    print self.image
    self.rect = self.image.get_rect()

  def load_image(self):
    return image.load('hand.jpg').convert()

class GlobalState(object):
    time = 0
    note_group = None

GS = GlobalState()

class Note(sprite.DirtySprite):
    NOTE_SPEED = 1.0
    NOTE_THRESHOLD = 30.0
    def __init__(self, time, x, y):
        super(Note, self).__init__()
        self.image = self.load_image()
        self.rect = self.image.get_rect()
        self.time = time
        self.rect.x = x
        self.rect.y = y

    def load_image(self):
        return pygame.transform.scale(image.load('note.jpg').convert(), (32, 32))

    def update(self):
        pass

class Song(object):
    def __init__(self, filename):
        self.song = self.load_file(filename)

    def load_file(self, filename):
        with open(filename) as f:
            read = f.read()

        lines = read.split('\n')
        notes = [line.split(' ') for line in lines if line]
        for i in range(len(notes)):
            time, x, y = notes[i]
            try:
                time = float(time)
                x = int(x)
                y = int(y)
                notes[i] = (time, x, y)
            except ValueError:
                print "Invalid format for song {}".format(filename)
                raise
        return notes

    def get_notes(self):
        g = sprite.Group()
        for note in self.song:
            g.add(Note(*note))
        return g


WIDTH = 800
HEIGHT = 600
def init():
    # initialize leap motion
    controller = Leap.Controller()

    # initialize pygame
    pygame.init()

    # setup the screen
    scr_size = (WIDTH, HEIGHT)  # first is width, second height
    screen = pygame.display.set_mode(scr_size)
    pygame.display.set_caption("DDR")

    # load the background
    # solid colors
    background = pygame.Surface(scr_size)
    background = background.convert()
    background.fill((0, 0, 0)) # RGB colors

    # draw background and update display
    screen.blit(background, (0, 0))
    pygame.display.flip() 

    pygame.mouse.set_visible(True)

    random.seed()

    clock = pygame.time.Clock()
    return screen, background, clock, controller


# create groups
def init_models():
    hand_group = sprite.Group()
    for _ in range(2):
        hand_group.add(Hand())

    song = Song('test_song')
    note_group = song.get_notes()

    group = sprite.Group()
    for s in hand_group.sprites():
        group.add(s)

    for s in note_group.sprites():
        group.add(s)

    return group, hand_group, note_group, song

def transform_coordinates(pos):
    return ((100-pos.x)*(HEIGHT/100), (100-pos.y)/(WIDTH/100))

if __name__ == "__main__":
    screen, background, clock, controller = init()
    all_sprites, all_hands, all_notes, song = init_models()

    while True:
      # event handling goes here
      for event in pygame.event.get( ):
        if event.type == QUIT:
          sys.exit( )

      # get ticks since last call
      time_passed = clock.tick( 60 ) # tick takes optional argument that is an int for max frames per second

      all_hands.sprites()[0].rect.move_ip(1, 0)
      all_hands.sprites()[1].rect.move_ip(0, 1)

      # collision handling and game updates would go here

      frame = controller.frame()
      for i, hand in enumerate(frame.hands):
          print hand.palm_position
          conv = transform_coordinates(hand.palm_position)
          hand = all_hands.sprites()[i]
          print conv
          hand.rect.x = conv[0]
          hand.rect.y = conv[1]
     
      # draw!
      screen.blit(background, (0, 0))
      all_sprites.draw(screen)
      pygame.display.flip()
