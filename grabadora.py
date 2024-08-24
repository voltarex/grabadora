import time
import sys
import wave
import datetime
import os
import threading
import wx

import pyaudio
from pydub import AudioSegment
from pynput import keyboard

import GrabadoraGUIFrame


class GUI(GrabadoraGUIFrame.GrabadoraGUIFrame):
    def __init__(self, parent):
        GrabadoraGUIFrame.GrabadoraGUIFrame.__init__(self, parent)

    # def FindSquare(self, event):
    #    num = int(self.m_textCtrl1.GetValue())
    #    self.m_textCtrl2.SetValue(str(num * num))

app = wx.App(False)
frame = GUI(None)
frame.Show(True)
#start the applications
app.MainLoop()

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

# Initialize volume factor (initially 1.0 for no adjustment)
volume_factor = 1.0

def callback(in_data, frame_count, time_info, status):
    # Adjust volume (multiply by 0.5 for 50% reduction)
    adjusted_data = bytearray(int(sample * volume_factor) for sample in in_data)


    # Process audio data for recording (e.g., write to a buffer)
    #output_wavefile.writeframes(in_data)  # Write data to the WAV file
    output_wavefile.writeframes(adjusted_data)  # Write data to the WAV file
    return in_data, pyaudio.paContinue

p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(2),
                channels=CHANNELS,
                rate=44100,
                input=True,
                output=True,
                stream_callback=callback)
                
# Create a WAV file with a unique filename based on date and time
now = datetime.datetime.now()

# Combine all arguments (if any) into a single string
arguments = "_".join(sys.argv[1:])  


output_filename = f"audio{'__' if arguments else ''}{arguments}__{now.strftime('%d-%m-%Y__%H-%M-%S')}.wav"
output_wavefile = wave.open(output_filename, 'wb')
output_wavefile.setnchannels(CHANNELS)
output_wavefile.setsampwidth(p.get_sample_size(FORMAT))
output_wavefile.setframerate(RATE)

# create a separate thread to capture user's volume input
volume_change_timer = None
volume_change_amount = 0

def start_volume_change(amount):
    global volume_change_timer, volume_change_amount
    volume_change_amount = amount
    volume_change_timer = threading.Timer(0.2, adjust_volume)
    volume_change_timer.start()

def adjust_volume():
    global volume_factor, volume_change_amount, volume_change_timer
    volume_factor = min(max(volume_factor + volume_change_amount, 0.1), 1.0)
    volume_change_amount = 0
    volume_change_timer = None


def on_press(key):
    global volume_change_timer
    try:
        k = key.char  # single-char keys
    except:
        k = key  # for special keys like ctrl, alt, etc.
    if k == '+':
        start_volume_change(0.1)
    elif k == '-':
        start_volume_change(-0.1)

def on_release(key):
    global volume_change_timer
    if volume_change_timer:
        volume_change_timer.cancel()
        volume_change_timer = None

def input_thread():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


# Start the input thread
input_thread = threading.Thread(target=input_thread)
input_thread.daemon = True
input_thread.start()
formatted_time = ''



try:
    # Record the start time
    start = time.time()
    print('* Grabando. Teclear <ctrl>+C para finalizar')
    print(' - Presione "+" para subir el volumen o "-" para bajarlo')
    
    while stream.is_active():
        elapsed_time = time.time() - start
        
        # Convert elapsed time to hours, minutes, and seconds
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format the time as HH:MM:SS
        formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        print(f"\r* Tiempo de grabacion: {formatted_time} (Volumen: {volume_factor:.2f})", end="", flush=True)
        
        time.sleep(0.1)
except KeyboardInterrupt:
    print()
    print("* Grabacion finalizada por el usuario.")
except Exception as e:  # Catch any other exceptions
    print(f"* Ocurrio un error inesperado: {e}")
    
# Record the end time
end = time.time()

print()  # Print a newline to avoid overwriting the last line
print(f"* Tiempo total de grabacion: {formatted_time}")

print('* Grabacion concluida, cerrando archivos...')
stream.close()
p.terminate()
output_wavefile.close()

# Read the WAV file
sound = AudioSegment.from_wav(output_filename)

# Split the filename at the last dot (.) to get the base name and extension
base, extension = output_filename.rsplit('.', 1)
mp3_filename = f"{base}.mp3"

# Export the sound as MP3
sound.export(mp3_filename, format="mp3")
print(f'* Grabacion guardada en el archivo: {mp3_filename}')

# Delete the original WAV file (use with caution)
try:
    os.remove(output_filename)
except FileNotFoundError:
    print(f"* Archivo WAV {output_filename} no se encontro. Nada sera borrado.")

# Wait for user input before closing
# input("* Oprima cualquier tecla para finalizar...")