Initial version

---------------------------
For exe creation:
> pyinstaller --windowed --noconfirm --icon=grabadora.ico --add-data="grabadora.ico;." grabadora.py
-----------------------------------------------------------------

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
  
