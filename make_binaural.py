import glob
import numpy as np
from util import load_audio

# Directories (specific for my computer)
source_dir = 'Samples 48k/*.wav'
hrtf_dir_MIT = 'HRTFsets/MIT/diffuse/elev0/*.wav'
hrtf_dir_LISTEN = 'HRTFsets/LISTEN/IRC_1025/COMPENSATED/WAV/IRC_1025_C/*.wav'
hrtf_dir_SOFA = 'HRTFsets/SOFA Far-Field/*.sofa'

# Parse contents of 4 different HRTF database_MITs:
_SOURCES = glob.glob(source_dir)
_MIT = glob.glob(hrtf_dir_MIT)
_LISTEN = glob.glob(hrtf_dir_LISTEN)
_SOFA = glob.glob(hrtf_dir_SOFA)

# Initializing sliding windows that will be resized depending on the block length
sliding_window_left = np.zeros(10)
sliding_window_right = np.zeros(10)



class binauralAudio:
    def __init__(self, debug_state):
        # global previousHRTF
        global sliding_window_left
        global sliding_window_right
        global debug

        debug = debug_state

        # Storing the previous HRTF index (used for fading between HRTFs)
        self.previousHRTF = ''

        make_dictionaries()


    
    def make_binaural(self, audio_data, horizontal_angle, vertical_angle, hrtf_set):
    # def make_binaural(audio_data, index):
        # global previousHRTF
        global sliding_window_left
        global sliding_window_right
        
        # Convert the angles set by the sliders to angles in the coordinates used for each dataset (each use different coordinates)
        if hrtf_set == "MIT":
            hrtf_invert = False
            if horizontal_angle < 0:
                horizontal_angle = -horizontal_angle
                hrtf_invert = True

            vert_ang = min(database_MIT.keys(), key=lambda x:abs(x-vertical_angle))
            if debug: print("MIT - vertical angle: ", vert_ang)
            hor_ang = min(database_MIT[vert_ang], key=lambda x:abs(x-horizontal_angle))
            if debug: print("MIT - horizontal angle: ", hor_ang)

            padding = str(hor_ang).rjust(3, "0")
            hrtf_name = 'HRTFsets/MIT/diffuse/elev' + str(vert_ang) + '/H' + str(vert_ang) + 'e' + padding + 'a.wav'
            # FILES = glob.glob(hrtf_name)
            # print(FILES)
            if debug: print("concatenated hrtf: ", hrtf_name)
        
        elif hrtf_set == "LISTEN":
            hrtf_invert = False # no need to invert the HRTF with this dataset

            vert_ang = (vertical_angle + 360)%360
            vert_ang = min(database_LISTEN.keys(), key=lambda x:abs(x-vert_ang))
            if debug: print("LISTEN - vertical angle: ", vert_ang)

            hor_ang = (-horizontal_angle + 360)%360
            hor_ang = min(database_LISTEN[vert_ang], key=lambda x:abs(x-hor_ang))
            if debug: print("LISTEN - horizontal angle: ", hor_ang)

            padding = str(hor_ang).rjust(3, "0")
            padding2 = str(vert_ang).rjust(3, "0")
            hrtf_name = "HRTFsets/LISTEN/IRC_1025/COMPENSATED/WAV/IRC_1025_C/IRC_1025_C_R0195_T" + padding + "_P" + padding2 + ".wav"


        elif hrtf_set == "SOFA":
            hrtf_name = ""
            print("to implement")
        
        else:
            raise AttributeError("Incorrect HRTF set selected.")

        

        if self.previousHRTF == hrtf_name or self.previousHRTF == '':

            # Load the HRTF based on angle given
            # HRIR_0, fs_H0 = librosa.load(_LISTEN[index],sr=48000,mono=False)
            HRIR_0, fs_H0 = load_audio(hrtf_name)

            # s_0_L = signal.fftconvolve(audio_data[0,:].T,HRIR_0[0,:], mode='full') # spatialized source 0 LEFT
            # s_0_R = signal.fftconvolve(audio_data[1,:].T,HRIR_0[1,:], mode='full') # spatialized source 0 RIGHT
            if not hrtf_invert:
                s_0_L = convolveLeft(audio_data[0,:], HRIR_0.T[0,:])     # Convolve the left signal
                s_0_R = convolveRight(audio_data[1,:], HRIR_0.T[1,:])    # Convolve the right signal
            else:   # invert the channels of the HRIR
                s_0_L = convolveLeft(audio_data[0,:], HRIR_0.T[1,:])     # Convolve the left signal
                s_0_R = convolveRight(audio_data[1,:], HRIR_0.T[0,:])    # Convolve the right signal

            s_0_L *= np.iinfo(np.int16).max + 1.0
            s_0_R *= np.iinfo(np.int16).max + 1.0

            # Combine the LEFT and RIGHT signals in a way that the audio stream expects
            Bin_Mix = np.vstack([s_0_L[0:audio_data.shape[1]].astype(np.int16),s_0_R[0:audio_data.shape[1]].astype(np.int16)])
            if debug: print(np.max(Bin_Mix))
            # return Bin_Mix
        else:
            # Load the HRTF for the old and new angle
            # HRIR_0, fs_H0 = librosa.load(_LISTEN[previousIndex],sr=48000,mono=False)
            # HRIR_1, fs_H0 = librosa.load(_LISTEN[index],sr=48000,mono=False)
            HRIR_0, fs_H0 = load_audio(self.previousHRTF)
            HRIR_1, fs_H0 = load_audio(hrtf_name)

            if not hrtf_invert:
                temp = sliding_window_left
                s_0_L = convolveLeft(audio_data[0,:], HRIR_0[0,:])     # Convolve the left signal
                sliding_window_left = temp
                s_1_L = convolveLeft(audio_data[0,:], HRIR_1[0,:])     # Convolve the left signal

                temp = sliding_window_right
                s_0_R = convolveRight(audio_data[1,:], HRIR_0[1,:])    # Convolve the right signal
                sliding_window_right = temp
                s_1_R = convolveRight(audio_data[1,:], HRIR_1[1,:])    # Convolve the right signal

                # Create amplitude envelopes to fade from one HRTF to the next using sin^2
                n = np.arange(0, len(s_0_L))
                f_in = np.sin(0.5*n/max(n)*np.pi)
                f_in = f_in**2
                f_out = 1-f_in

                s_out_L = s_0_L*f_out + s_1_L*f_in
                s_out_R = s_0_R*f_out + s_1_R*f_in

            
            else:   # invert the channels of the HRIR
                temp = sliding_window_left
                s_0_L = convolveLeft(audio_data[0,:], HRIR_0[1,:])     # Convolve the left signal
                sliding_window_left = temp
                s_1_L = convolveLeft(audio_data[0,:], HRIR_1[1,:])     # Convolve the left signal

                temp = sliding_window_right
                s_0_R = convolveRight(audio_data[1,:], HRIR_0[0,:])    # Convolve the right signal
                sliding_window_right = temp
                s_1_R = convolveRight(audio_data[1,:], HRIR_1[0,:])    # Convolve the right signal

                # Amplitude envelopes to fade from one HRTF to the next
                n = np.arange(0, len(s_0_L))
                f_in = np.sin(0.5*n/max(n)*np.pi)
                f_in = f_in**2
                f_out = 1-f_in

                s_out_L = s_0_L*f_out + s_1_L*f_in
                s_out_R = s_0_R*f_out + s_1_R*f_in

            s_out_L *= np.iinfo(np.int16).max + 1.0
            s_out_R *= np.iinfo(np.int16).max + 1.0
            

            # Combine the LEFT and RIGHT signals in a way that the audio stream expects
            Bin_Mix = np.vstack([s_out_L[0:audio_data.shape[1]].astype(np.int16),s_out_R[0:audio_data.shape[1]].astype(np.int16)])
        self.previousHRTF = hrtf_name
        return Bin_Mix

# Function responsible for convolving the left channel
def convolveLeft(signal, hrtf):
    k = len(signal) + len(hrtf) - 1
    hrtf_padded = np.pad(hrtf, (0,k-len(hrtf)))
    global sliding_window_left
    if(len(sliding_window_left) != k):
        sliding_window_left = np.zeros(k)
        if debug: print("REINITIALIZING THE LEFT SLIDING WINDOW")
    # print(sliding_window_left)
    sliding_window_left = np.delete(sliding_window_left, np.s_[0:len(signal)])
    # print(sliding_window_left.shape)
    sliding_window_left = np.append(sliding_window_left, signal)
    # print(sliding_window_left.shape)
    signal_ft = np.fft.fftn(sliding_window_left)
    hrtf_ft = np.fft.fftn(hrtf_padded)
    sig = np.multiply(signal_ft, hrtf_ft)
    inv_ft = np.fft.ifftn(sig)
    # valid_samples = inv_ft[len(inv_ft)-len(signal):]
    # print('length: ',len(inv_ft), len(signal), len(inv_ft)-len(signal))
    valid_samples = np.real(inv_ft[len(inv_ft)-len(signal):])

    return valid_samples

# Function responsible for convolving the right channel
def convolveRight(signal, hrtf):
    k = len(signal) + len(hrtf) - 1
    hrtf_padded = np.pad(hrtf, (0,k-len(hrtf)))
    global sliding_window_right
    if(len(sliding_window_right) != k):
        sliding_window_right = np.zeros(k)
        if debug: print("REINITIALIZING THE RIGHT SLIDING WINDOW")
    sliding_window_right = np.delete(sliding_window_right, np.s_[0:len(signal)])
    sliding_window_right = np.append(sliding_window_right, signal)
    signal_ft = np.fft.fftn(sliding_window_right)
    hrtf_ft = np.fft.fftn(hrtf_padded)
    sig = np.multiply(signal_ft, hrtf_ft)
    inv_ft = np.fft.ifftn(sig)
    # valid_samples = inv_ft[len(inv_ft)-len(signal):]
    # print('length: ',len(inv_ft), len(signal), len(inv_ft)-len(signal))
    valid_samples = np.real(inv_ft[len(inv_ft)-len(signal):])

    return valid_samples

# Function that creates the dictionaries mapping the directions to corresponding HRTFs for all HRTF datasets
def make_dictionaries():
    # Create a dictionary with all the HRTF provided by the database_MIT. key:value <=> elevation:horizontal_angle
    global database_MIT
    global database_LISTEN

    hrtf2_dir_MIT = 'HRTFsets/MIT/diffuse/*/*.wav'
    lst = glob.glob(hrtf2_dir_MIT)
    lst[:] = (elem[elem.index('H', 22)+1:len(elem)-5] for elem in lst) # Only keep the relevant characters of the filename in the list for easier processing
    database_MIT = {}
    for elem in lst:
        if(database_MIT.get(int(elem[:elem.index('e')])) == None):
            database_MIT[int(elem[:elem.index('e')])] = [int(elem[elem.index('e')+1:])]
        else:
            database_MIT[int(elem[:elem.index('e')])].append(int(elem[elem.index('e')+1:]))
    if debug : print(database_MIT)
    # print(lst)

    # Create a dictionary with all the HRTF provided by the database_LISTEN. key:value <=> elevation:horizontal_angle
    lst = glob.glob(hrtf_dir_LISTEN)
    if debug: print(lst)
    lst[:] = (elem[elem.index('T', 60)+1:len(elem)-4] for elem in lst) # Only keep the relevant characters of the filename in the list for easier processing
    if debug: print(lst)
    database_LISTEN = {}
    for elem in lst:
        if(database_LISTEN.get(int(elem[elem.index('P')+1:])) == None):
            database_LISTEN[int(elem[elem.index('P')+1:])] = [int(elem[:elem.index('_')])]
        else:
            database_LISTEN[int(elem[elem.index('P')+1:])].append(int(elem[:elem.index('_')]))
    if debug : print(database_LISTEN)      