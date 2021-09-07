import serial
import time
import threading
from myUtil import serialBaud, serialPort
from myUtil import MHz, kHz, minUkw, maxUkw, minKw, maxKw, minMw, maxMw, minLw, maxLw
from myUtil import minCap, maxCap
from myUtil import capToLw, capToMw, capToKw, capToUkw
from myLog import log, elog, slog
import myRadios
import myNoise
import statistics

currentDict = None
def getDict():
    return currentDict

currentFreq = None
def getFreq():
    return currentFreq

currentTuneFactor = None
def getTuneFactor():
    return currentTuneFactor

currentRadio = None

serialObj = None
lastCaps = []

def parseSerial(line):
    currentDict = {}
    try:
        line = line.decode("utf-8").strip()
        segs = line.split("\t")
    except UnicodeDecodeError as e:
        # this typically happens when connection is started in the middle of a message
        elog(e.reason)
        return currentDict
    
    try: 
        for seg in segs:
            [key, val] = seg.split(":")
            key = key.strip()
            val = val.strip()
            if key == "Cap":
                val = float(val)
            else:
                val = int(val)
            currentDict[key] = val
    except ValueError as e:
        elog("ValueError: {}".format(line))
    
    return currentDict

def capToFreq(currentDict):
    cap = currentDict["Cap"]
    if currentDict["LW"] == 1:
        return capToLw(cap)
    elif currentDict["MW"] == 1:
        return capToMw(cap)
    elif currentDict["KW"] == 1:
        return capToKw(cap)
    elif currentDict["UKW"] == 1:
        return capToUkw(cap)
    return 0

def thread_run():
    global currentDict
    global lastCaps
    global currentFreq
    global currentRadio
    global currentTuneFactor
    global serialObj

    modeDebounce = 0

    while True:
        if not serialObj or not serialObj.is_open:
            serialObj = serial.Serial()
            serialObj.port = serialPort
            serialObj.baudrate = serialBaud
            try: 
                serialObj.open()
                slog("Connected to Arduino on {}".format(serialPort))
            except serial.SerialException as e: 
                elog(e)
                time.sleep(2)
        else:
            try:
                line = serialObj.readline()
                currentDict = parseSerial(line)
                # log(currentDict)
            except serial.SerialException as e: 
                serialObj.close() # close so that Linux can use the same /dev/ttyUSB*
                elog(e)
                time.sleep(2)

            if "On" in currentDict and "LW" in currentDict and "MW" in currentDict and "KW" in currentDict and "UKW" in currentDict and "Vol" in currentDict and "Tre" in currentDict and "Cap" in currentDict:
                # if valid data

                # check how many band selectors are active
                mode = currentDict["LW"] + currentDict["MW"] + currentDict["KW"] + currentDict["UKW"]
                if mode == 1:
                    # normal mode
                    maxTuneFactor = 0

                    # iron out spikes in cap values
                    lastCaps = lastCaps[0:4]
                    lastCaps.insert(0, currentDict["Cap"])
                    currentDict["Cap"] = statistics.median(lastCaps)

                    currentFreq = capToFreq(currentDict)
                    isOn = currentDict["On"] == 1
                    vol = currentDict["Vol"] * 100 / 255 if isOn else 0
                    staticVol = vol
                    for radio in myRadios.getRadios():
                        tuneFactor = radio.tuneFactor(currentFreq)
                        maxTuneFactor = max(maxTuneFactor, tuneFactor)
                        # cross-over noise works as follows:
                        if tuneFactor == 0:
                            # full noise. no signal
                            radio.off()
                            staticVol = staticVol
                        else:
                            currentRadio = radio
                            if tuneFactor <= 0.5:
                                # full noise with a little bit of signal
                                myVol = tuneFactor * 2 * vol
                                staticVol = staticVol
                            elif tuneFactor < 1:
                                # full signal with a little bit of noise
                                myVol = vol
                                staticVol = (2 * (1 - tuneFactor)) * staticVol
                            else:
                                # full signal. no noise
                                myVol = vol
                                staticVol = 0  
                            radio.setVolume(myVol)

                    myNoise.setVolume(staticVol)
                    currentTuneFactor = maxTuneFactor
                elif mode == 0:
                    # if no channel is selected

                    # @TODO: maybe future use to calibrate the tuner or something
                    myNoise.setVolume(0)
                    if currentRadio != None: 
                        currentRadio.off()
                    currentFreq = None
                    currentRadio = None
                    currentTuneFactor = None
                if mode == 2:
                    # if: two buttons are pressed
                    modeDebounce += 1
                    if modeDebounce == 4 and currentRadio:
                        currentRadio.next()
                else:
                    modeDebounce = 0

thread = threading.Thread(target=thread_run, daemon=True)
thread.name = "serial"
thread.start()
