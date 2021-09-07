#!/usr/bin/python3

# @see https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc-module.html

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("confFile", nargs="?", help="The yaml file where your stations are configured.", default="./default.yaml")
parser.add_argument("--no-gui", help="Hide the fancy colorful GUI", action="store_true", default=None)
parser.add_argument("--gui-fps", help="How often to refresh the GUI per second", type=int, default=1)
args = parser.parse_args()

import sys
import os
import subprocess
import shutil
import random
import time
import traceback
import threading
from myLog import log, elog, slog


def thread_exception_handler(args):
    theLog = str(args.exc_type)
    if args.exc_value:
        theLog += ": " + str(args.exc_value)
    elog(theLog)
    if args.thread and args.thread.is_alive():
        elog("Thread {} crashed.".format(args.thread.name))

threading.excepthook = thread_exception_handler

import myNoise
import vlc
import yaml
from myRadios import RadioStation
import myDrawer
import myRadios
from myUtil import MHz, kHz
import myLog
import mySerial
import myLed

random.seed()
myDrawer.start(noGui = args.no_gui, guiRefresh = args.gui_fps)

# #####
#
# Setup
#
# #####

with open(args.confFile, 'r') as stream:
    new_cwd = os.path.dirname(args.confFile)
    if new_cwd != '':
        # change base dir, so that files for VLC can be referenced relative to the configuration file
        os.chdir(new_cwd)
        myLog.log(f"Changed cwd to {os.getcwd()}")
    try:
        config = yaml.safe_load(stream)
        if not "radios" in config:
            raise ValueError("Expected configuration to have a key \"radios\" as root element.")
        if not isinstance(config["radios"], list):
            raise ValueError("Expected \"radios\" to be a list, but it is not.")

        radios = []
        for idx in range(len(config["radios"])):
            try:
                radioConfig = config["radios"][idx]
                if not isinstance(radioConfig, dict):
                    raise ValueError("Expected radio at index {} to be a dict".format(idx))
                if not "name" in radioConfig:
                    raise ValueError("Expected radio at index {} to have a name".format(idx))
                if not isinstance(radioConfig["name"], str):
                    raise ValueError("Expected name at index {} to be a string".format(idx))
                name = radioConfig["name"].strip()
                if not "uri" in radioConfig:
                    raise ValueError("Expected radio at index {} to have an uri".format(idx))
                if not isinstance(radioConfig["uri"], str):
                    raise ValueError("Expected uri at index {} to be a string".format(idx))
                uri = radioConfig["uri"].strip()
                if not "frequency" in radioConfig:
                    raise ValueError("Expected radio at index {} to have a frequency".format(idx))
                if isinstance(radioConfig["frequency"], str):
                    frequency = radioConfig["frequency"].strip()
                    if frequency.endswith("MHz"):
                        frequency = float(frequency[:-3]) * MHz
                    elif frequency.endswith("kHz"):
                        frequency = float(frequency[:-3]) * kHz
                    else:
                        raise ValueError("Expected frequency at index {} to have a form like \"102.4MHz\"".format(idx))
                elif isinstance(radioConfig["frequency"], float) or isinstance(radioConfig["frequency"], int):
                    frequency = float(radioConfig["frequency"])
                else:
                    raise ValueError("Expected frequency at index {} to have a valid format".format(idx))
                if "shuffle" in radioConfig:
                    if not isinstance(radioConfig["shuffle"], bool):
                        raise ValueError("Expected shuffle at index {} to be boolean".format(idx))
                    shuffle = radioConfig["shuffle"]
                else:
                    shuffle = False
                if "stop" in radioConfig:
                    if not isinstance(radioConfig["stop"], bool):
                        raise ValueError("Expected stop at index {} to be boolean".format(idx))
                    stop = radioConfig["stop"]
                else:
                    stop = False
                if "pause" in radioConfig:
                    if not isinstance(radioConfig["pause"], bool):
                        raise ValueError("Expected pause at index {} to be boolean".format(idx))
                    pause = radioConfig["pause"]
                else:
                    pause = False
                if "equalizer" in radioConfig:
                    if not isinstance(radioConfig["equalizer"], str):
                        raise ValueError("Expected equalizer at index {} to be a string".format(idx))
                    equalizerName = radioConfig["equalizer"]
                else:
                    equalizerName = None

                radio = RadioStation(name, uri, frequency, stop=stop, pause=pause, shuffle=shuffle, equalizerName=equalizerName)
                radios.append(radio)
            except ValueError as e:
                elog ("Error with radio at index {}: {}".format(idx, e))
        
        myRadios.setRadios(radios)

    except yaml.YAMLError as e:
        elog(e)
    except ValueError as e:
        elog ("Error parsing {}: {}".format(args.confFile, e))

# ####
#
# Work
#
# ####

# everything runs in sub-threads. So, go take a break, drink coffee or do whatever parents do when their kids are occupied.
while True:
    time.sleep(999)

