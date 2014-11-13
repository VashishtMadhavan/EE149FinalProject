#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame, random, sys
from pygame.locals import *
from pygame import sprite, image

# initialize pygame
pygame.init( )

# setup the screen
scr_size = ( 800, 600 )  # first is width, second height
screen = pygame.display.set_mode( scr_size )
pygame.display.set_caption("DDR")

class Hand(sprite.DirtySprite):
  hand_list = sprite.Group()
  def __init__(self):
    super(Hand, self).__init__()

    self.image = self.load_image()
    self.rect = self.image.get_rect()
    Hand.hand_list.add(self)

  def load_image(self):
    return image.load('hand.jpg').convert()

# load the background
# solid colors
background = pygame.Surface(scr_size)
background = background.convert()
background.fill((0, 0, 0)) # RGB colors

# draw background and update display
screen.blit(background, (0, 0))
pygame.display.update( ) 

pygame.mouse.set_visible( True )

random.seed( )

clock = pygame.time.Clock( )

# global data

# create groups
all_hands = []
all_hands.append(Hand())

# the game loop -- go!
while True:
  
  # event handling goes here
  for event in pygame.event.get( ):
    if event.type == QUIT:
      sys.exit( )

  # get ticks since last call
  time_passed = clock.tick( 60 ) # tick takes optional argument that is an int for max frames per second

  for hand in all_hands:
      hand.rect.move_ip(1, 0)

  # collision handling and game updates would go here
 
  # draw!
  screen.blit(background, (0, 0))
  Hand.hand_list.draw(background)
  pygame.display.flip()
