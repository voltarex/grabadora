import time
import wave
import datetime
import os
import wx
import logging
import subprocess

import pyaudio
from pydub import AudioSegment
# from pynput import keyboard
import numpy as np
# from scipy.signal import resample

import GrabadoraGUIFrame

# pyaudio constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Set up logging
logging.basicConfig(
    filename='grabadora.log',       # Log file location
    filemode='w',                   # Overwrite the log file instead of appending
    level=logging.DEBUG,            # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)


# def resample_audio(audio_data, orig_rate, target_rate):
#     num_samples = int(len(audio_data) * float(target_rate) / orig_rate)
#     return resample(audio_data, num_samples)
#
# def mono_to_stereo(mono_data):
#     return np.repeat(mono_data, 2)
#
# def stereo_to_mono(stereo_data):
#     return np.mean(stereo_data.reshape(-1, 2), axis=1)

def check_ffmpeg_installed():
    try:
        # Try to run 'ffmpeg -version' to check if it's installed
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logging.debug("ffmpeg instalado correctamente")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Return False if ffmpeg is either not installed or fails to run
        return False

def notify_ffmpeg_missing():
    wx.MessageBox(
        "FFmpeg no está instalado o no se lo encuentra en su PATH.\n\n"
        "Asegurese de instalarlo adecuadamente.\n\n"
        "https://ffmpeg.org/download.html \n\n"
        "Mientras tanto, la grabadora funcionara adecuadamente,\n"
        "  pero no habra conversión de formato wav a mp3.",
        "FFmpeg Not Found",
        wx.ICON_ERROR | wx.OK
    )


class GUI(GrabadoraGUIFrame.GrabadoraGUIFrame):
    def __init__(self, parent):
        logging.info("Start GrabadoraGUIFrame")
        GrabadoraGUIFrame.GrabadoraGUIFrame.__init__(self, parent)

        # Create a WAV file with a unique filename based on date and time
        now = datetime.datetime.now()

        self.audioCallback = MyAudioCallback(self)
        self.pya = None
        self.stream = None
        self.output_wavefile = None
        self.state_fsm = "init"
        self.peak_level_db = None

        logging.info("Set output filename")
        self.output_filename = f"audio_{now.strftime('%d-%m-%Y_%H-%M-%S')}.wav"
        self.m_textCtrlFilename.SetValue(self.output_filename)

        # Initialize variables for the time counter
        logging.info("Create timer")
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_timer, self.timer)
        self.counter = 0
        self.running = False

        self.export = True
        if not check_ffmpeg_installed():
            notify_ffmpeg_missing()
            self.export = False


    def onAudioNameUpdate(self, event):
        logging.debug("output filename updated")
        self.output_filename = self.m_textCtrlFilename.GetValue()
        event.Skip()

    def onStartRec(self, event):
        # if all is already initialized and we return after a 'pause'
        logging.info("onStartRec")
        if self.state_fsm == "pause":
            logging.debug("stream.start_stream()")
            self.stream.start_stream()

            logging.debug("Restart timer")
            self.timer.Start(100)  # Start the timer to trigger every 100ms

            frame.m_buttonStartRec.SetLabel("Grabando...")
            frame.m_buttonPauseRec.SetLabel("Pausar grabacion")
            frame.m_buttonStartRec.Disable()
            frame.m_buttonPauseRec.Enable()
            frame.m_buttonStopRec.Enable()

            self.state_fsm = "start"
        # this is the first 'start'
        if self.state_fsm == "init":
            try:
                # lock the filename
                self.m_textCtrlFilename.SetEditable(False)
                logging.debug("Start pyaudio.PyAudio()")
                self.pya = pyaudio.PyAudio()

                # Get default input and output device info
                input_device = self.pya.get_default_input_device_info()
                output_device = self.pya.get_default_output_device_info()

                self.input_channels = input_device['maxInputChannels']
                self.output_channels = output_device['maxOutputChannels']
                self.input_rate = int(input_device['defaultSampleRate'])
                self.output_rate = int(output_device['defaultSampleRate'])

                logging.debug(f"Default Input: {self.input_channels} channels at {self.input_rate} Hz")
                logging.debug(f"Default Output: {self.output_channels} channels at {self.output_rate} Hz")
                logging.debug("")


                # List all audio devices and their information
                for i in range(self.pya.get_device_count()):
                    info = self.pya.get_device_info_by_index(i)
                    logging.debug(f"Device {i}: {info['name']}")
                    logging.debug(f"  Input Channels: {info['maxInputChannels']}")
                    logging.debug(f"  Output Channels: {info['maxOutputChannels']}")

                logging.debug("")
                logging.debug("Open pyaudio.PyAudio()")
                self.stream = self.pya.open(format=self.pya.get_format_from_width(2),
                                            channels=CHANNELS,
                                            rate=RATE,
                                            input=True,
                                            output=True,
                                            stream_callback=self.audioCallback.audio_processing_callback)

                logging.debug("Open output_wavefile")
                self.output_wavefile = wave.open(frame.output_filename, 'wb')
                self.output_wavefile.setnchannels(CHANNELS)
                self.output_wavefile.setsampwidth(self.pya.get_sample_size(FORMAT))
                self.output_wavefile.setframerate(RATE)

                # Record the start time
                self.counter = 0  # Reset the counter on start

                logging.debug("Start timer")
                self.timer.Start(100)  # Start the timer to trigger every 100ms

                frame.m_buttonStartRec.SetLabel("Grabando...")
                frame.m_buttonStartRec.Disable()
                frame.m_buttonPauseRec.Enable()
                frame.m_buttonStopRec.Enable()

                self.state_fsm = "start"

                logging.info("Audio stream successfully opened.")
            except OSError as e:
                logging.error(f"Failed to open audio stream: {str(e)}")
                frame.m_buttonStartRec.SetLabel("ERROR!")
                self.state_fsm = "error"

            except Exception as e:
                logging.error(f"An unexpected error occurred: {str(e)}")
                frame.m_buttonStartRec.SetLabel("ERROR!")
                self.state_fsm = "error"

        event.Skip()

    def onPauseRec(self, event):
        if self.state_fsm == "start":
            logging.info("onPausetRec")
            logging.debug("stop_steam()")
            self.stream.stop_stream()

            logging.debug("stop timer")
            self.timer.Stop()  # Stop the timer

            frame.m_buttonStartRec.SetLabel("Retomar grabacion")
            frame.m_buttonPauseRec.SetLabel("Grabacion pausada")
            frame.m_buttonStartRec.Enable()
            self.state_fsm = "pause"

        event.Skip()


    def onStopRec(self, event):
        if self.state_fsm == "start" or self.state_fsm == "pause":

            logging.info("onStopRec")
            try:
                logging.debug("stop timer")
                self.timer.Stop()  # Stop the timer

                logging.debug("stop stream")
                self.stream.stop_stream()
                logging.debug("close stream and output wave")
                self.stream.close()
                self.pya.terminate()
                self.output_wavefile.close()

                if self.export:
                    # Read the WAV file
                    logging.debug("read wave")
                    sound = AudioSegment.from_wav(frame.output_filename)

                    # Split the filename at the last dot (.) to get the base name and extension
                    base, extension = frame.output_filename.rsplit('.', 1)
                    mp3_filename = f"{base}.mp3"

                    # Export the sound as MP3
                    logging.debug(f"export wave {frame.output_filename} to {mp3_filename}")
                    sound.export(mp3_filename, format="mp3")
                    logging.debug("delete wave")
                    os.remove(frame.output_filename)

                logging.debug("disable all buttons")
                frame.m_buttonStopRec.SetLabel("Grabacion concluida.")
                frame.m_buttonStartRec.Disable()
                frame.m_buttonPauseRec.Disable()
                frame.m_buttonStopRec.Disable()
                logging.info("All closed successfully.")

                self.state_fsm = "stop"

            except OSError as e:
                logging.error(f"Failed to close audio stream: {str(e)}")
                self.state_fsm = "error"

            except Exception as e:
                logging.error(f"An unexpected error occurred: {str(e)}")
                self.state_fsm = "error"

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
        logging.debug("onFrameExit")
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

        # # Resample if needed (input_rate != output_rate)
        # if self.instance.input_rate != self.instance.output_rate:
        #     audio_data = resample_audio(audio_data, self.instance.input_rate, self.instance.output_rate)
        #
        # # Handle channel differences
        # if self.instance.input_channels == 1 and self.instance.output_channels == 2:
        #     audio_data = mono_to_stereo(audio_data)
        # elif self.instance.input_channels == 2 and self.instance.output_channels == 1:
        #     audio_data = stereo_to_mono(audio_data)

        # Process audio data for recording (e.g., write to a buffer)
        # output_wavefile.writeframes(in_data)  # Write data to the WAV file
        while self.instance.output_wavefile is None:
            time.sleep(1)

        self.instance.output_wavefile.writeframes(audio_data)  # Write data to the WAV file

        # Convert back to bytes
        out_data = audio_data.astype(np.int16).tobytes()

        return (out_data, pyaudio.paContinue)

        # Adjust volume (multiply by 0.5 for 50% reduction)
        #adjusted_data = bytearray(int(sample) for sample in in_data)
        #return in_data, pyaudio.paContinue


if __name__ == "__main__":
    logging.info("Application starting.")
    app = wx.App(False)
    logging.info("Frame starting.")
    frame = GUI(None)
    logging.info("Start frame.update_display()")
    frame.update_display()  # Show initial time in the text control
    logging.info("Disable Pause & Stop buttons")
    frame.m_buttonPauseRec.Disable()
    frame.m_buttonStopRec.Disable()
    logging.info("Start main loop")
    app.MainLoop()
