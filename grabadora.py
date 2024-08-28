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

# Initialize volume factor (initially 1.0 for no adjustment)
volume_factor = 1.0

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
        self.resume_after_pause = False
        self.start_time = None
        self.output_filename = f"audio_{now.strftime('%d-%m-%Y_%H-%M-%S')}.wav"
        self.m_textCtrlFilename.SetValue(self.output_filename)


    def onAudioNameUpdate(self, event):
        self.output_filename = self.m_textCtrlFilename.GetValue()
        event.Skip()

    def onStartRec(self, event):
        if not self.resume_after_pause:
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
            self.start_time = time.time()

        event.Skip()

    def onPauseRec(self, event):
        self.stream.pause_stream()
        event.Skip()

    def onStopRec(self, event):
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

        event.Skip()

    def onVolumeUpdate(self, event):
        event.Skip()

    def onFrameExit(self, event):
        wx.Exit()  # This will close the entire application

    def run_loop(self, event):

        while self.stream.is_active():
            elapsed_time = time.time() - self.start_time

            # Convert elapsed time to hours, minutes, and seconds
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Format the time as HH:MM:SS
            formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

            #print(f"\r* Tiempo de grabacion: {formatted_time} (Volumen: {volume_factor:.2f})", end="", flush=True)

            time.sleep(0.1)

            # Record the end time
            end = time.time()

            # Yield to other threads
            wx.Yield()

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
        peak_level_db = 20 * np.log10(peak_level / np.iinfo(np.int16).max)

        # Adjust volume (multiply by 0.5 for 50% reduction)
        adjusted_data = bytearray(int(sample * volume_factor) for sample in in_data)

        # Process audio data for recording (e.g., write to a buffer)
        #output_wavefile.writeframes(in_data)  # Write data to the WAV file
        while self.instance.output_wavefile is None:
            time.sleep(1)

        self.instance.output_wavefile.writeframes(adjusted_data)  # Write data to the WAV file
        return in_data, pyaudio.paContinue

if __name__ == "__main__":
    app = wx.App(False)
    frame = GUI(None)
    app.MainLoop()


# print(f"* Tiempo total de grabacion: {formatted_time}")
#
# print(f'* Grabacion guardada en el archivo: {mp3_filename}')
#
# # Delete the original WAV file (use with caution)
# try:
#     os.remove(frame.output_filename)
# except FileNotFoundError:
#     print(f"* Archivo WAV {frame.output_filename} no se encontro. Nada sera borrado.")

##################################
########### Volume stuff
# create a separate thread to capture user's volume input
# volume_change_timer = None
# volume_change_amount = 0
#
# def start_volume_change(amount):
#     global volume_change_timer, volume_change_amount
#     volume_change_amount = amount
#     volume_change_timer = threading.Timer(0.2, adjust_volume)
#     volume_change_timer.start()
#
# def adjust_volume():
#     global volume_factor, volume_change_amount, volume_change_timer
#     volume_factor = min(max(volume_factor + volume_change_amount, 0.1), 1.0)
#     volume_change_amount = 0
#     volume_change_timer = None
#
#
# def on_press(key):
#     global volume_change_timer
#     try:
#         k = key.char  # single-char keys
#     except:
#         k = key  # for special keys like ctrl, alt, etc.
#     if k == '+':
#         start_volume_change(0.1)
#     elif k == '-':
#         start_volume_change(-0.1)
#
# def on_release(key):
#     global volume_change_timer
#     if volume_change_timer:
#         volume_change_timer.cancel()
#         volume_change_timer = None
#
# def input_thread():
#     with keyboard.Listener(on_press=on_press) as listener:
#         listener.join()
#
#
# # Start the input thread
# input_thread = threading.Thread(target=input_thread)
# input_thread.daemon = True
# input_thread.start()

