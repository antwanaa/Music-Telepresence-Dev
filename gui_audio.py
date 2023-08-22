import wave
import numpy as np
import pyaudio

from gui import GUI
from make_binaural import binauralAudio


debug = False

CHUNK = 1024
# CHUNK = 16384


# Start the Graphical User Interface
gui = GUI()

# Create a binaural audio instance
binaural = binauralAudio(debug)

if debug: print('Now we can continue running code while mainloop runs!')


# with wave.open('Samples 48k\Audience Applause.wav', 'rb') as wf:
# with wave.open('Samples 48k\Car Horn, Monotone.wav', 'rb') as wf:
# with wave.open('Samples 48k\Peugeot_Exhaust.wav', 'rb') as wf:
with wave.open('Samples 48k\Buddy2.wav', 'rb') as wf:
# with wave.open(_LISTEN[27], 'rb') as wf:

    # Instantiate PyAudio and initialize PortAudio system resources
    p = pyaudio.PyAudio()

    # Open stream
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    # rate=wf.getframerate(),
                    rate=44100,
                    output=True)

    # Play samples from the wave file

    while len(data := wf.readframes(CHUNK)):  # Requires Python 3.8+ for :=
        data_np = np.frombuffer(data,dtype=np.int16)
        data_np = np.reshape(data_np, (2,-1), order='F')
        data_np2 = data_np.copy()

        if debug: print(gui.w2.get()) # Print slider value

        # Make Binaural audio
        try:
            data_np2 = binaural.make_binaural(data_np2, gui.horAngle.get(), gui.vertAngle.get(), gui.hrtfSelector.get())
        except RuntimeError:
            exit("==================\n| GUI was closed |\n==================")
        
        if debug: print(np.max(np.abs(data_np2)))

        data_to_send = data_np2.flatten(order='F')
        if debug: print('data to send:')
        if debug: print(data_to_send)
        # data_to_send = data_np2.flatten()
        if debug: print(data_np2.shape, ' => ', data_to_send.shape)
        # stream.write(data)
        stream.write(data_to_send.tobytes())

    # Close stream
    stream.close()
    del data

    # Release PortAudio system resources
    p.terminate()
    # Close GUI
    gui.callback()


