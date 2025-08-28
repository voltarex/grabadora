
"""
Audio Recorder GUI Application
==============================

Description:
    A wxPython-based graphical interface for audio recording and monitoring.
    Uses PyAudio for real-time audio input/output, records to WAV format,
    and optionally converts recordings to MP3 using FFmpeg (if installed).

Features:
    - Monitor microphone input with live peak level display.
    - Start and stop audio recording.
    - Save recordings to WAV format and optionally export to MP3.
    - Adjustable input gain via a slider control.
    - Timer display showing elapsed recording time.

Dependencies:
    - Python 3.x
    - wxPython
    - PyAudio
    - NumPy
    - pydub
    - gevent
    - FFmpeg (optional, for MP3 export)

Author: Aaron Elberg (voltarex)
Created: 24-Aug-2024
Last Updated:
License:
MIT License

Copyright (c) 2024 Aaron Elberg, aka voltarex

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import time
import wave
import datetime
import os
import wx
import logging
import subprocess
import pyaudio
from pydub import AudioSegment
import numpy as np
from pathlib import Path

import GrabadoraGUIFrame

# pyaudio constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
GAIN = 2.0

# Set up logging
logging.basicConfig(
    filename='grabadora.log',       # Log file location
    filemode='w',                   # Overwrite the log file
    level=logging.INFO,             # Log level
    format='%(asctime)s - %(levelname)s - %(name)s.%(funcName)s - %(message)s'
)
def check_ffmpeg_installed():
    """
    Check whether FFmpeg is installed and accessible in the system PATH.

    Attempts to run `ffmpeg -version` using subprocess. If the command executes
    successfully, FFmpeg is considered installed.

    Returns:
        bool: True if FFmpeg is installed and executable, False otherwise.
    """
    try:
        # Try to run 'ffmpeg -version' to check if it's installed
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logging.info("ffmpeg instalado correctamente")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Return False if ffmpeg is either not installed or fails to run
        return False

def notify_ffmpeg_missing():
    """
    Show a wxPython message box notifying the user that FFmpeg is not installed.

    Informs the user that recordings will still work but conversion from WAV
    to MP3 will be disabled until FFmpeg is properly installed.
    """
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
    """
    Main application GUI class for the audio recorder.

    Extends:
        GrabadoraGUIFrame.GrabadoraGUIFrame

    Responsibilities:
        - Manage user interface events for monitoring and recording.
        - Control audio input/output streams with PyAudio.
        - Handle WAV recording and optional MP3 export (via FFmpeg).
        - Track recording time, audio gain, and microphone peak levels.
    """
    def __init__(self, parent):
        """
        Initialize the GUI frame and application state.

        Args:
            parent: Parent window for this frame.
        """
        # Create a per-class logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Starting GrabadoraGUIFrame")
        GrabadoraGUIFrame.GrabadoraGUIFrame.__init__(self, parent)

        self.audioCallback = MyAudioCallback(self)
        self.pya = pyaudio.PyAudio()

        # Streams
        self.monitor_stream = None
        self.record_stream = None

        # File handling
        self.output_wavefile = None
        self.output_filename = ""

        # FSM and levels
        self.state_fsm = "idle"
        self.peak_level_db = None
        self.current_gain = 2.0

        # Devices info
        self.input_channels = None
        self.output_channels = None
        self.input_rate = None
        self.output_rate = None

        # Timer
        self.timer = None
        self.start_time = None  # When the timer was last started
        self.rec_elapsed = 0.0  # Total elapsed time before last pause
        self.timer_running = False

        # Desktop path
        desktop_path = Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))
        self.cds_audio_path = desktop_path / "CdS Audio"
        if not self.cds_audio_path.exists():
            self.cds_audio_path.mkdir(parents=True)
            self.logger.info(f'Directory "CdS Audio" created at: {self.cds_audio_path}')
        else:
            self.logger.info(f'Directory "CdS Audio" already exists at: {self.cds_audio_path}')

        self.export = True
        if not check_ffmpeg_installed():
            notify_ffmpeg_missing()
            self.export = False

        # Get default devices
        self.logger.info("Start pyaudio.PyAudio()")
        self.pya = pyaudio.PyAudio()

        input_device = self.pya.get_default_input_device_info()
        output_device = self.pya.get_default_output_device_info()
        self.input_channels = input_device['maxInputChannels']
        self.output_channels = output_device['maxOutputChannels']
        self.input_rate = int(input_device['defaultSampleRate'])
        self.output_rate = int(output_device['defaultSampleRate'])
        self.logger.info(f"Default Input: {self.input_channels} channels at {self.input_rate} Hz")
        self.logger.info(f"Default Output: {self.output_channels} channels at {self.output_rate} Hz")

        # List all audio devices and their information
        for i in range(self.pya.get_device_count()):
            info = self.pya.get_device_info_by_index(i)
            logging.debug(f"Device {i}: {info['name']}")
            logging.debug(f"  Input Channels: {info['maxInputChannels']}")
            logging.debug(f"  Output Channels: {info['maxOutputChannels']}")
        self.logger.info("")

    def onAudioNameUpdate(self, event):
        """
        Update the output filename when the user modifies the text field.

        Ensures the filename ends with '.wav' and stores it in
        `self.output_filename`.

        Args:
            event: wx.Event triggered by filename text update.
        """
        self.logger.info("output filename updated")
        self.output_filename = self.m_textCtrlFilename.GetValue()
        if not self.output_filename.endswith('.wav'):
            self.output_filename += '.wav'

        event.Skip()

    def onMonitor(self, event):
        """
        Toggle audio monitoring mode.

        - If idle: opens a PyAudio stream, initializes default devices,
          and starts monitoring microphone input/output without recording.
        - If monitoring: stops and closes the audio stream, returning to idle.

        Args:
            event: wx.Event triggered by monitor button.
        """

        try:
            if self.state_fsm not in ["idle", "monitoring"]:
                raise ValueError("Invalid state")

            if self.state_fsm == "idle":
                self.logger.info("Start monitoring")

                # Create a WAV file with a unique filename based on date and time
                now = datetime.datetime.now()

                self.logger.info("Set output filename")
                self.output_filename = f"audio_{now.strftime('%d-%m-%Y_%H-%M-%S')}.wav"
                base, extension = self.output_filename.rsplit('.', 1)
                self.m_textCtrlFilename.SetValue(base)
                self.m_textCtrlFilename.SetEditable(True)

                self.logger.info("Initialize buttons")
                self.m_buttonMonitor.SetLabel("Finalizar monitor")
                self.m_buttonStartRec.SetLabel("Iniciar grabacion")
                self.m_buttonStopRec.SetLabel("Finalizar grabacion")
                self.m_buttonMonitor.Enable()
                self.m_buttonStartRec.Enable()
                self.m_buttonStopRec.Disable()
                self.m_textCtrlFilename.Enable()
                self.m_textCtrlFilename.SetEditable(True)

                self.logger.info("Open pyaudio.PyAudio() for monitor streaming")
                # Open monitoring stream only (input->output)
                self.monitor_stream = self.pya.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=self.audioCallback.monitor_callback
                )

                self.monitor_stream.start_stream()

                # Initialize variables for the time count
                self.logger.info("Create timer")
                self.timer = wx.Timer(self)
                self.Bind(wx.EVT_TIMER, self.update_timer, self.timer)

                # Start the timer to trigger every 100ms
                self.timer.Start(100)

                self.current_gain = 2.0 # reset the gain
                self.m_gain_slider.SetValue(20)
                self.m_slider_label.SetLabel(f"Amplificación: {20}")
                self.state_fsm = "monitoring"

            elif self.state_fsm == "monitoring":
                self.logger.info("Stop monitoring")

                if self.monitor_stream:
                    self.monitor_stream.stop_stream()
                    self.monitor_stream.close()
                    self.monitor_stream = None

                # stop the timer
                self.logger.info("stop timer")
                if self.timer:
                    self.timer.Stop()  # Stop the timer
                    self.timer = None
                    self.start_time = None

                self.logger.info("Reset buttons")
                self.m_buttonMonitor.SetLabel("Iniciar monitor")
                self.m_buttonStartRec.SetLabel("Iniciar grabacion")
                self.m_buttonStopRec.SetLabel("Finalizar grabacion")
                self.m_buttonStartRec.Disable()
                self.m_buttonStopRec.Disable()
                self.m_textCtrlFilename.SetValue("")
                self.m_textCtrlFilename.Disable()
                self.m_textCtrlFilename.SetEditable(False)

                self.state_fsm = "idle"

            event.Skip()

        except ValueError as e:
            logging.error(f"Invalid state: {str(e)}")
            self.m_buttonStartRec.SetLabel("ERROR!")
            self.m_buttonMonitor.SetLabel("ERROR!")
            self.m_buttonStartRec.SetLabel("ERROR!")
            self.m_buttonStopRec.SetLabel("ERROR!")
            self.state_fsm = "error"

        except OSError as e:
            logging.error(f"Failed to open audio stream: {str(e)}")
            self.m_buttonMonitor.SetLabel("ERROR!")
            self.state_fsm = "error"

        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            self.m_buttonMonitor.SetLabel("ERROR!")
            self.state_fsm = "error"

    def onStartRec(self, event):
        """
        Start or resume audio recording.

        - From 'init': creates output WAV file, starts timer, and
          begins writing audio frames.

        Args:
            event: wx.Event triggered by record button.
        """
        self.logger.info("onStartRec")
        if self.state_fsm not in ["monitoring", "recording", "pause_rec"]:
            raise ValueError("Invalid state")

        try:
            if self.state_fsm == "monitoring":
                self.logger.info("Start recording")

                # lock the filename
                self.logger.info("Lock filename")
                self.m_textCtrlFilename.SetEditable(False)
                self.m_textCtrlFilename.Disable()
                self.output_filename = self.m_textCtrlFilename.GetValue()
                if not self.output_filename.endswith('.wav'):
                    self.output_filename += '.wav'
                self.output_filename = os.path.join(self.cds_audio_path, self.output_filename)

                self.logger.info("Open output_wavefile")
                self.output_wavefile = wave.open(self.output_filename, 'wb')
                self.output_wavefile.setnchannels(CHANNELS)
                self.output_wavefile.setsampwidth(self.pya.get_sample_size(FORMAT))
                self.output_wavefile.setframerate(RATE)

                # Open input-only recording stream
                self.logger.info("Open Audio stream for output file.")
                self.record_stream = self.pya.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=False,
                    frames_per_buffer=CHUNK,
                    stream_callback=self.audioCallback.record_callback
                )
                self.record_stream.start_stream()

                # start elapsed time counter
                self.rec_elapsed = 0
                self.start_time = time.monotonic()
                self.timer_running = True

                frame.m_buttonStartRec.SetLabel("Grabando...")

                self.state_fsm = "recording"

            elif self.state_fsm == "recording":
                self.logger.info("Pause recording")
                self.record_stream.stop_stream()

                frame.m_buttonStartRec.SetLabel("Pausado...")
                frame.m_buttonStartRec.SetBackgroundColour(wx.Colour(255, 255, 0))  # Yellow
                frame.m_buttonStartRec.Refresh()

                if self.timer_running:
                    # Add the time from last start to now
                    self.rec_elapsed += time.monotonic() - self.start_time
                    self.timer_running = False

                self.state_fsm = "pause_rec"

            elif self.state_fsm == "pause_rec":
                self.logger.info("Resume recording")
                self.record_stream.start_stream()

                # start elapsed time counter
                self.start_time = time.monotonic()
                self.timer_running = True

                frame.m_buttonStartRec.SetLabel("Grabando...")
                frame.m_buttonStartRec.SetBackgroundColour(wx.Colour(63, 239, 21))
                frame.m_buttonStartRec.Refresh()

                self.state_fsm = "recording"


        except OSError as e:
            logging.error(f"Failed to open audio stream: {str(e)}")
            frame.m_buttonStartRec.SetLabel("ERROR!")
            self.state_fsm = "error"

        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            frame.m_buttonStartRec.SetLabel("ERROR!")
            self.state_fsm = "error"

        frame.m_buttonMonitor.Disable()
        frame.m_buttonStartRec.Enable()
        frame.m_buttonStopRec.Enable()
        event.Skip()

    def onStopRec(self, event):
        """
        Stop audio recording and close audio file.
        Monitoring is ON, state FSM moves to "monitoring"

        - Stops timer .
        - Finalizes WAV file and closes it.
        - If export is enabled, converts the WAV file to MP3 via FFmpeg
          and deletes the original WAV file.
        - Updates UI buttons to indicate completion.

        Args:
            event: wx.Event triggered by stop button.
        """
        if self.state_fsm not in ["recording", "pause_rec"]:
            raise ValueError("Invalid state")

        self.logger.info("onStopRec")
        try:

            self.logger.info("close wavefile")
            # Stop recording stream
            if self.record_stream:
                self.record_stream.stop_stream()
                self.record_stream.close()
                self.record_stream = None

            # Close WAV file
            if self.output_wavefile:
                self.output_wavefile.close()
                self.output_wavefile = None

            # Close the elapsed time counter
            if self.timer_running:
                # Add the time from last start to now
                self.rec_elapsed += time.monotonic() - self.start_time
                self.timer_running = False

            if self.export:
                # Read the WAV file
                self.logger.info("read wave")
                sound = AudioSegment.from_wav(frame.output_filename)

                # Split the filename at the last dot (.) to get the base name and extension
                base, _ = frame.output_filename.rsplit('.', 1)
                mp3_filename = f"{base}.mp3"

                # Export the sound as MP3
                self.logger.info(f"export wave {frame.output_filename} to {mp3_filename}")
                sound.export(mp3_filename, format="mp3", bitrate="192k")
                self.logger.info("delete wave")
                os.remove(frame.output_filename)


            self.logger.info("All closed successfully. Return to monitoring state")

            self.logger.info("Set output filename")
            # Create a WAV file with a unique filename based on date and time
            now = datetime.datetime.now()
            self.output_filename = f"audio_{now.strftime('%d-%m-%Y_%H-%M-%S')}.wav"
            base, extension = self.output_filename.rsplit('.', 1)
            self.m_textCtrlFilename.SetValue(base)
            self.m_textCtrlFilename.SetEditable(True)

            self.logger.info("Initialize buttons")
            self.m_buttonMonitor.SetLabel("Finalizar monitor")
            self.m_buttonStartRec.SetLabel("Iniciar grabacion")
            self.m_buttonStopRec.SetLabel("Finalizar grabacion")
            self.m_buttonStartRec.SetBackgroundColour(wx.Colour(63, 239, 21))
            self.m_buttonStartRec.Refresh()
            self.m_buttonMonitor.Enable()
            self.m_buttonStartRec.Enable()
            self.m_buttonStopRec.Disable()
            self.m_textCtrlFilename.Enable()
            self.m_textCtrlFilename.SetEditable(True)
            self.state_fsm = "monitoring"

        except OSError as e:
            logging.error(f"Failed to close audio stream: {str(e)}")
            self.state_fsm = "error"

        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            self.state_fsm = "error"

        event.Skip()

    def elapsed(self):
        """
        Calculates recording elpased time

        Updates `self.rec_elapsed` based on the accumulated value and current time

        Args:
            None
        """
        if self.timer_running:
            return self.rec_elapsed + (time.monotonic() - self.start_time)
        else:
            return self.rec_elapsed

    def onGainChange(self, event):
        """
        Handle changes to the gain slider.

        Updates `self.current_gain` based on the slider value and
        reflects the value in the UI label.

        Args:
            event: wx.Event triggered by slider adjustment.
        """
        slider_value = self.m_gain_slider.GetValue()
        self.current_gain = slider_value / 10.0  # Adjust gain based on slider position

        self.m_slider_label.SetLabel(f"Amplificación: {slider_value}")

        event.Skip()

    def update_timer(self, event):
        """
        Increment the recording timer counter and refresh the display.

        Triggered every 100 ms by a wx.Timer during active recording.

        Args:
            event: wx.TimerEvent generated by the timer.
        """

        self.update_display()

    def update_display(self):
        """
        Update the recording time display and microphone level gauge.

        - Converts internal counter into a formatted time string (HH:MM:SS.mmm).
        - Updates the text control with elapsed time.
        - Updates microphone input level gauge if peak level is available.
        """

        # Convert counter to hours:minutes:seconds:milliseconds format
        elapsed = self.elapsed()
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        milliseconds = int((elapsed - int(elapsed)) * 1000)

        # Update the text control with the formatted time
        time_str = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
        self.m_textCtrlRecTime.SetValue(time_str)

        if self.peak_level_db is not None:
            gauge_value = self.map_db_to_gauge()
            self.m_gaugeMicLevel.SetValue(gauge_value)

    def map_db_to_gauge(self):
        """
        Map a peak decibel level to a gauge value (0–100).

        - -60 dB maps to 0 (silence).
        - 0 dB maps to 100 (maximum level).
        - Values in between are linearly scaled.

        Returns:
            int: Gauge value between 0 and 100.
        """

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
        """
        Exit the application when the frame is closed.

        Args:
            event: wx.Event triggered by window close action.
        """
        self.logger.info("onFrameExit")
        wx.Exit()  # This will close the entire application

class MyAudioCallback(wx.EvtHandler):
    """
    Helper class that wraps the PyAudio callback function.

    Stores a reference to the main GUI instance so that the
    callback can update state such as gain and peak levels.
    """
    def __init__(self, instance):
        """
        Initialize the callback handler.

        Args:
            instance (GUI): Reference to the GUI class that owns
                            the recording state and output file.
        """
        super().__init__()
        self.instance = instance  # Store the instance reference
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Audio callback handler initialized")


    def monitor_callback(self, in_data, frame_count, time_info, status):
        """
        PyAudio stream callback for monitoring audio data.

        Workflow:
            - Converts input bytes to NumPy array of int16 samples.
            - Applies gain from `instance.current_gain`.
            - Clips values to int16 range.
            - Updates peak decibel level for UI gauge.
            - Writes amplified samples to WAV file if in 'start' state.
            - Returns processed audio as bytes for playback.

        Args:
            in_data (bytes): Raw input audio data.
            frame_count (int): Number of audio frames in this buffer.
            time_info (dict): Timing information from PyAudio.
            status (int): Status flag from PyAudio.

        Returns:
            tuple: (out_data, pyaudio.paContinue)
        """
        # Convert audio data to NumPy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        # Apply gain dynamically
        adjusted_gain = self.instance.current_gain  # Use the current gain from the instance
        amplified_data = np.clip(audio_data * adjusted_gain, -32768, 32767).astype(np.int16)  # Apply gain and clip
        # amplified_data = np.clip(audio_data * adjusted_gain, np.iinfo(np.int16).min, np.iinfo(np.int16).max).astype(np.int16)

        # Calculate the peak level (maximum absolute value)
        peak_level = np.max(np.abs(amplified_data))

        # Avoid divide by zero issue by checking if peak_level is 0
        if peak_level > 0:
            self.instance.peak_level_db = 20 * np.log10(peak_level / np.iinfo(np.int16).max)
        else:
            self.instance.peak_level_db = -100  # Set to a very low dB value for silence

        # Convert back to bytes
        out_data = amplified_data.tobytes()

        return out_data, pyaudio.paContinue


    def record_callback(self, in_data, frame_count, time_info, status):
        """
        PyAudio stream callback for writing audio data to a file.

        Workflow:
            - Converts input bytes to NumPy array of int16 samples.
            - Applies gain from `instance.current_gain`.
            - Clips values to int16 range.
            - Updates peak decibel level for UI gauge.
            - Writes amplified samples to WAV file if in 'start' state.
            - Returns processed audio as bytes for playback.

        Args:
            in_data (bytes): Raw input audio data.
            frame_count (int): Number of audio frames in this buffer.
            time_info (dict): Timing information from PyAudio.
            status (int): Status flag from PyAudio.

        Returns:
            tuple: (None, pyaudio.paContinue)
        """
        # Convert audio data to NumPy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        # Apply gain dynamically
        adjusted_gain = self.instance.current_gain  # Use the current gain from the instance
        amplified_data = np.clip(audio_data * adjusted_gain, -32768, 32767).astype(np.int16)  # Apply gain and clip
        # amplified_data = np.clip(audio_data * adjusted_gain, np.iinfo(np.int16).min, np.iinfo(np.int16).max).astype(np.int16)

        # Calculate the peak level (maximum absolute value)
        peak_level = np.max(np.abs(amplified_data))

        # Avoid divide by zero issue by checking if peak_level is 0
        if peak_level > 0:
            self.instance.peak_level_db = 20 * np.log10(peak_level / np.iinfo(np.int16).max)
        else:
            self.instance.peak_level_db = -100  # Set to a very low dB value for silence

        # Process audio data for recording (e.g., write to a buffer)
        while self.instance.output_wavefile is None:
            time.sleep(1)

        # only write to output file if in start mode; if pause, don't
        if self.instance.output_wavefile is not None:
            self.instance.output_wavefile.writeframes(amplified_data)  # Write data to the WAV file

        return None, pyaudio.paContinue


if __name__ == "__main__":
    logging.info("Start app.")
    app = wx.App(False)
    logging.info("Start Frame (GUI)).")
    frame = GUI(None)
    logging.info("Start frame.update_display()")
    frame.update_display()  # Show initial time in the text control
    logging.info("Disable all buttons")
    frame.m_buttonMonitor.Enable()
    frame.m_buttonStartRec.Disable()
    frame.m_buttonStopRec.Disable()
    logging.info("Start main loop")
    app.MainLoop()
