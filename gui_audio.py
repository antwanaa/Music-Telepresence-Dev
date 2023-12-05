import wave
import numpy as np
import pyaudio

from gui import GUI
from make_binaural import binauralAudio
from room_color import roomColor


debug = False

CHUNK = 2048
# CHUNK = 16384


# Start the Graphical User Interface
gui = GUI()

# Create a binaural audio instance
binaural = binauralAudio(debug)

# Create a room colorization instance
room = roomColor(debug)


## Open an audio file
# with wave.open('Samples 48k\Audience Applause.wav', 'rb') as wf:
# with wave.open('Samples 48k\Car Horn, Monotone.wav', 'rb') as wf:
# with wave.open('Samples 48k\Peugeot_Exhaust.wav', 'rb') as wf:
with wave.open('Samples 48k\Buddy2.wav', 'rb') as wf:

    # Instantiate PyAudio and initialize PortAudio system resources
    p = pyaudio.PyAudio()

    # Open an audio stream
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    # rate=wf.getframerate(),
                    rate=44100,
                    output=True)

    # Play samples from the wave file
    while len(data := wf.readframes(CHUNK)):  # Requires Python 3.8+ for :=
        data_np = np.frombuffer(data, dtype=np.int16)
        data_np = (data_np*0.5).astype(np.int16) # divide by 2 to prevent clipping
        
        ## Process the array to make it easier to deal with
        # Row 0 = left channel 
        # Row 1 = right channel
        data_np = np.reshape(data_np, (2,-1), order='F')
        
        # Change the signal to a floating point array between -1 and 1 (same format used by librosa.load)
        # and to keep the convolution result under control
        data_np2 = (data_np/32768).astype(np.float32)


        ## Give the audio a "room color"
        if(gui.colorRoom.get()):
            data_np2 = room.colorize_room(data_np2, gui.firSelector.get())

        ## Make Binaural audio
        if(gui.useBin.get()):
            try:
                data_np2 = binaural.make_binaural(data_np2, 
                                                gui.horAngle.get(), 
                                                gui.vertAngle.get(), 
                                                gui.hrtfSelector.get())
            except RuntimeError:
                exit("==================\n| GUI was closed |\n==================")
       

        ## Repack the array after processing to send to the stream
        data_np2 = (data_np2*32768).astype(np.int16)
        data_to_send = data_np2.flatten(order='F')
        data_to_send = (data_to_send*1).astype(np.int16)
        if debug: 
            print("shape of data_np2: ", data_np2.shape, ' => shape of data_to_send: ', data_to_send.shape)
            print('data to send:')
            print(data_to_send)
        if(np.max(data_to_send) >= 32000*1):
            print(np.max(data_to_send), " ## TOO LOUD, CLIPPING ##")
        stream.write(data_to_send.tobytes())

    # Close stream
    stream.close()
    del data

    # Release PortAudio system resources
    p.terminate()
    # Close GUI
    gui.callback()


