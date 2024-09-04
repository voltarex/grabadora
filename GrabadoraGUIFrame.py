# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Jun 17 2015)
## http://www.wxformbuilder.org/
##
## ANY EDIT OF THIS FILE will be override if changes in wxFormBuilder !
###########################################################################

import wx
import wx.xrc
import os
import sys

###########################################################################
## Class GrabadoraGUIFrame
###########################################################################

class GrabadoraGUIFrame(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"Grabadora", pos=wx.DefaultPosition,
                          size=wx.Size(500, 330), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizerVertical = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText1 = wx.StaticText(self, wx.ID_ANY, u"      Nombre del audio", wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        self.m_staticText1.Wrap(-1)
        bSizerVertical.Add(self.m_staticText1, 0, wx.ALL | wx.EXPAND, 5)

        self.m_textCtrlFilename = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize,
                                              wx.TE_PROCESS_ENTER)

        bSizerVertical.Add(self.m_textCtrlFilename, 0, wx.ALL | wx.EXPAND, 5)

        bSizerHorizontal_1 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_buttonStartRec = wx.Button(self, wx.ID_ANY, u"Comenzar grabacion", wx.Point(-1, -1), wx.DefaultSize, 0)
        self.m_buttonStartRec.SetBackgroundColour(wx.Colour(63, 239, 21))  # Green background

        # Set the button's foreground color (text color)
        self.m_buttonStartRec.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
        bSizerHorizontal_1.Add(self.m_buttonStartRec, 1, 0, 5)

        self.m_buttonPauseRec = wx.Button(self, wx.ID_ANY, u"Pausar grabacion", wx.Point(-1, -1), wx.DefaultSize, 0)
        self.m_buttonPauseRec.SetBackgroundColour(wx.Colour(236, 252, 61))  # Yellow background

        # Set the button's foreground color (text color)
        self.m_buttonPauseRec.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
        bSizerHorizontal_1.Add(self.m_buttonPauseRec, 1, 0, 5)

        self.m_buttonStopRec = wx.Button(self, wx.ID_ANY, u"Finalizar grabacion", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_buttonStopRec.SetBackgroundColour(wx.Colour(255, 87, 74))  # Red background

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

        self.m_buttonExit = wx.Button(self, wx.ID_ANY, u"Salir!", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizerVertical.Add(self.m_buttonExit, 0, wx.ALL, 5)

        self.SetSizer(bSizerVertical)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.m_textCtrlFilename.Bind(wx.EVT_KILL_FOCUS, self.onAudioNameUpdate)
        self.m_buttonStartRec.Bind(wx.EVT_BUTTON, self.onStartRec)
        self.m_buttonPauseRec.Bind(wx.EVT_BUTTON, self.onPauseRec)
        self.m_buttonStopRec.Bind(wx.EVT_BUTTON, self.onStopRec)
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

    # Virtual event handlers, override them in your derived class
    def onAudioNameUpdate(self, event):
        event.Skip()

    def onStartRec(self, event):
        event.Skip()

    def onPauseRec(self, event):
        event.Skip()

    def onStopRec(self, event):
        event.Skip()

    def onFrameExit(self, event):
        event.Skip()
