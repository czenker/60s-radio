import shutil
import os
from stringcolor import * 
import time
import threading
import vlc
import math
import myRadios
import myLog
import mySerial
from myUtil import MHz, kHz
import psutil
import gpiozero
from myLog import log, elog, slog

defaultScreenSize = (0, 0)

colors = {
  "grey": lambda s: str(cs(s, "grey")),
  "green": lambda s: str(cs(s, "green")),
  "yellow": lambda s: str(cs(s, "yellow")),
  "red": lambda s: str(cs(s, "red")),
  "yellow_dim": lambda s: str(cs(s, "olive")),
  "red_badge": lambda s: str(cs(s, "white", "red")),
  "green_badge": lambda s: str(cs(s, "white", "green")),
}

data = []
lastScreen = None
currentLine = None

# #######
#
# Library
#
# #######

def clear():
  global data
  global currentLine
  data = []
  currentLine = None

def writeLine(line, color = None):
  if color:
    line = color(line)
  data.append(line)

def write(string, color = None, space = True):
  global currentLine

  if color:
    string = color(string)
  if space:
    string += " "

  currentLine = (currentLine or "") + string

def endLine():
  global currentLine
  data.append(currentLine or "")
  currentLine = None

def flush():
  global data
  global lastScreen
  global currentLine

  if currentLine != None:
    endLine()
  
  screen = "\n".join(data)
  clear()
  if screen != lastScreen:
    _ = os.system('clear')
    print(screen)
    lastScreen = screen

def hasTerminal():
  return getScreenSize() != defaultScreenSize

def getScreenSize():
  return shutil.get_terminal_size(fallback=defaultScreenSize)


def pad(string, length):
    string = str(string)
    if len(string) > length:
        string = "{}…".format(string[0:length-1])
    return string.ljust(length)

def formatFreq(freq):
    if freq < 2000 * kHz:
        return "{:>5.0f}kHz".format(freq / kHz)
    elif freq < 10 * MHz:
        return "{:>5.2f}MHz".format(freq / MHz)
    else:
        return "{:>5.1f}MHz".format(freq / MHz)

def formatTime(msec):
    sec = round(msec / 1000)
    hours = math.floor(sec / 60 / 60)
    mins = math.floor(sec / 60 - hours * 60)
    secs = math.floor(sec - 60 * mins - 60*60*hours)

    if hours > 0:
        return "{hours:>02d}:{mins:>02d}:{secs:>02d}".format(hours=hours, mins=mins, secs=secs)
    else:
        return "{mins:>02d}:{secs:>02d}".format(mins=mins, secs=secs)

def draw_thread(noGui = None, guiRefresh = 1):
    if noGui == None:
        noGui = not hasTerminal()

    lastNetSentBytes = None
    lastNetRecvBytes = None
    lastNetTime = None

    while True:
        if not noGui:
            clear()
            terminalCols, terminalLines = getScreenSize()

            iconWidth = 1
            nameWidth = 20
            freqWidth = 8
            bandWidth = 3
            descWidth = terminalCols - iconWidth - nameWidth - freqWidth - bandWidth - 4*2
            if descWidth < 15:
                descWidth = 0
                nameWidth = terminalCols - iconWidth - freqWidth - bandWidth - 3*2
            if nameWidth < 15:
                nameWidth += bandWidth + 2
                bandWidth = 0

            radios = myRadios.getRadios()
            for idx in range(len(radios)):
                
                radio = radios[idx]

                color = None
                tuneFactor = radio.tuneFactor(mySerial.getFreq()) if mySerial.getFreq() != None else None
                if tuneFactor and tuneFactor == 1:
                    color = colors["green"]
                elif tuneFactor and tuneFactor > 0:
                    color = colors["yellow"]
                media = radio.getMedia()
                if descWidth > 0 and media:
                    if media.get_meta(vlc.Meta.Artist) != None:
                        description = "{artist} – {track}".format(
                            artist = pad(radio.getPlayer().get_media().get_meta(vlc.Meta.Artist), math.floor((descWidth - 3) / 2)),
                            track = pad(radio.getPlayer().get_media().get_meta(vlc.Meta.Title), math.ceil((descWidth - 3) / 2))
                        )
                    else:
                        description = pad(media.get_meta(vlc.Meta.Title), descWidth)
                else:
                    description = pad("", descWidth)

                if radio.getPlayer():
                    if radio.getPlayer().get_state() == vlc.State.Buffering:
                        icon = "◐"
                    elif radio.getPlayer().get_state() == vlc.State.Ended:
                        icon = "✘"
                    elif radio.getPlayer().get_state() == vlc.State.Error:
                        icon = "🕱"
                    elif radio.getPlayer().get_state() == vlc.State.NothingSpecial:
                        icon = "◌"
                    elif radio.getPlayer().get_state() == vlc.State.Opening:
                        icon = "🖿"
                    elif radio.getPlayer().get_state() == vlc.State.Paused:
                        icon = "⏸"
                    elif radio.getPlayer().get_state() == vlc.State.Playing:
                        icon = "▶"
                    elif radio.getPlayer().get_state() == vlc.State.Stopped:
                        icon = "⏹"
                    else:
                        icon = "?"
                else:
                    icon = "?"
                
                line = ""
                if iconWidth > 0:
                    line += icon + "  "
                if nameWidth > 0:
                    line += pad(radio.name, nameWidth) + "  "
                if descWidth > 0:
                    line += description + "  "
                if bandWidth > 0:
                    line += "{:>3s}".format(radio.band) + "  "
                if freqWidth > 0:
                    line += formatFreq(radio.freq)

                writeLine(line, color)

            endLine()

            # ##############
            #
            # current radio
            # 
            # ##############

            if mySerial.currentRadio:
                radio = mySerial.currentRadio
                player = radio.getPlayer()
                media = radio.getMedia()
                writeLine(radio.name)
                writeLine("{}/{}".format(formatTime(player.get_time()), formatTime(player.get_length())))





            # #####
            #
            # panel
            #
            # #####

            currentDict = mySerial.getDict()
            if currentDict != None and "On" in currentDict:
                if currentDict["On"] == 1:
                    write(" ON  ", colors["green_badge"])
                else:
                    write(" OFF ", colors["red_badge"])
            else:
                write(" ??? ", colors["yellow_dim"])
            
            write(" ")
            for band in ["LW", "MW", "KW", "UKW"]:
                if currentDict != None and band in currentDict:
                    if currentDict[band] == 1:
                        write(band, colors["green"])
                    else:
                        write(band, colors["grey"])
                else:
                    write(band, colors["yellow_dim"])

            write(" ")
            
            if currentDict != None and "Vol" in currentDict:
                vol = round(currentDict["Vol"] * 100 / 255)
                if vol > 0:
                    icon = "🔈"
                    icon = "🔉" if vol > 50 else icon
                    icon = "🔊" if vol > 75 else icon
                    write("{icon} {:>3}%".format(vol, icon=icon))
                else:
                    write("🔇   0%", colors["red"])
            else:
                write("🔇  ???%", colors["yellow_dim"])

            write(" ")

            if mySerial.getFreq():
                write("📶 {:>8s}".format(formatFreq(mySerial.getFreq())))
            else:
                write("📶 ??????Hz", colors["yellow_dim"])

            write(" ")

            try:
                temp = gpiozero.CPUTemperature().temperature
            except gpiozero.exc.BadPinFactory:
                temp = None
            if temp:
                color = None
                if temp >= 70:
                    color = colors["red"]
                elif temp >= 80:
                    color = colors["red_badge"]
                write("🌡 {:>3d}°C".format(round(temp)), color)
            else:
                write("🌡 ???°C", colors["yellow_dim"])

            write(" ")

            try:
                load, _, _ = os.getloadavg()
            except OSError:
                load = None
            if load:
                color = None
                if load >= 3:
                    color = colors["red"]
                elif load >= 4:
                    color = colors["red_badge"]
                write("🏋 {:>5.2f}".format(load), color)
            else:
                write("🏋 ?????", colors["yellow_dim"])

            write(" ")

            mem = psutil.virtual_memory()
            mem_usage = round((mem.total - mem.available) / mem.total * 100)

            if mem_usage:
                color = None
                if load >= 80:
                    color = colors["red"]
                elif load >= 95:
                    color = colors["red_badge"]
                write("🧠 {:>3d}%".format(mem_usage), color)
            else:
                write("🧠 ???%", colors["yellow_dim"])
            
            write(" ")

            net = psutil.net_io_counters()
            if lastNetSentBytes != None and lastNetRecvBytes != None and lastNetTime != None:
                net_sent = net.bytes_sent - lastNetSentBytes
                net_recv = net.bytes_recv - lastNetRecvBytes
                time_delta = time.time() - lastNetTime

                net_sent_pers = net_sent / time_delta
                net_recv_pers = net_recv / time_delta
            else:
                net_sent_pers = None
                net_recv_pers = None
            
            lastNetSentBytes = net.bytes_sent
            lastNetRecvBytes = net.bytes_recv
            lastNetTime = time.time()

            if net_recv_pers != None:
                write("▼ {:>5.1f}kB/s".format(net_recv_pers / 1024))
            else:
                write("▼ ??????kB/s", colors["yellow_dim"])

            if net_sent_pers != None:
                write("▲ {:>5.1f}kB/s".format(net_sent_pers / 1024))
            else:
                write("▲ ??????kB/s", colors["yellow_dim"])

            endLine()
            endLine()

            logHeight = max(1, terminalLines - len(radios) - 4)
            logsToDisplay = min(logHeight, len(myLog.logs))

            if logsToDisplay > 0:
                theLogs = myLog.logs[0:logsToDisplay]
                theLogs.reverse()

                for theLog in theLogs:
                    color = colors["grey"]
                    if theLog["severity"] == "ERROR":
                        color = colors["red"]
                    elif theLog["severity"] == "SUCCESS":
                        color = colors["green"]
                    elif theLog["severity"] == "WARNING":
                        color = colors["yellow"]

                    writeLine(pad(theLog["msg"], terminalCols), color)

            flush()
        time.sleep(1 / guiRefresh)

def start(*args, **kwargs):
    thread = threading.Thread(target=draw_thread, args=args, kwargs=kwargs, daemon=True)
    thread.name = "draw"
    thread.start()
