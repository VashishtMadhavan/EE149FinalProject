#!/usr/bin/env python
# -*- coding: utf-8 -*-

from aubio import tempo, source
from numpy import median

def analyze_song(filename):

    win_s = 2048                # fft size
    hop_s = win_s / 2           # hop size

    s = source(filename, 0, hop_s)
    samplerate = s.samplerate
    print samplerate
    o = tempo("default", win_s, hop_s, samplerate)

    # tempo detection delay, in samples
    # default to 4 blocks delay to catch up with
    delay = 4. * hop_s

    # list of beats, in samples
    beats = []

    # total number of frames read
    total_frames = 0
    while True:
        samples, read = s()
        is_beat = o(samples)
        if is_beat:
            this_beat = o.get_last_ms()
            beats.append(this_beat)
        print o.get_bpm()
        total_frames += read
        if read < hop_s: break

    median_win_s = 5
    bpms_median = [ median(beats[i:i + median_win_s:1]) for i in range(len(beats) - median_win_s ) ]
    print beats

    return beats

#beats = analyze_song('song.wav')

import os, sys
sys.path.insert(0, os.environ.get('LEAPMOTION_SDK'))
import pygame, random, sys
from pygame import sprite, image, QUIT

import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

class Hand(sprite.DirtySprite):
  left_hand = None
  right_hand = None
  WIDTH = 60
  HEIGHT = 80
  def __init__(self, is_left):
    super(Hand, self).__init__()

    self.image = self.load_image(is_left)
    self.rect = self.image.get_rect()
    if is_left:
        Hand.left_hand = self
    else:
        Hand.right_hand = self

  def load_image(self, is_left):
    hand = image.load('{}_hand.png'.format("left" if is_left else "right")).convert_alpha()
    hand = pygame.transform.scale(hand, (Hand.WIDTH, Hand.HEIGHT))
    return hand

class GlobalState(object):
    time = 0
    note_group = None

GS = GlobalState()

class Note(sprite.DirtySprite):
    NOTE_SPEED = 1.0
    NOTE_THRESHOLD = 30.0

    NOTE_DIEDOWN = 1000
    def __init__(self, x, y):
        super(Note, self).__init__()
        self.image = self.load_image()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.delay = 0
        self.created = GS.time
        self.hit = False

    @property
    def note_time(self):
        return self.created + self.delay

    @property
    def can_hit(self):
        return (GS.time - self.note_time) > 0

    def load_image(self):
        return pygame.transform.scale(image.load('note.jpg').convert_alpha(), (64, 64))

    def update(self):
        if GS.time > (self.note_time + Note.NOTE_DIEDOWN):
            self.kill()

        if not self.hit and (GS.time - self.note_time) > 0:
            n = self.image.convert_alpha()
            # red at 50%
            n.fill((255,0,0,127))
            self.image.blit(n, (0,0))
            self.hit = True

    def set_delay(self, delay):
        self.delay = delay

class Song(object):
    def __init__(self, filename, sprite_group):
        self.sound = pygame.mixer.Sound(filename)
        self.group = sprite_group
        self.last_time = 0
        self.bpm = 135
        self.bpms = self.bpm / (60.0 * 1000)
        self.mspb = 1.0 / self.bpms
        print self.mspb
        self.delay = 1000
        self.start_time = 0

    def play(self):
        self.sound.play()

    def init(self, time):
        self.start_time = time

    def update(self):
        #if not time > 3000:
            #self.last_time = time
            #return

        time = GS.time
        time += self.delay
        time -= self.start_time
        if (time - self.last_time) > self.mspb:
            note = Note(random.randrange(40, 800), random.randrange(40, 600))
            note.set_delay(self.delay)
            self.group.add(note)
            self.last_time += self.mspb

WIDTH = 800
HEIGHT = 600

def init(filename):
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
    background.fill((255, 255, 255)) # RGB colors

    # draw background and update display
    screen.blit(background, (0, 0))
    pygame.display.flip() 

    pygame.mouse.set_visible(True)

    random.seed()

    clock = pygame.time.Clock()

    return screen, background, clock, controller


# create groups
def init_models(filename):
    hand_group = sprite.Group()
    for i in range(2):
        hand_group.add(Hand(i==0))

    note_group = sprite.Group()
    song = Song(filename, note_group)

    group = sprite.Group()
    for s in hand_group.sprites():
        group.add(s)

    return group, hand_group, note_group, song

VIEWPORT_LEN = 120
def transform_coordinates(pos):
    return ((pos.x + VIEWPORT_LEN) / (VIEWPORT_LEN * 2) * WIDTH, (pos.z + VIEWPORT_LEN) / (VIEWPORT_LEN * 2) * HEIGHT)

if __name__ == "__main__":
    filename = 'song.wav'
    screen, background, clock, controller = init(filename)
    all_sprites, all_hands, all_notes, song = init_models(filename)
    font = pygame.font.Font(None, 32)

    chan = song.sound.play()
    total_time = 0
    song.init(pygame.time.get_ticks())
    score = 0
    while True:
      # event handling goes here
      for event in pygame.event.get( ):
        if event.type == QUIT:
          sys.exit( )

      # get ticks since last call
      time_passed = clock.tick( 60 ) # tick takes optional argument that is an int for max frames per second

      for hand in all_hands.sprites():
          hand.rect.center = (-hand.rect.width*2, -hand.rect.height*2)

      # collision handling and game updates would go here

      screen.blit(background, (0, 0))
      frame = controller.frame()
      for hand in frame.hands:
          conv = transform_coordinates(hand.palm_position)
          hand_o = (Hand.left_hand if hand.is_left else Hand.right_hand)
          hand_o.rect.center = conv
     
      # draw!
      all_notes.update()
      all_sprites.draw(screen)
      GS.time = pygame.time.get_ticks()
      song.update()
      all_notes.draw(screen)
      collided = pygame.sprite.groupcollide(all_notes, all_hands, False, False)
      for note in collided:
          if note.can_hit:
              note.kill()
              score += 10
      surface = font.render(str(score), True, (0, 255, 0))
      screen.blit(surface, (30, 30))
      pygame.display.flip()
