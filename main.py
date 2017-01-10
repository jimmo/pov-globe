import pyb
import utime

import micropython
micropython.alloc_emergency_exception_buf(100)

COLS = 36+37
ROWS = 60

frame = [0b1110011, 0, 0, 0]*(COLS*ROWS)

# 37 leds, yellow/blue
strip_top = pyb.SPI(2, pyb.SPI.MASTER, baudrate=1000000, crc=None)
# 36 leds, black/red
#strip_bottom = pyb.SPI(2, pyb.SPI.MASTER, baudrate=1000000, crc=None)

def update(r, g, b):
  strip_top.send(bytes([0]*4 + [0b11100111, b, g, r]*37 + [255]*4))
  #strip_bottom.send(bytes([0]*4 + [255, b, g, r]*36 + [255]*4))

def red():
  update(255, 0, 0)

def green():
  update(0, 255, 0)

def blue():
  update(0, 0, 255)

def orange():
  update(255, 128, 128)

pin_hall_top = pyb.Pin.board.X12
pin_hall_bottom = pyb.Pin.board.Y12

start_top = pyb.micros()
start_bottom = pyb.micros()

cycle_time_top = 500000
cycle_time_bottom = 500000

toggle_top = False
toggle_bottom = False

advance_top = False
advance_bottom = False

def on_top_tick(t):
  global toggle_top
  pyb.LED(2).toggle()
  toggle_top = not toggle_top
  if toggle_top:
    red()
  else:
    green()
  advance_top = True

def on_bottom_tick(t):
  global toggle_bottom
  pyb.LED(3).toggle()
  toggle_top = not toggle_bottom
  if toggle_bottom:
    blue()
  else:
    orange()
  advance_bottom = True

def on_sync(t):
  timer_top.freq(ROWS * 1000000 // cycle_time_top)
  timer_bottom.freq(ROWS * 1000000 // cycle_time_bottom)

timer_top = pyb.Timer(1, freq=5, callback=on_top_tick)
timer_bottom = pyb.Timer(2, freq=5, callback=on_bottom_tick)
timer_sync = pyb.Timer(3, freq=10, callback=on_sync)

x = [0,0]

start_top = pyb.micros()
start_bottom = pyb.micros()

def on_hall_top(line):
  print('top')
  global start_top, cycle_time_top
  x[0] += 1
  if pin_hall_top.value():
    cycle_time_top = (pyb.elapsed_micros(start_top) * 20 + cycle_time_top * 80) // 100
    start_top = pyb.micros()

def on_hall_bottom(line):
  print('boittom')
  global start_bottom, cycle_time_bottom
  x[1] += 1
  if pin_hall_bottom.value():
    cycle_time_bottom = (pyb.elapsed_micros(start_bottom) * 20 + cycle_time_bottom * 80) // 100
    start_bottom = pyb.micros()

hall_top_int = pyb.ExtInt(pin_hall_top, pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_DOWN, on_hall_top)
hall_bottom_int = pyb.ExtInt(pin_hall_bottom, pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_DOWN, on_hall_bottom)

#while True:
#  timer_top.freq(ROWS * 1000000 / cycle_time_top)
#  timer_bottom.freq(ROWS * 1000000 / cycle_time_bottom)
#  utime.sleep(0.01)

y_top = 0
y_bottom = 0
while True:
  if advance_top:
    #spi.send(bytes([0]*4 + frame[y_top*4*
    advance_top = False
