#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from aubio import tempo, source
#from numpy import median
from __future__ import print_function
import pygame, random, sys, time, os, json
sys.path.insert(0, "/System/Library/Frameworks/Python.framework/Versions/Current/Extras/lib/python")
import lightblue
from pygame import sprite, image, QUIT, KEYDOWN

import threading

DEBUG_MODE = 0

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

    MAX_DRIVE_SPEED = 7;
    MIN_DRIVE_SPEED = -7;

    # Set to false for PLAY
    DEBUG_MODE = True

    def __init__(self, mac_address):
        self.s = lightblue.socket()
        self.s.connect((mac_address, 1))
        self.checksum = 0
        self.send(self.Initialize)
        self.checksum = 0
        self.drive_speed = 0

    def send(self, data):
        print('SENDING BLUETOOTH', data)
        self.checksum += data
        self.s.send(chr(data))

    def recv(self, *args):
        return self.s.recv(*args)

    def fail(self):
        if DEBUG_MODE:
            print('0')
            self.send(0)
            return

        self.drive_speed = max(self.MIN_DRIVE_SPEED, self.drive_speed - 1)
        output_speed = self.drive_speed
        if self.drive_speed < 0: 
            output_speed = -output_speed | 8

        self.send(self.Speed_Control)
        self.send(self.DriveID)
        self.send(output_speed)

        self.send_checksum()

    def succeed(self):
        if DEBUG_MODE:
            print('1')
            self.send(1)
            return

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
    errors = 0

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

SCORING_METHODS = {}
def scoring_method(func):
    name = func.__name__
    SCORING_METHODS[name] = func
    return func

@scoring_method
def simple(self, failed, bluetooth):
    if failed:
        bluetooth.fail()
    else:
        bluetooth.succeed()

@scoring_method
def constant_threshold(self, failed, bluetooth):
    if self.good_run and failed:
        self.good_run = False
        self.tally = -1
    elif (not self.good_run) and not failed:
        self.good_run = True
        self.tally = -1

    if failed:
        bluetooth.fail()
        self.tally = 0
        return

    if self.tally > max(abs(self.bluetooth.drive_speed), 2):
        self.tally = 0
        bluetooth.succeed()
    else:
        self.tally += 1

@scoring_method
def growing_threshold(self, failed, bluetooth):
    if self.good_run and failed:
        self.good_run = False
        self.tally = -1
    elif (not self.good_run) and not failed:
        self.good_run = True
        self.tally = -1

    if failed:
        bluetooth.fail()
        self.tally = 0
        return

    if self.tally > max(abs(self.bluetooth.drive_speed), 2):
        self.tally = 0
        bluetooth.succeed()
    else:
        self.tally += 1

DEFAULT_THRESHOLD = 3

class Song(object):
    def __init__(self, song, sprite_group, scoring_method, bluetooth):
        path = os.path.join('songs', song['name'], 'song.wav')
        self.sound = pygame.mixer.Sound(path)
        self.group = sprite_group
        self.last_time = 0

        self.bpm = song['bpm']
        self.bpms = self.bpm / (60.0 * 1000)
        self.mspb = 1.0 / self.bpms
        self.delay = 2000
        self.start_time = 0

        self.tally = 0
        self.good_run = True
        self.scoring_method = scoring_method
        self.bluetooth = bluetooth

        self.prev_time = 0
        self.accum_dist = 0

    def play(self):
        self.sound.play()

    def init(self, time):
        self.start_time = time

    def update(self):
        curr_time = time.time()
        if self.prev_time != 0:
            self.accum_dist += (curr_time - self.prev_time) * (self.bluetooth.drive_speed * 50)
        self.prev_time = curr_time

        adjusted_time = GS.time - self.start_time
        if (adjusted_time - self.last_time) > self.mspb:
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
        methd = self.scoring_method
        return methd(self, True, self.bluetooth)

    def good_note(self):
        methd = self.scoring_method
        return methd(self, False, self.bluetooth)

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
    background.fill((255, 255, 255)) # RGB colors

    # draw background and update display
    screen.blit(background, (0, 0))
    pygame.display.flip() 

    pygame.mouse.set_visible(True)

    random.seed()

    clock = pygame.time.Clock()

    return screen, background, clock, controller

def connect_bluetooth():
    blue = Bluetooth('00:06:66:00:A6:9B')
    return blue



# create groups
def init_models(filename, scoring_method, bluetooth):
    hand_group = sprite.Group()
    for i in range(2):
        hand_group.add(Hand(i==0)) # left or right hand

    note_group = sprite.Group()
    song = Song(filename, note_group, scoring_method, bluetooth)

    group = sprite.Group()
    for s in hand_group.sprites():
        group.add(s)

    return group, hand_group, note_group, song

VIEWPORT_LEN = 120
def transform_coordinates(pos):
    """Transforms the coordinate system of the Leap Motion to the screen"""
    return ((pos.x + VIEWPORT_LEN) / (VIEWPORT_LEN * 2) * WIDTH, (pos.z + VIEWPORT_LEN) / (VIEWPORT_LEN * 2) * HEIGHT)

def load_song_names():
    songs = os.listdir('songs')
    songs = [x for x in songs if not x[0] == '.']
    l = []
    for song in songs:
        with open(os.path.join('songs', song, 'config.json')) as f:
            j = json.load(f)
            j['name'] = song
            l.append(j)
    return l

stop = threading.Event()

def game_over_check(bluetooth):
    bluetooth.s.setblocking(False)
    accum_messages = ""
    while not stop.is_set():
        a = None
        try:
            a = bluetooth.recv(100)
        except Exception, e:
            # These two errors occur because we're in non-blocking mode. Ignore them. 
            if 'Resource temporarily unavailable' in str(e):
                pass
            elif 'Connection reset by peer' in str(e):
                pass
            else:
                print(e)
                print(e.message)
        if a:
            print(a, end='', sep='')
            accum_messages += a

INIT = 0
LOADING = 1
PLAYING = 2
PICK_DIFFICULTY = 3

MAX_DIST = 1800

def main():
    state = INIT
    screen, background, clock, controller = init()
    font = pygame.font.Font(None, 32)
    GS.screen = screen
    score = 0
    index = 0

    def quit():
        stop.set()
        sys.exit()

    songs = load_song_names()
    scoring_methods = SCORING_METHODS.items()
    while True:
        if stop.is_set():
            break
        if state == PLAYING:
          for event in pygame.event.get( ):
            if event.type == QUIT:
              sys.exit( )
            elif event.type == KEYDOWN:
              if event.unicode.lower() == 'q':
                quit()
              elif event.unicode.lower() == 'a':
                bluetooth.succeed()
              elif event.unicode.lower() == 'b':
                bluetooth.fail()
              elif event.unicode.lower() == 'g':
                bluetooth.game_over()

          if not pygame.mixer.get_busy():
            bluetooth.game_over()
            print('game over')
            quit()

          screen.blit(background, (0, 0))

          frame = controller.frame()
          for hand in frame.hands:
              conv = transform_coordinates(hand.palm_position)
              hand_o = (Hand.left if hand.is_left else Hand.right)
              hand_o.rect.center = conv
         
          # draw!
          all_notes.update()
          GS.time = pygame.time.get_ticks()
          song.update()
          all_notes.draw(screen)
          all_sprites.draw(screen)
          collided = pygame.sprite.groupcollide(all_notes, all_hands, False, False)
          for note in collided:
              if note.can_hit:
                  note.kill()
                  song.good_note()

          if song.accum_dist > MAX_DIST or song.accum_dist < 0:
              bluetooth.game_over()
              quit()

          surface = font.render("Drive speed: {}".format(bluetooth.drive_speed), True, (0, 255, 0))
          screen.blit(surface, (30, 30))
          surface = font.render("GS ERRORS: {}".format(GS.errors), True, (0, 255, 0))
          screen.blit(surface, (30, 70))
          surface = font.render("accum dist: {}".format(song.accum_dist), True, (0, 255, 0))
          screen.blit(surface, (30, 100))
          pygame.display.flip()
        elif state == INIT:
            screen.fill((255, 255, 255))

            for event in pygame.event.get( ):
                if event.type == QUIT:
                    sys.exit( )
                elif event.type == KEYDOWN:
                    if event.unicode.lower() == ' ':
                        filename = songs[index]
                        state = PICK_DIFFICULTY
                    elif event.key == pygame.K_UP:
                        index -= 1
                    elif event.key == pygame.K_DOWN:
                        index += 1
                    elif event.unicode.lower() == 'q':
                        quit()

            surface = font.render("spacebar to select song, up and down arrow to scroll", True, (0, 255, 0))
            screen.blit(surface, (30, 30))
            top = 60
            index = min(index, len(songs) - 1)
            index = max(index, 0)
            for i, song in enumerate(songs):
                s = song['title']
                if i == index:
                    s = '>>' + s + '<<'
                surface = font.render(s, True, (0, 255, 0))
                screen.blit(surface, (45, top))
                top += 30
            pygame.display.flip()
        elif state == PICK_DIFFICULTY:
            screen.fill((255, 255, 255))

            for event in pygame.event.get( ):
                if event.type == QUIT:
                    sys.exit( )
                elif event.type == KEYDOWN:
                    if event.unicode.lower() == ' ':
                        scoring_method = scoring_methods[index][1]
                        state = LOADING
                    elif event.key == pygame.K_UP:
                        index -= 1
                    elif event.key == pygame.K_DOWN:
                        index += 1
                    elif event.unicode.lower() == 'q':
                        quit()

            surface = font.render("spacebar to select method, up and down arrow to scroll", True, (0, 255, 0))
            screen.blit(surface, (30, 30))
            top = 60
            index = min(index, len(scoring_methods) - 1)
            index = max(index, 0)
            for i, meth in enumerate(scoring_methods):
                s = meth[0]
                if i == index:
                    s = '>>' + s + '<<'
                surface = font.render(s, True, (0, 255, 0))
                screen.blit(surface, (45, top))
                top += 30
            pygame.display.flip()

        elif state == LOADING:
            surface = font.render("loading...", True, (0, 255, 0))
            screen.fill((255, 255, 255))
            screen.blit(surface, (30, 30))
            pygame.display.flip()

            bluetooth = connect_bluetooth()
            game_over_t = threading.Thread(target=lambda: game_over_check(bluetooth))
            game_over_t.daemon = True
            game_over_t.start()
            all_sprites, all_hands, all_notes, song = init_models(filename, scoring_method, bluetooth)

            chan = song.sound.play()
            total_time = 0
            song.init(pygame.time.get_ticks())
            state = PLAYING

if __name__ == "__main__":
    main()
