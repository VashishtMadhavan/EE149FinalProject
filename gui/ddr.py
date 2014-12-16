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
start = None
TIME = []

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
        #self.s.connect((mac_address, 1))
        self.checksum = 0
        #self.send(self.Initialize)
        self.checksum = 0
        self.drive_speed = 0

    def send(self, data):
        self.checksum += data
        #self.s.send(chr(data))

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
        TIME.append(start - time.time())
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
    self.real_image = self.load_image(is_left)
    self.rect = self.image.get_rect()
    if is_left:
        Hand.left = self
    else:
        Hand.right = self

  def load_image(self, is_left):
    hand = image.load('{}_hand.png'.format("left" if is_left else "right")).convert_alpha()
    hand = pygame.transform.scale(hand, (Hand.WIDTH, Hand.HEIGHT))
    return hand

  def rotate(self, angle):
    angle = -(angle * 180 / Leap.PI)
    self.image = pygame.transform.rotate(self.real_image, angle)

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

class ProgressBar(sprite.DirtySprite):
    def __init__(self, title, max_value, rect, background_color=None):
        super(ProgressBar, self).__init__()
        self.title = title
        self.max_value = max_value
        self.rect = rect
        self.image = pygame.Surface((self.rect.width, self.rect.height)).convert()
        if not background_color:
            background_color = (255, 255, 255)
        self.background_color = background_color
        self.line_color = (255, 0, 0)
        self.progress_color = (0, 255, 0)
        self.robot_color = (0, 0, 255)

    def progress(self, value):
        self.value = value

    def update(self):
        self.image.fill(self.background_color)

        pos = (self.value / self.max_value) * self.rect.width

        font = pygame.font.Font(None, 32)
        text_size = font.size(self.title)
        rendered = font.render(self.title, True, (0, 0, 0))
        text_pos = self.rect.width/2 - text_size[0]/2, 0
        self.image.blit(rendered, text_pos)

        start = 0, self.rect.height / 2
        end = self.rect.right, self.rect.height / 2
        pygame.draw.line(self.image, self.line_color, start, end, 2)
        robot_pos = int(pos), self.rect.height / 2
        pygame.draw.circle(self.image, self.robot_color, robot_pos, 10, 0)

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

def init(GS):
    # initialize leap motion
    GS.controller = Leap.Controller()

    # initialize pygame
    pygame.init()

    # setup the screen
    scr_size = (WIDTH, HEIGHT)  # first is width, second height
    GS.screen = pygame.display.set_mode(scr_size)
    pygame.display.set_caption("DDR")

    # load the background
    # solid colors
    GS.background = pygame.Surface(scr_size)
    GS.background = GS.background.convert()
    GS.background.fill((255, 255, 255)) # RGB colors

    # draw background and update display
    GS.screen.blit(GS.background, (0, 0))
    pygame.display.flip() 

    pygame.mouse.set_visible(True)

    random.seed()

def connect_bluetooth():
    return Bluetooth('00:06:66:00:A6:9B')

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

stop = threading.Event()

def game_over_check(bluetooth):
    bluetooth.s.setblocking(False)
    accum_messages = ""
    return
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

MAX_DIST = 3000

class State(object):
    def quit(self):
        sys.exit()

class Playing(State):
    def __call__(self):
      state = None
      for event in pygame.event.get():
        if event.type == QUIT:
          self.quit()
        elif event.type == KEYDOWN:
          if event.unicode.lower() == 'q':
            self.quit()
          elif event.unicode.lower() == 'a':
            GS.bluetooth.succeed()
          elif event.unicode.lower() == 'b':
            GS.bluetooth.fail()
          elif event.unicode.lower() == 'g':
            GS.bluetooth.game_over()

      if not pygame.mixer.get_busy():
        state = GameOver
        GS.win = False

      GS.screen.blit(GS.background, (0, 0))

      #put the hands off screen
      Hand.right.rect.center = Hand.left.rect.center = (-100, -100)

      frame = GS.controller.frame()
      for hand in frame.hands:
        conv = transform_coordinates(hand.palm_position)
        hand_o = (Hand.left if hand.is_left else Hand.right)
        hand_o.rect.center = conv
        dirt = hand.direction
        dirt.z = -1
        dirt = dirt.normalized
        hand_o.rotate(dirt.yaw)
     
      surface = GS.font.render("Drive speed: {}".format(GS.bluetooth.drive_speed), True, (0, 255, 0))
      GS.screen.blit(surface, (30, 30))
      surface = GS.font.render("Distance left (meters): {:.2f}".format((MAX_DIST - GS.song.accum_dist)/1000), True, (0, 255, 0))
      GS.screen.blit(surface, (30, 70))

      GS.robot_progress.progress(GS.song.accum_dist)
      GS.time_progress.progress((pygame.time.get_ticks() - GS.song_start)/ 1000.0)
      GS.all_sprites.update()
      GS.all_notes.update()
      GS.time = pygame.time.get_ticks()
      GS.song.update()
      GS.all_notes.draw(GS.screen)
      GS.all_sprites.draw(GS.screen)
      collided = pygame.sprite.groupcollide(GS.all_notes, GS.all_hands, False, False)
      for note in collided:
          if note.can_hit:
              global start
              start = time.time()
              note.kill()
              GS.song.good_note()

      if GS.song.accum_dist > MAX_DIST or GS.song.accum_dist < -(MAX_DIST/20):
        state = GameOver
        GS.win = (GS.song.accum_dist > MAX_DIST)

      pygame.display.flip()
      return state

class Init(State):
    def __init__(self):
        super(Init, self).__init__()
        self.index = 0
        self.songs = self.load_song_names()

    def load_song_names(self):
        songs = os.listdir('songs')
        songs = [x for x in songs if not x[0] == '.']
        l = []
        for song in songs:
            with open(os.path.join('songs', song, 'config.json')) as f:
                j = json.load(f)
                j['name'] = song
                l.append(j)
        return l

    def __call__(self):
        state = None
        GS.screen.fill((255, 255, 255))

        for event in pygame.event.get( ):
            if event.type == QUIT:
                sys.exit( )
            elif event.type == KEYDOWN:
                if event.unicode.lower() == ' ':
                    GS.filename = self.songs[self.index]
                    return PickDifficulty
                elif event.key == pygame.K_UP:
                    self.index -= 1
                elif event.key == pygame.K_DOWN:
                    self.index += 1
                elif event.unicode.lower() == 'q':
                    quit()

        surface = GS.font.render("spacebar to select song, up and down arrow to scroll", True, (0, 255, 0))
        GS.screen.blit(surface, (30, 30))
        top = 60
        self.index = min(self.index, len(self.songs) - 1)
        self.index = max(self.index, 0)
        for i, song in enumerate(self.songs):
            s = song['title']
            if i == self.index:
                s = '>>' + s + '<<'
            surface = GS.font.render(s, True, (0, 255, 0))
            GS.screen.blit(surface, (45, top))
            top += 30
        pygame.display.flip()

class PickDifficulty(State):
    def __init__(self):
        super(PickDifficulty, self).__init__()
        self.index = 0
        self.scoring_methods = SCORING_METHODS.items()

    def __call__(self):
        GS.screen.fill((255, 255, 255))

        for event in pygame.event.get( ):
            if event.type == QUIT:
                self.quit()
            elif event.type == KEYDOWN:
                if event.unicode.lower() == ' ':
                    GS.scoring_method = self.scoring_methods[self.index][1]
                    return Loading
                elif event.key == pygame.K_UP:
                    self.index -= 1
                elif event.key == pygame.K_DOWN:
                    self.index += 1
                elif event.unicode.lower() == 'q':
                    quit()

        surface = GS.font.render("spacebar to select method, up and down arrow to scroll", True, (0, 255, 0))
        GS.screen.blit(surface, (30, 30))
        top = 60
        index = min(self.index, len(self.scoring_methods) - 1)
        index = max(self.index, 0)
        for i, meth in enumerate(self.scoring_methods):
            s = meth[0]
            if i == self.index:
                s = '>>' + s + '<<'
            surface = GS.font.render(s, True, (0, 255, 0))
            GS.screen.blit(surface, (45, top))
            top += 30
        pygame.display.flip()

class Loading(State):
    def __call__(self):
        GS.screen.fill((255, 255, 255))

        surface = GS.font.render("loading...", True, (0, 255, 0))
        GS.screen.blit(surface, (30, 30))
        pygame.display.flip()

        GS.bluetooth = connect_bluetooth()
        game_over_t = threading.Thread(target=lambda: game_over_check(GS.bluetooth))
        game_over_t.daemon = True
        game_over_t.start()
        GS.all_sprites, GS.all_hands, GS.all_notes, GS.song = init_models(GS.filename, GS.scoring_method, GS.bluetooth)
        rect = pygame.Rect(0, 0, 400, 50)
        rect.right = WIDTH - 10
        rect.top = 10
        GS.robot_progress = ProgressBar("Robot Progress", MAX_DIST, rect)
        rect = pygame.Rect(0, 0, 400, 50)
        rect.right = WIDTH - 10
        rect.top = 10 + 50
        GS.time_progress = ProgressBar("Song Progress", GS.song.sound.get_length(), rect)
        GS.all_sprites.add(GS.robot_progress)
        GS.all_sprites.add(GS.time_progress)

        return WaitingForHands

class WaitingForHands(State):
    def __call__(self):
        font = pygame.font.Font(None, 32)

        frame = GS.controller.frame()
        if not frame.hands:
            GS.screen.fill((255, 255, 255))
            surface = GS.font.render("Please place your hands in the leap motion field of view", True, (0, 255, 0))
            GS.screen.blit(surface, (30, 30))
            pygame.display.flip()
        else:
            GS.song.sound.play()
            GS.song_start = pygame.time.get_ticks()
            GS.song.init(pygame.time.get_ticks())
            return Playing

class GameOver(State):
    def __call__(self):
        GS.screen.fill((255, 255, 255))
        GS.song.sound.stop()

        surface = GS.font.render("Game Over!", True, (0, 255, 0))
        textpos = surface.get_rect()
        textpos.centerx = GS.background.get_rect().centerx
        textpos.centery = 30
        GS.screen.blit(surface, textpos)
        surface = GS.font.render("You {}".format("win!" if GS.win else "lose!"), True, (0, 255, 0))
        textpos = surface.get_rect()
        textpos.centerx = GS.background.get_rect().centerx
        textpos.centery = 100
        GS.screen.blit(surface, textpos)
        surface = GS.font.render("Spacebar to play again, q to quit", True, (0, 255, 0))
        textpos = surface.get_rect()
        textpos.centerx = GS.background.get_rect().centerx
        textpos.centery = 150
        GS.screen.blit(surface, textpos)
        pygame.display.flip()

        for event in pygame.event.get( ):
            if event.type == QUIT:
                self.quit()
            elif event.type == KEYDOWN:
                if event.unicode.lower() == ' ':
                    return Init
                elif event.unicode.lower() == 'q':
                    self.quit()

def main():
    init(GS)
    GS.song_start = 0
    GS.index = 0
    GS.win = False
    GS.font = pygame.font.Font(None, 32)
    state = Init

    while True:
        if stop.is_set():
            break
        state_inst = state()
        state = state_inst() or state


if __name__ == "__main__":
    main()
