import vlc
import random
import myUtil
from myUtil import MHz, kHz, minUkw, maxUkw, minKw, maxKw, minMw, maxMw, minLw, maxLw
from myLog import log, elog, slog, wlog
import time

# @see https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc-module.html

vlcInstance = vlc.Instance('--no-video', '--audio', '--audio-visual', 'none', '--random', '--audio-replay-gain-mode', 'track')
vlcInstance.log_unset() # potentially dangerous: suppressing errors

eqIndexByName = {}
for idx in range(vlc.libvlc_audio_equalizer_get_preset_count()):
    name = vlc.libvlc_audio_equalizer_get_preset_name(idx).decode("utf-8") 
    eqIndexByName[name] = idx

class RadioStation:
    def __detectBand(self, freq):
        ''' get the frequency band and the minimum / maximum frequency this
            radio can be heared without static noise
        '''
        if freq == 0:
            return 0, 0, "Static"
        if freq >= minUkw and freq <= maxUkw:
            return freq - 0.15   * MHz, freq + 0.15 * MHz, "UKW"
        elif freq >= minKw and freq <= maxKw:
            return freq - 0.015 * MHz, freq + 0.015 * MHz, "KW"
        elif freq >= minMw and freq <= maxMw:
            # "For Europe, Africa and Asia the MW band consists of 120 channels with centre frequencies from 531 to 1602 kHz spaced every 9 kHz"
            return freq - 5 * kHz, freq + 5 * kHz, "MW"
        elif freq >= minLw and freq <= maxLw:
            # "Long-wave carrier frequencies are exact multiples of 9 kHz"
            return freq - 2.25 * kHz, freq + 2.25 * kHz, "LW"
        else:
            raise ValueError("Frequency of {} is not within any known band. Got {}Hz".format(self.name, freq))
    def __getTracksFromPlaylist(self, playlistPath):
        ''' takes a path to something that might be a playlist and extracts all tracks

            if it is not a playlist, it will return a list of itself
        '''
        playlist = vlcInstance.media_list_new([playlistPath])
        medias = []

        playlist.lock()
        for i in range(playlist.count()):
            thisMedia = playlist.item_at_index(i)
            thisMedia.parse()
            subitems = thisMedia.subitems()
            if subitems:
                # if it is a playlist
                for sub in thisMedia.subitems():
                    medias.append(sub)
            else:
                # if it is a file of its own
                medias.append(thisMedia)
        playlist.unlock()

        return medias

    def __onResume(self):
        if self.lastPlayback:
            now = time.time()
            diff = now - self.lastPlayback
            if diff > 0.5 and self.shouldPause and self.getPlayer().is_seekable():
                maxPlayerTime = self.getPlayer().get_length()
                currentPlayerTime = self.getPlayer().get_time()
                if maxPlayerTime > 0 and currentPlayerTime + diff * 1000 <= maxPlayerTime:
                    # skip forward in the same song
                    self.getPlayer().set_time(round(currentPlayerTime + diff * 1000))
                else:
                    self.vlcMediaListPlayer.next()
                    if (self.shuffle or self.start_random) and diff > 1:
                        self.getPlayer().set_position(random.random())

    def __init__(self, name, playlistPath, freq = 0, stop = False, pause = False, shuffle = False, start_random = False, equalizerName = None):
        ''' Represent a radio station and how it is played

        Parameters
        ----------

        name: str
            The name of the station. Is displayed in the GUI only.
        
        playlistPath: str
            The thing that should be played. Basically everything that VLC understands.

            Could be a local file, a playlist or an url.
        
        freq: number
            At what frequency the radio station can be heard.

            It needs to be in any of the configured frequency bands.
            For Example "102_400_000" will have the station at 102.4MHz.
            You have to take care that no two stations are overlapping.

        stop: bool, optional
            If the playback should be stopped when the station is tuned out of.

            This is a recommended option when playing web streams.
            Has the advantage that bandwidth is saved when the stream is not played,
            but at the disadvantage that there might be a small gap when tuning into that station

            Another use-case is when you want that your file is played from the beginning when
            tuning into that station, but at the (unrealistic) price of having it played from
            start again when tuning away and in again.
        
            (default False)

        pause: bool, optional
            If the playback should be paused when the station is tuned out of.

            Lowers CPU when not playing, and – other than `stop` – allows instant continuation
            of playback. But it comes with the price that the station will still play the same song
            when you tune back in after 5 minutes.

            (default False)
       
        shuffle: bool
            Shuffles track order when using a playlist.

            (default False)
       
        start_random: bool
            Starts at a random position when using the playlist. 
            It is a lighter version of `shuffle` as it does not shuffle the track order, but still gives
            a random entry point into the playlist.

            (default False)
        '''
        self.name = name
        self.freq = freq
        self.shouldStop = stop
        self.shouldPause = pause
        self.shuffle = shuffle
        self.start_random = start_random
        self.lastPlayback = None
        [self.minFreq, self.maxFreq, self.band] = self.__detectBand(freq)
        self.vlcMediaListPlayer = vlcInstance.media_list_player_new()

        tracks = self.__getTracksFromPlaylist(playlistPath)

        if shuffle:
            random.shuffle(tracks)

        playlist = vlcInstance.media_list_new(tracks)

        self.vlcMediaListPlayer.set_media_list(playlist)
        self.getPlayer().set_role(vlc.MediaPlayerRole.Music)
        self.vlcMediaListPlayer.set_playback_mode(vlc.PlaybackMode.loop)
        self.setVolume(0)
        if equalizerName:
            if equalizerName in eqIndexByName:
                equalizerIdx = eqIndexByName[equalizerName]
                equalizer = vlc.libvlc_audio_equalizer_new_from_preset(equalizerIdx)
                self.getPlayer().set_equalizer(equalizer)
            else:
                wlog("Equalizer with name {} does not exist. Valid values:".format(equalizerName))
                wlog(", ".join(eqIndexByName.keys()))

        if start_random:
            self.vlcMediaListPlayer.play_item_at_index(random.randint(0, len(tracks)-1 ))

        if not stop:
            self.vlcMediaListPlayer.play()

        if shuffle or start_random:
            self.getPlayer().set_position(random.random())
    def getPlayer(self):
        return self.vlcMediaListPlayer.get_media_player()
    def getState(self):
        return self.vlcMediaListPlayer.get_state()
    def getMedia(self):
        player = self.getPlayer()
        if player:
            return player.get_media()
        else:
            return None
    def setVolume(self, volume):
        if volume > 0 and not self.vlcMediaListPlayer.is_playing():
            self.__onResume()
            self.vlcMediaListPlayer.play()
        self.getPlayer().audio_set_volume(int(volume))
    def next(self):
        self.vlcMediaListPlayer.next()
    def off(self):
        self.setVolume(0)
        if self.vlcMediaListPlayer.is_playing():
            self.lastPlayback = time.time()
            if self.shouldPause and self.getPlayer().can_pause():
                self.vlcMediaListPlayer.set_pause(True)
            elif self.shouldStop:
                self.vlcMediaListPlayer.stop()
    def tuneFactor(self, freq):
        ''' How good the frequency is tuned to the radio.
            0 - not at all, 1 - perfect
        '''
        dist = self.maxFreq - self.minFreq
        if freq >= self.minFreq and freq <= self.maxFreq:
            return 1
        elif freq >= self.maxFreq and freq <= self.maxFreq + dist:
            return 1 - (freq - self.maxFreq) / dist
        elif freq <= self.minFreq and freq >= self.minFreq - dist:
            return 1 - (self.minFreq - freq) / dist
        else:
            return 0

radios = []

def getRadios(): 
  return radios

def setRadios(theRadios):
  global radios
  radios = theRadios

  for radio1 in radios:
      for radio2 in radios:
          if radio1 != radio2:
              if radio1.tuneFactor(radio2.minFreq) > 0 or radio1.tuneFactor(radio2.maxFreq) > 0:
                  wlog("Core frequency of {} overlaps with {}.".format(radio2.name, radio1.name))
