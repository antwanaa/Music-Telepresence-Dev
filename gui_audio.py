import wave
import numpy as np
import pyaudio
import threading

from gui import GUI
from make_binaural import binauralAudio

debug = False

CHUNK = 1024

def audio_playback():
    binaural = binauralAudio(debug)

    if debug:
        print('Now we can continue running code while mainloop runs!')

    with wave.open('Samples 48k/Buddy2.wav', 'rb') as wf:
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=44100,
                        output=True)

        while len(data := wf.readframes(CHUNK)):
            data_np = np.frombuffer(data, dtype=np.int16)
            norm = np.iinfo(data_np.dtype).max + 1.0
            data_np = data_np.astype(np.float32) / norm
            data_np = np.reshape(data_np, (2, -1), order='F')
            data_np2 = data_np.copy()

            if debug:
                print(gui.horAngle.get())

            try:
                data_np2 = binaural.make_binaural(data_np2, gui.horAngle.get(), gui.vertAngle.get(),
                                                  gui.hrtfSelector.get())
            except RuntimeError:
                exit("==================\n| GUI was closed |\n==================")

            if debug:
                print(np.max(np.abs(data_np2)))

            data_to_send = data_np2.flatten(order='F')
            if debug:
                print('data to send:')
            if debug:
                print(data_to_send)
            if debug:
                print(data_np2.shape, ' => ', data_to_send.shape)
            stream.write(data_to_send.tobytes())

        stream.close()
        del data
        p.terminate()
        gui.callback()

def run_gui():
    gui.root.mainloop()


# Start the Graphical User Interface
gui = GUI()

# Start audio processing and playback in a separate thread
threading.Thread(target=audio_playback).start()

# Run the GUI mainloop in the main thread
gui.root.mainloop()