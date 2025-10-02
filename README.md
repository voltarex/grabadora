Initial version

---------------------------
For exe creation:
> pyinstaller --windowed --noconfirm --icon=grabadora.ico --add-data="grabadora.ico;." grabadora.py
-----------------------------------------------------------------

- V2.2 updates:
  - moved logfile location to user working directory
  - fixed mp3 file wrong location
  - changed conversion dialog box to non-modal to keep the main GUI responsive (although no action is allowed)
  - better error handling in onStopRec()
  - added a checker for a valid filename
- V2.1: Added a progress dialog box while converting from wav to mp3. Not really showing progress,
  but at least shows that conversion is ongoing
- v2.0 updates:
  - Created two PyAudio streams, one for monitoring (mic to headset) and one for recording to file (mic to file). This
    way can monitor incoming audio without recording
  - Updated gain to 2.0 by default
  - Added comments to each method
  - Added source files headers and license
  - Changed timer mechanism, not relaying anymore on 100ms intervals but rather on time.monotonic()
  
- v1.13 updates:
  Filename cannot be changed and textbox is disabled while recording
  Audio stream keeps flowing in pause state, although not recorded in output file
  Changed default gain to 20 
  
