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

import wx
import wx.xrc
import os
import sys
from pathlib import Path

VERSION = "v2.2"

###########################################################################
## Class GrabadoraGUIFrame
###########################################################################

class GrabadoraGUIFrame(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"Grabadora", pos=wx.DefaultPosition,
                          size=wx.Size(500, 400), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizerVertical = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText1 = wx.StaticText(self, wx.ID_ANY, u"      Nombre del audio", wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        self.m_staticText1.Wrap(-1)
        bSizerVertical.Add(self.m_staticText1, 0, wx.ALL | wx.EXPAND, 5)

        bSizerHorizontal_0 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_textCtrlFilename = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                              wx.TE_PROCESS_ENTER)

        bSizerHorizontal_0.Add(self.m_textCtrlFilename, 1, wx.ALL | wx.EXPAND, 5)

        # Create a button with a file manager icon next to the TextCtrl
        self.m_buttonBrowse = wx.Button(self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(30, 30))
        self.m_buttonBrowse.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_BUTTON))
        bSizerHorizontal_0.Add(self.m_buttonBrowse, 0, wx.ALL, 5)

        # Add the horizontal sizer to the vertical sizer
        bSizerVertical.Add(bSizerHorizontal_0, 0, wx.EXPAND, 5)

        bSizerHorizontal_2 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_buttonMonitor = wx.Button(self, wx.ID_ANY, u"Iniciar monitor", wx.Point(-1, -1), wx.Size(150,30), 0)
        self.m_buttonMonitor.SetBackgroundColour(wx.Colour(0, 0, 128))  # Blue background

        # Set the button's foreground color (text color)
        self.m_buttonMonitor.SetForegroundColour(wx.Colour(255, 255, 255))  # White text
        bSizerHorizontal_2.Add(self.m_buttonMonitor, 0, 0, 5)

        bSizerVertical.Add(bSizerHorizontal_2, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)

        # Add space between the two horizontal sizers (20px spacer)
        bSizerVertical.AddSpacer(20)  # Adds 20 pixels of vertical space

        bSizerHorizontal_1 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_buttonStartRec = wx.Button(self, wx.ID_ANY, u"Iniciar grabacion", wx.Point(-1, -1), wx.DefaultSize, 0)
        self.m_buttonStartRec.SetBackgroundColour(wx.Colour(63, 239, 21))  # Green background

        # Set the button's foreground color (text color)
        self.m_buttonStartRec.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
        bSizerHorizontal_1.Add(self.m_buttonStartRec, 1, 0, 5)

        self.m_buttonStopRec = wx.Button(self, wx.ID_ANY, u"Finalizar grabacion", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_buttonStopRec.SetBackgroundColour(wx.Colour(255, 165, 0))  # Red background

        # Set the button's foreground color (text color)
        self.m_buttonStopRec.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
        bSizerHorizontal_1.Add(self.m_buttonStopRec, 1, 0, 5)

        bSizerVertical.Add(bSizerHorizontal_1, 1, wx.EXPAND, 5)

        bSizer7 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_staticText6 = wx.StaticText(self, wx.ID_ANY, u"    Tiempo de grabacion", wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        self.m_staticText6.Wrap(-1)
        bSizer7.Add(self.m_staticText6, 0, wx.ALL, 5)

        self.m_textCtrlRecTime = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer7.Add(self.m_textCtrlRecTime, 0, 0, 5)

        bSizerVertical.Add(bSizer7, 1, wx.EXPAND, 5)

        self.m_staticText11 = wx.StaticText(self, wx.ID_ANY, u"      Nivel del microfono", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText11.Wrap(-1)
        bSizerVertical.Add(self.m_staticText11, 0, 0, 5)

        self.m_gaugeMicLevel = wx.Gauge(self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL)
        self.m_gaugeMicLevel.SetValue(0)
        bSizerVertical.Add(self.m_gaugeMicLevel, 0, wx.ALL | wx.EXPAND, 5)

        self.m_staticText12 = wx.StaticText(self, wx.ID_ANY, u"      Amplificacion del microfono", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText12.Wrap(-1)
        bSizerVertical.Add(self.m_staticText12, 0, 0, 5)

        self.m_gain_slider = wx.Slider(self, value=20, minValue=1, maxValue=40, style=wx.SL_HORIZONTAL)
        # Add tick marks to the slider
        self.m_gain_slider.SetTickFreq(1)

        # Create a label to display the current value
        self.m_slider_label = wx.StaticText(self, label=f"Amplificación: {self.m_gain_slider.GetValue()}")

        bSizerVertical.Add(self.m_gain_slider, 0, wx.ALL | wx.EXPAND, 5)
        bSizerVertical.Add(self.m_slider_label, flag=wx.CENTER | wx.ALL, border=10)

        # Create a horizontal sizer
        bSizerHorizontal_3 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_buttonExit = wx.Button(self, wx.ID_ANY, u"Salir!", wx.DefaultPosition, wx.DefaultSize, 0)

        # Add the button to the horizontal sizer
        bSizerHorizontal_3.Add(self.m_buttonExit, 0, wx.ALL, 5)

        # Add a stretchable space to push the text to the right
        bSizerHorizontal_3.AddStretchSpacer(1)

        # Create the text label
        self.m_textLabel = wx.StaticText(self, wx.ID_ANY, VERSION, wx.DefaultPosition, wx.DefaultSize, 0)

        # Add the text label to the horizontal sizer
        bSizerHorizontal_3.Add(self.m_textLabel, 0, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)

        bSizerVertical.Add(bSizerHorizontal_3, 0, wx.EXPAND, 5)

        self.SetSizer(bSizerVertical)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.m_textCtrlFilename.Bind(wx.EVT_KILL_FOCUS, self.onAudioNameUpdate)
        self.m_buttonBrowse.Bind(wx.EVT_BUTTON, self.on_browse)
        self.m_buttonMonitor.Bind(wx.EVT_BUTTON, self.onMonitor)
        self.m_buttonStartRec.Bind(wx.EVT_BUTTON, self.onStartRec)
        self.m_buttonStopRec.Bind(wx.EVT_BUTTON, self.onStopRec)
        self.m_gain_slider.Bind(wx.EVT_SLIDER, self.onGainChange)

        #self.m_sliderVolumeOutput.Bind(wx.EVT_SCROLL, self.onVolumeUpdate)
        self.m_buttonExit.Bind(wx.EVT_BUTTON, self.onFrameExit)

        # Determine the correct path to the icon file
        icon_path = self.get_icon_path("grabadora.ico")

        # Set the icon for the window
        icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.Show(True)

    def get_icon_path(self, filename):
        # Handle the path correctly when running from an executable or script
        if getattr(sys, 'frozen', False):  # When running as an executable
            return os.path.join(sys._MEIPASS, filename)
        else:
            return filename  # Running from the script

    def __del__(self):
        pass

    def on_browse(self, event):

        # Get the current filename from the TextCtrl
        default_filename = self.m_textCtrlFilename.GetValue()

        desktop_path = Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))

        # Define the path for the "CdS Audio" directory
        cds_audio_path = desktop_path / "CdS Audio"


        # Create a file dialog for saving the file
        with wx.FileDialog(self, "Guardar archivo de audio", defaultDir=str(cds_audio_path), defaultFile=default_filename, wildcard="WAV files (*.wav)|*.wav",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as save_dialog:

            # Show the dialog and check if the user pressed OK
            if save_dialog.ShowModal() == wx.ID_OK:
                # Get the chosen file path
                save_path = save_dialog.GetPath()

                # Set the file path in the TextCtrl
                if save_path.endswith('.wav'):
                    base, extension = save_path.rsplit('.', 1)

                self.m_textCtrlFilename.SetValue(base)

        event.Skip()

    # Virtual event handlers, override them in your derived class
    def onAudioNameUpdate(self, event):
        event.Skip()

    def onMonitor(self, event):
        event.Skip()

    def onStartRec(self, event):
        event.Skip()

    def onStopRec(self, event):
        event.Skip()

    def onGainChange(self, event):
        event.Skip()

    def onFrameExit(self, event):
        event.Skip()
