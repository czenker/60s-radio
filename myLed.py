import threading
import gpiozero
import myUtil
import time
import random
import mySerial
from myLog import log, elog, slog

HIGH = 1 # we can't use anything lower or a clear flickering will show. We can't use PiGPIO (which supports HW PWM), because it will interfere with the Amp.
LOW = 0.5
OFF = 0

def getValue():
  myDict = mySerial.getDict()
  if not myDict or not "On" in myDict or myDict["On"] != 1:
    return OFF
  
  tuneFactor = mySerial.getTuneFactor()
  
  if tuneFactor == None:
    return LOW
  elif tuneFactor > 0.99:
    # radio is perfectly tuned
    return HIGH
  elif tuneFactor < 0.01:
    # radio is totally out of tune
    return LOW
  else:
    # radio is badly tuned: make the LED flicker
    oddity = tuneFactor*0.65 + 0.1
    if random.random() <= oddity:
      return HIGH
    else:
      return LOW

lastValues = []

def thread_run():
  global lastValues
  while True:
    value = getValue()

    # keep track of last values to give the feel that the light is actually a coil-based light.
    lastValues = lastValues[0:3]
    lastValues.insert(0, value)
    value = sum(lastValues) / len(lastValues)

    value *= value # adapt for non-linear dim of LEDs
    led.value = value
    time.sleep(1 / 25)

try:
  led = gpiozero.PWMLED(myUtil.ledPin)

  thread = threading.Thread(target=thread_run, daemon=True)
  thread.name = "led"
  thread.start()
except gpiozero.exc.BadPinFactory as e:
  elog("LED GPIO could not be initialized. You are probably not running on a RasPi, so we disable the LED feature.")



