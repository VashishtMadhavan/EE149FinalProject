#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
 A pygame template that has the most common setup items
 Does not break into a main( ) and uses global data for simplicity
 This template is intended to be simple and easy to follow, not optimized by any means
 
 My pygame_helpers.py is recommended as a companion, as the Sprites used
 in the drawing are of types defined in this file, 
 otherwise comment out/remove these examples

 Written by Alex Kuhl
 http://www.alexkuhl.org/teaching/pygame
 Licensed under a Creative Commons Attribution-Share Alike 3.0 Unported License. 
 Must keep this entire notice in both this file and derivative works
'''

import pygame, random, sys
from pygame.locals import *
from pygame_helpers import *

# initialize pygame
pygame.init( )

# setup the screen
scr_size = ( 800, 600 )  # first is width, second height
screen = pygame.display.set_mode( scr_size )
pygame.display.set_caption( "Game Title" )

# load the background
# solid colors
background = pygame.Surface( scr_size )
background.fill( ( 0, 0, 0 ) ) # RGB colors
# for an image...
# the load_image arguments are filname, whether or not the image uses alpha, and whether uses a colorkey (we won't use colorkey)
# background = load_image( filename, True, False )[ 0 ]
# background = pygame.transform.scale( background, scr_size )

# draw background and update display
screen.blit( background, ( 0,0 ) )
pygame.display.update( ) 

pygame.mouse.set_visible( True )

random.seed( )

clock = pygame.time.Clock( )

# global data

# create groups

# the game loop -- go!
while True:
  
  # event handling goes here
  for event in pygame.event.get( ):
    if event.type == QUIT:
      sys.exit( )

  # get ticks since last call
  time_passed = clock.tick( 60 ) # tick takes optional argument that is an int for max frames per second

  # collision handling and game updates would go here
 
  # draw!
  drawgrp.clear( screen, background )
  rectlist = drawgrp.draw( screen )
  pygame.display.update( rectlist )
  #screen.blit( background, ( 0,0 ) )
  #dot.blit( screen )
  #pygame.display.flip( )

# end while (game loop)