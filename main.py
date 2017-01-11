import pyb
import utime
import urandom
import math

import micropython
micropython.alloc_emergency_exception_buf(100)

STRIP_WIDTH = 40
COLS = STRIP_WIDTH * 2
ROWS = 100

frame = bytearray(4*COLS*ROWS)

debug = False

def set_pixel(x, y, r, g, b):
  if x >= COLS or y >= ROWS:
    return
  if x % 2 == 1:
    x = STRIP_WIDTH + x // 2
  else:
    x = x // 2
  idx = 4 * (y * COLS + x)
  frame[idx] = 0b11110011
  frame[idx + 1] = b
  frame[idx + 2] = g
  frame[idx + 3] = r

for x in range(COLS):
  for y in range(ROWS):
    set_pixel(x, y, 0, 0, 0)

grid = False
if grid:
  for x in range(COLS):
    set_pixel(x, 0, 255, 0, 0)
    set_pixel(x, 10, 0, 255, 0)
    set_pixel(x, 20, 0, 0, 255)
    set_pixel(x, 31, 255, 0, 0)
    set_pixel(x, 41, 0, 255, 0)
    set_pixel(x, 51, 0, 0, 255)


  for y in range(ROWS):
    set_pixel(0, y, 255, 0, 0)
    set_pixel(10, y, 0, 255, 0)
    set_pixel(20, y, 0, 0, 255)
    set_pixel(30, y, 255, 0, 0)
    set_pixel(40, y, 0, 255, 0)
    set_pixel(50, y, 0, 0, 255)
    set_pixel(60, y, 255, 0, 0)
    set_pixel(70, y, 0, 255, 0)

f = open('globe.ppm')
gx = 0
gy = 0
while True:
  try:
    r = int(f.readline().strip())
    g = int(f.readline().strip())
    b = int(f.readline().strip())
    if r == max(r, g, b):
      r = min(255, int(1.5*r))
    if g == max(r, g, b):
      g = min(255, int(1.5*g))
    if b == max(r, g, b):
      b = min(255, int(1.5*b))
    set_pixel(gy, gx, r, g, b)
    gx += 1
    if gx == ROWS:
      gx = 0
      gy += 1
  except:
    break
f = None


# 37 leds, yellow/blue
strip_top = pyb.SPI(1, pyb.SPI.MASTER, baudrate=2000000, phase=1, polarity=1, bits=8, firstbit=pyb.SPI.MSB, crc=None)
# 36 leds, black/red
strip_bottom = pyb.SPI(2, pyb.SPI.MASTER, baudrate=2000000, phase=1, polarity=1, bits=8, firstbit=pyb.SPI.MSB, crc=None)

def update(s, r):
  idx = (r * STRIP_WIDTH) * 4
  s.send(bytes([0]*4) + frame[idx:idx + STRIP_WIDTH * 4] + bytes([255]*4))

pin_hall_top = pyb.Pin.board.X12
pin_hall_bottom = pyb.Pin.board.Y12

start_top = pyb.micros()
start_bottom = pyb.micros()

cycle_time_top = 500000
cycle_time_bottom = 500000

advance_top = False
advance_bottom = False

def on_top_tick(t):
  global advance_top
  advance_top = True

def on_bottom_tick(t):
  global advance_bottom
  advance_bottom = True

def on_sync(t):
  timer_top.freq(ROWS * 1000000 // cycle_time_top)
  timer_bottom.freq(ROWS * 1000000 // cycle_time_bottom)

timer_top = pyb.Timer(1, freq=50, callback=on_top_tick)
timer_bottom = pyb.Timer(2, freq=50, callback=on_bottom_tick)
timer_sync = pyb.Timer(3, freq=2, callback=on_sync)

start_top = pyb.micros()
start_bottom = pyb.micros()

def on_hall_top(line):
  global start_top, cycle_time_top, advance_top, y_top
  #if not pin_hall_top.value():
    #print('top')
  cycle_time_top = (pyb.elapsed_micros(start_top) * 50 + cycle_time_top * 50) // 100
  start_top = pyb.micros()
  y_top = 0

def on_hall_bottom(line):
  global start_bottom, cycle_time_bottom, advance_bottom, y_bottom
  #if not pin_hall_bottom.value():
    #print('bottom')
  cycle_time_bottom = (pyb.elapsed_micros(start_bottom) * 50 + cycle_time_bottom * 50) // 100
  start_bottom = pyb.micros()
  y_bottom = 1

hall_top_int = pyb.ExtInt(pin_hall_top, pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_DOWN, on_hall_top)
hall_bottom_int = pyb.ExtInt(pin_hall_bottom, pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_DOWN, on_hall_bottom)

y_top = 0
y_bottom = ROWS // 2

running_time = pyb.millis()

class Dot:
  def __init__(self, r, g, b):
    self.x = urandom.randrange(COLS)
    self.y = urandom.randrange(ROWS)
    self.d = math.pi * urandom.randrange(0, 200) / 100
    self.r = r
    self.g = g
    self.b = b

  def draw(self):
    try:
      set_pixel(int(self.x), int(self.y), self.r, self.g, self.b)
    except:
      print(self.x, self.y)

  def move(self):
    set_pixel(int(self.x), int(self.y), 0, 0, 0)
    self.x += math.cos(self.d)
    if self.x >= COLS:
      self.x -= COLS
    if self.x < 0:
      self.x += COLS
    self.y += math.sin(self.d)
    if self.y >= ROWS:
      self.y -= ROWS
    if self.y < 0:
      self.y += ROWS
    set_pixel(int(self.x), int(self.y), self.r, self.g, self.b)
    #self.x = (self.x + 1) % COLS
    #self.y = (self.y + 1) % ROWS

dots = [Dot(255,0,0), Dot(0, 255, 0), Dot(0, 0, 255), Dot(255, 255, 0), Dot(0, 255, 255), Dot(255, 0, 255)]
#for d in dots:
#  d.draw()

#print("blanking...")
strip_top.send(bytes([0]*4 + [0b11100001,0,0,0]*STRIP_WIDTH + [255]*4))
strip_bottom.send(bytes([0]*4 + [0b11100001,0,0,0]*STRIP_WIDTH + [255]*4))

while True:
  if advance_top:
    y_top = (y_top + 2) % (ROWS * 2)
    #print('top', y_top)
    update(strip_top, y_top)
    advance_top = False
  if advance_bottom:
    y_bottom = (y_bottom + 2) % (ROWS * 2)
    #print('bottom', y_bottom)
    update(strip_bottom, y_bottom)
    advance_bottom = False
  if pyb.elapsed_millis(running_time) > 100:
    running_time = pyb.millis()
    #for d in dots:
    #  d.move()
