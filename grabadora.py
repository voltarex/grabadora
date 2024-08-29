import time
import wave
import datetime
import os
import wx

import pyaudio
from pydub import AudioSegment
# from pynput import keyboard
import numpy as np

import GrabadoraGUIFrame

# pyaudio constants
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100


# Create a WAV file with a unique filename based on date and time
now = datetime.datetime.now()
formatted_time = ''


class GUI(GrabadoraGUIFrame.GrabadoraGUIFrame):
    def __init__(self, parent):
        GrabadoraGUIFrame.GrabadoraGUIFrame.__init__(self, parent)

        self.audioCallback = MyAudioCallback(self)
        self.pya = None
        self.stream = None
        self.output_wavefile = None
        self.resume_after_stop = False
        self.peak_level_db = None
        self.output_filename = f"audio_{now.strftime('%d-%m-%Y_%H-%M-%S')}.wav"
        self.m_textCtrlFilename.SetValue(self.output_filename)

        # Initialize variables for the time counter
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_timer, self.timer)
        self.counter = 0
        self.running = False

    def onAudioNameUpdate(self, event):
        self.output_filename = self.m_textCtrlFilename.GetValue()
        event.Skip()

    def onStartRec(self, event):
        # if all is already initialized and we return after a 'pause'
        if self.resume_after_stop:
            self.stream.start_stream()
        # this is the first 'start'
        else:
            # lock the filename
            self.m_textCtrlFilename.SetEditable(False)

            self.pya = pyaudio.PyAudio()
            self.stream = self.pya.open(format=self.pya.get_format_from_width(2),
                                        channels=CHANNELS,
                                        rate=44100,
                                        input=True,
                                        output=True,
                                        stream_callback=self.audioCallback.audio_processing_callback)

            self.output_wavefile = wave.open(frame.output_filename, 'wb')
            self.output_wavefile.setnchannels(CHANNELS)
            self.output_wavefile.setsampwidth(self.pya.get_sample_size(FORMAT))
            self.output_wavefile.setframerate(RATE)

            # Record the start time
            self.counter = 0  # Reset the counter on start

        self.timer.Start(100)  # Start the timer to trigger every 100ms

        frame.m_buttonStartRec.SetLabel("Grabando...")
        frame.m_buttonPauseRec.Enable()
        frame.m_buttonStopRec.Enable()

        event.Skip()

    def onPauseRec(self, event):
        self.stream.stop_stream()
        self.resume_after_stop = True  # in case 'start' will be called again

        self.timer.Stop()  # Stop the timer

        frame.m_buttonStartRec.SetLabel("Retomar grabacion")
        frame.m_buttonPauseRec.SetLabel("Grabacion pausada")
        event.Skip()


    def onStopRec(self, event):

        self.timer.Stop()  # Stop the timer

        self.stream.stop_stream()
        self.stream.close()
        self.pya.terminate()
        self.output_wavefile.close()

        # Read the WAV file
        sound = AudioSegment.from_wav(frame.output_filename)

        # Split the filename at the last dot (.) to get the base name and extension
        base, extension = frame.output_filename.rsplit('.', 1)
        mp3_filename = f"{base}.mp3"

        # Export the sound as MP3
        sound.export(mp3_filename, format="mp3")
        os.remove(frame.output_filename)

        frame.m_buttonStopRec.SetLabel("Grabacion concluida.")
        frame.m_buttonStartRec.Disable()
        frame.m_buttonPauseRec.Disable()
        frame.m_buttonStopRec.Disable()

        event.Skip()

    def update_timer(self, event):
        self.counter += 1  # Increment counter (each 100ms, so 10 increments = 1 second)
        self.update_display()

    def update_display(self):
        # Convert counter to hours:minutes:seconds:milliseconds format
        milliseconds = (self.counter * 100) % 1000
        seconds = (self.counter // 10) % 60
        minutes = (self.counter // 600) % 60
        hours = (self.counter // 36000)

        # Update the text control with the formatted time
        time_str = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
        frame.m_textCtrlRecTime.SetValue(time_str)

        if self.peak_level_db is not None:

            gauge_value = self.map_db_to_gauge()
            frame.m_gaugeMicLevel.SetValue(gauge_value)

    def map_db_to_gauge(self):
        # Define the thresholds
        db_min = -60.0  # Silence threshold
        db_max = 0.0  # Maximum signal level (0 dB)

        # Normalize the dB value into a 0-100 range for the gauge
        if self.peak_level_db < db_min:
            return 0  # Below silence threshold, map to 0
        elif self.peak_level_db > db_max:
            return 100  # Above maximum threshold, map to 100

        # Linear scaling between db_min and db_max
        return int((self.peak_level_db - db_min) / (db_max - db_min) * 100)

    def onFrameExit(self, event):
        wx.Exit()  # This will close the entire application



# class crafted around audio_processing_callback with only purpose to pass self as argument
class MyAudioCallback(wx.EvtHandler):
    def __init__(self, instance):
        super().__init__()
        self.instance = instance  # Store the instance reference

    def audio_processing_callback(self, in_data, frame_count, time_info, status):
        # Convert audio data to NumPy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        # Calculate the peak level (maximum absolute value)
        peak_level = np.max(np.abs(audio_data))

        # Calculate peak level in decibels (dB)
        self.instance.peak_level_db = 20 * np.log10(peak_level / np.iinfo(np.int16).max)

        # Adjust volume (multiply by 0.5 for 50% reduction)
        adjusted_data = bytearray(int(sample) for sample in in_data)

        # Process audio data for recording (e.g., write to a buffer)
        # output_wavefile.writeframes(in_data)  # Write data to the WAV file
        while self.instance.output_wavefile is None:
            time.sleep(1)

        self.instance.output_wavefile.writeframes(adjusted_data)  # Write data to the WAV file
        return in_data, pyaudio.paContinue


if __name__ == "__main__":
    app = wx.App(False)
    frame = GUI(None)
    frame.update_display()  # Show initial time in the text control
    frame.m_buttonPauseRec.Disable()
    frame.m_buttonStopRec.Disable()
    app.MainLoop()
