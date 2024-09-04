Initial version

---------------------------
For exe creation:
> pyinstaller --windowed --icon=grabadora.ico --add-data="grabadora.ico;." grabadora.py
-----------------------------------------------------------------

- 28.08.24 - About flaws using an event handler with a while loop:
The issue you're encountering with the unresponsive GUI is due to the nature of how wxPython processes events. When you run an endless loop (like a while loop) inside an event handler, it blocks the main event loop, preventing wxPython from processing other events (like user interactions with buttons or even a stop signal).
Key Points:

    Blocking the Event Loop: The while loop inside the run_loop method is blocking wxPython’s event loop, so the interface freezes and can't handle the stop event.
    wx.Yield() Issue: Although wx.Yield() processes pending events, it’s not sufficient to make the GUI responsive because it's called within the same event handler that's holding the loop, creating a bottleneck.

Solution:

To prevent the GUI from freezing, you should avoid blocking the main event loop. The best approach is to use a background task or asynchronous event handling. wxPython provides some tools for this, including wx.Timer and wx.CallLater, or you can use threading or the wx.FutureCall method.


Solution:

To prevent the GUI from freezing, you should avoid blocking the main event loop. The best approach is to use a background task or asynchronous event handling. wxPython provides some tools for this, including wx.Timer and wx.CallLater, or you can use threading or the wx.FutureCall method.
Using wx.Timer Example:

A wx.Timer can be used to periodically check for events without freezing the GUI. Here’s an example of how you might implement this.

python

import wx

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create buttons
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.start_button = wx.Button(panel, label="Start")
        self.stop_button = wx.Button(panel, label="Stop")
        sizer.Add(self.start_button, 0, wx.ALL, 5)
        sizer.Add(self.stop_button, 0, wx.ALL, 5)
        panel.SetSizer(sizer)

        # Bind button events
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start)
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop)

        # Timer for running the loop
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.run_loop, self.timer)

        # Variables for loop control
        self.running = False

    def on_start(self, event):
        self.running = True
        self.timer.Start(100)  # Run loop every 100ms

    def on_stop(self, event):
        self.running = False
        self.timer.Stop()

    def run_loop(self, event):
        if self.running:
            print("Loop running...")
            # Do your work here
        else:
            print("Loop stopped.")

app = wx.App(False)
frame = MyFrame(None, title="Timer-based Event Loop")
frame.Show()
app.MainLoop()

Explanation:

    Start and Stop Buttons: Clicking the "Start" button starts the loop by setting self.running = True and starting a wx.Timer. The "Stop" button stops the loop by setting self.running = False and stopping the timer.
    Non-blocking Loop: The wx.Timer triggers the run_loop method at a regular interval (every 100 milliseconds in this case). This approach keeps the main event loop free, allowing the GUI to remain responsive.
    Stopping the Loop: When the "Stop" button is clicked, the loop stops cleanly without blocking the event handling for other GUI interactions.

Alternative Approaches:

    wx.CallLater or wx.FutureCall: These are similar to wx.Timer, but they execute a method after a set delay without blocking the main event loop. This can be useful for asynchronous tasks.
    Threading: For more complex or long-running operations, you might consider using Python’s threading module. However, you need to be cautious with threading and wxPython, as wxPython isn't thread-safe. You would need to use thread-safe mechanisms like wx.CallAfter to update the GUI from a background thread.

Example with wx.CallLater:

python

import wx

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create buttons
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.start_button = wx.Button(panel, label="Start")
        self.stop_button = wx.Button(panel, label="Stop")
        sizer.Add(self.start_button, 0, wx.ALL, 5)
        sizer.Add(self.stop_button, 0, wx.ALL, 5)
        panel.SetSizer(sizer)

        # Bind button events
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start)
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop)

        # Variables for loop control
        self.running = False

    def on_start(self, event):
        self.running = True
        self.run_loop()

    def on_stop(self, event):
        self.running = False

    def run_loop(self):
        if self.running:
            print("Loop running...")
            # Do your work here
            wx.CallLater(100, self.run_loop)  # Call the loop again after 100ms

app = wx.App(False)
frame = MyFrame(None, title="CallLater-based Event Loop")
frame.Show()
app.MainLoop()

Explanation:

    wx.CallLater(100, self.run_loop) calls the loop function after 100ms without blocking the main thread. This ensures that the GUI remains responsive while the loop continues to run asynchronously.

Both wx.Timer and wx.CallLater are non-blocking and help keep the GUI responsive.

