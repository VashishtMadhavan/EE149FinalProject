#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from aubio import tempo, source
#from numpy import median
import pygame, random, sys, time
sys.path.insert(0, "/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python")
import lightblue
from pygame import sprite, image, QUIT, KEYDOWN

import Leap

class Bluetooth(object):

    # OpCodes and Packet IDs
    Initialize = 19
    Game_Over = 23
    Speed_Control = 31
    DriveID = 34
    ExecID1 = 35
    ExecID2 = 36
    ExecID3 = 37
    ExecID4 = 38

    MAX_DRIVE_SPEED = 6;
    MIN_DRIVE_SPEED = -6;

    def __init__(self, mac_address):
        self.s = lightblue.socket()
        self.s.connect((mac_address, 1))
        time.sleep(1)
        self.checksum = 0
        self.send(self.Initialize)
        self.checksum = 0
        self.drive_speed = 0

    def send(self, data):
        print data
        self.checksum += data
        self.s.send(chr(data))

    def fail(self):
        print 'fail'
        self.drive_speed = max(self.MIN_DRIVE_SPEED, self.drive_speed - 1)
        output_speed = self.drive_speed
        if self.drive_speed < 0: 
            output_speed = -output_speed | 8
        self.send(self.Speed_Control)
        self.send(self.DriveID)
        self.send(output_speed)

        self.send_checksum()

    def succeed(self):
        print 'success'
        self.drive_speed = min(self.MAX_DRIVE_SPEED, self.drive_speed + 1)
        output_speed = self.drive_speed
        if self.drive_speed < 0: 
            output_speed = -output_speed | 8
        self.send(self.Speed_Control)
        self.send(self.DriveID)
        self.send(output_speed)
        
        self.send_checksum()

    def send_checksum(self):
        self.send(256 - self.checksum)
        self.checksum = 0

    def game_over(self):
        self.send(self.Game_Over)


# def analyze_song(filename):
# 
#     win_s = 2048                # fft size
#     hop_s = win_s / 2           # hop size
# 
#     s = source(filename, 0, hop_s)
#     samplerate = s.samplerate
#     print (samplerate)
#     o = tempo("default", win_s, hop_s, samplerate)
# 
#     # tempo detection delay, in samples
#     # default to 4 blocks delay to catch up with
#     delay = 4. * hop_s
# 
#     # list of beats, in samples
#     beats = []
# 
#     # total number of frames read
#     total_frames = 0
#     while True:
#         samples, read = s()
#         is_beat = o(samples)
#         if is_beat:
#             this_beat = o.get_last_ms()
#             beats.append(this_beat)
#         print (o.get_bpm())
#         total_frames += read
#         if read < hop_s: break
# 
#     median_win_s = 5
#     bpms_median = [ median(beats[i:i + median_win_s:1]) for i in range(len(beats) - median_win_s ) ]
#     print (beats)
# 
#     return beats

#beats = analyze_song('song.wav')

class Hand(sprite.DirtySprite):
  left = None
  right = None
  WIDTH = 60
  HEIGHT = 80
  def __init__(self, is_left):
    super(Hand, self).__init__()

    self.image = self.load_image(is_left)
    self.rect = self.image.get_rect()
    if is_left:
        Hand.left = self
    else:
        Hand.right = self

  def load_image(self, is_left):
    hand = image.load('{}_hand.png'.format("left" if is_left else "right")).convert_alpha()
    hand = pygame.transform.scale(hand, (Hand.WIDTH, Hand.HEIGHT))
    return hand

class GlobalState(object):
    time = 0
    note_group = None
    screen = None

GS = GlobalState()

class Note(sprite.DirtySprite):
    NOTE_SPEED = 1.0
    NOTE_THRESHOLD = 30.0

    NOTE_DIEDOWN = 1000
    def __init__(self, x, y, song):
        super(Note, self).__init__()
        self.song = song

        self.real_image = self.load_image()
        self.image = pygame.Surface(self.real_image.get_rect().size)
        self.image.fill((255, 255, 255))
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
            self.song.failed_note()

        if not self.can_hit:
            percentage = (self.note_time - GS.time) / float(self.delay)
            alpha = int(255 * percentage)
            alpha = 255 - alpha
            self.image.blit(self.real_image, (0, 0))
            self.image.set_alpha(alpha)
        elif not self.hit:
            self.hit = True
            s = pygame.Surface((self.image.get_width(), self.image.get_height())).convert_alpha()
            s.fill((0, 255, 0, 128))
            self.image.blit(s, (0, 0))

    def set_delay(self, delay):
        self.delay = delay

class Song(object):
    MAX_THRESHOLD = 8
    MIN_THRESHOLD = 0
    def __init__(self, filename, sprite_group):
        self.sound = pygame.mixer.Sound(filename)
        self.group = sprite_group
        self.last_time = 0
        self.bpm = 90
        self.bpms = self.bpm / (60.0 * 1000)
        self.mspb = 1.0 / self.bpms
        self.delay = 2000
        self.start_time = 0

        self.tally = 0
        self.threshold = 8
        self.good_run = True

    def play(self):
        self.sound.play()

    def init(self, time):
        self.start_time = time

    def update(self):
        time = GS.time - self.start_time
        if (time - self.last_time) > self.mspb:
            choose_pos = lambda: (random.randrange(200, 600), random.randrange(100, 500))
            while True:
                pos = choose_pos()
                note = Note(pos[0], pos[1], self)
                if not pygame.sprite.spritecollideany(note, self.group):
                    break
            note.set_delay(self.delay)
            self.group.add(note)
            self.last_time += self.mspb

    def failed_note(self):
        if self.good_run:
            self.good_run = False
            self.tally = 0

        if self.tally > self.threshold:
            self.tally = 0
            self.threshold = max(self.threshold - 1, self.MIN_THRESHOLD)
            #bluetooth.fail()
        else:
            self.tally += 1

    def good_note(self):
        if not self.good_run:
            self.good_run = True
            self.tally = 0

        if self.tally > self.threshold:
            self.tally = 0
            self.threshold = max(self.threshold + 1, self.MAX_THRESHOLD)
            #bluetooth.succeed()
        else:
            self.tally += 1

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

    blue = Bluetooth('00:06:66:00:A6:9B')

    return screen, background, clock, controller, blue


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
    screen, background, clock, controller, bluetooth = init(filename)
    all_sprites, all_hands, all_notes, song = init_models(filename)
    font = pygame.font.Font(None, 32)
    GS.screen = screen

    chan = song.sound.play()
    total_time = 0
    song.init(pygame.time.get_ticks())
    score = 0
    while True:
      # event handling goes here
      for event in pygame.event.get( ):
        if event.type == QUIT:
          sys.exit( )
        elif event.type == KEYDOWN:
          if event.unicode.lower() == 'q':
            sys.exit()
          elif event.unicode.lower() == 'a':
            bluetooth.succeed()
          elif event.unicode.lower() == 'b':
            bluetooth.fail()
          elif event.unicode.lower() == 'g':
            bluetooth.game_over()

      # get ticks since last call
      time_passed = clock.tick( 60 ) # tick takes optional argument that is an int for max frames per second

      for hand in all_hands.sprites():
          hand.rect.center = (-hand.rect.width*2, -hand.rect.height*2)

      if not pygame.mixer.get_busy():
        bluetooth.game_over()
        print 'game over'

      screen.blit(background, (0, 0))
      frame = controller.frame()
      for hand in frame.hands:
          conv = transform_coordinates(hand.palm_position)
          hand_o = (Hand.left if hand.is_left else Hand.right)
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
              song.good_note()
      surface = font.render(str(score), True, (0, 255, 0))
      screen.blit(surface, (30, 30))
      pygame.display.flip()
