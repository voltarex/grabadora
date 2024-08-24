# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Jun 17 2015)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc


###########################################################################
## Class GrabadoraGUIFrame
###########################################################################

class GrabadoraGUIFrame(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"Grabadora", pos=wx.DefaultPosition,
                          size=wx.Size(500, 273), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)

        bSizerVertical = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText1 = wx.StaticText(self, wx.ID_ANY, u"Modificar el nombre del audio", wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        self.m_staticText1.Wrap(-1)
        bSizerVertical.Add(self.m_staticText1, 0, wx.ALL | wx.EXPAND, 5)

        self.m_textCtrl1 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        bSizerVertical.Add(self.m_textCtrl1, 0, wx.ALL | wx.EXPAND, 5)

        bSizerHorizontal = wx.BoxSizer(wx.HORIZONTAL)

        self.m_buttonStartRec = wx.Button(self, wx.ID_ANY, u"Comenzar grabacion", wx.Point(-1, -1), wx.DefaultSize, 0)
        bSizerHorizontal.Add(self.m_buttonStartRec, 1, 0, 5)

        self.m_buttonStopRec = wx.Button(self, wx.ID_ANY, u"Finalizar grabacion", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizerHorizontal.Add(self.m_buttonStopRec, 1, 0, 5)

        bSizerVertical.Add(bSizerHorizontal, 1, wx.EXPAND, 5)

        self.SetSizer(bSizerVertical)
        self.Layout()

        self.Centre(wx.BOTH)

    def __del__(self):
        pass


