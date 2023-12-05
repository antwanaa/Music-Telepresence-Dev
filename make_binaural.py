import numpy as np
import librosa
import glob

# Directories
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

# TODO: when loading the HRTF, compute the FFT so that we do not need to compute it every iteration

class binauralAudio:
    def __init__(self, debug_state):
        # global previousHRTF
        global sliding_window_left
        global sliding_window_right
        global debug

        debug = debug_state

        # Storing the previous HRTF index (used for fading between HRTFs)
        self.previousHRTF = ''

        # Create the dictionaries mapping angles to the corresponding HRTF given a dataset
        make_dictionaries()


    # Given an audio stream, a horizontal and vertical angle, and the HRTF dataset 
    # of choice, returns a binaural rendering of the audio stream.
    def make_binaural(self, audio_data: np.ndarray[np.float32], horizontal_angle: int, vertical_angle: int, hrtf_set: str) -> np.ndarray[np.float32]:
        global sliding_window_left
        global sliding_window_right
        
        # Convert the angles set by the sliders to angles in the coordinates 
        # used for each dataset (each use different coordinates). Once done, 
        # select the corresponding HRTF file to use and store it in hrtf_name.
        if hrtf_set == "MIT":
            # The MIT dataset only provides "half a sphere" of HRTFs. In order to 
            # obtain the other half, we invert the left and right channels.
            hrtf_invert = False
            if horizontal_angle < 0:
                horizontal_angle = -horizontal_angle
                hrtf_invert = True

            vert_ang = min(database_MIT.keys(), key=lambda x:abs(x-vertical_angle))
            if debug: print("MIT - vertical angle: ", vert_ang)
            hor_ang = min(database_MIT[vert_ang], key=lambda x:abs(x-horizontal_angle))
            if debug: print("MIT - horizontal angle: ", hor_ang)

            hor_ang_str = str(hor_ang).rjust(3, "0")
            # hrtf_name = 'HRTFsets/MIT/diffuse/elev' + str(vert_ang) + '\H' + str(vert_ang) + 'e' + hor_ang_str + 'a.wav'
            key = "MIT_e" + str(vert_ang) + "_h" + hor_ang_str
            hrtf_name = key

            if debug: print("concatenated hrtf: ", hrtf_name)
        
        elif hrtf_set == "LISTEN":
            hrtf_invert = False     # No need to invert the HRTF with this dataset

            vert_ang = (vertical_angle + 360)%360
            vert_ang = min(database_LISTEN.keys(), key=lambda x:abs(x-vert_ang))
            if debug: print("LISTEN - vertical angle: ", vert_ang)

            hor_ang = (-horizontal_angle + 360)%360
            hor_ang = min(database_LISTEN[vert_ang], key=lambda x:abs(x-hor_ang))
            if debug: print("LISTEN - horizontal angle: ", hor_ang)

            hor_ang_str = str(hor_ang).rjust(3, "0")
            vert_ang_str = str(vert_ang).rjust(3, "0")
            hrtf_name = "HRTFsets/LISTEN/IRC_1025/COMPENSATED/WAV/IRC_1025_C/IRC_1025_C_R0195_T" + hor_ang_str + "_P" + vert_ang_str + ".wav"

            hrtf_name = "LISTEN_e" + vert_ang_str + "_h" + hor_ang_str

        elif hrtf_set == "SOFA":
            hrtf_name = ""
            print("to implement")
        
        else:
            raise AttributeError("Incorrect HRTF set selected.")

        
        # If the HRTF used for the previous block is the same as for the current block, then 
        # we do not need to implement the fading technique between two HRTFs. Similarly, if we 
        # are starting the stream then there is no previous HRTF and we do not need to "fade".
        if self.previousHRTF == hrtf_name or self.previousHRTF == '':

            # Load the HRTF based on given filename
            if hrtf_set == "MIT" or hrtf_set == "LISTEN":
                HRIR_0 = hrtfs_dictionary[hrtf_name]
            else:
                HRIR_0, fs_H0 = librosa.load(hrtf_name,sr=44100,mono=False)

            if not hrtf_invert:
                s_0_L = convolveLeft(audio_data[0,:], HRIR_0[0,:])     # Convolve the left signal
                s_0_R = convolveRight(audio_data[1,:], HRIR_0[1,:])    # Convolve the right signal
            else:   # invert the channels of the HRIR
                s_0_L = convolveLeft(audio_data[0,:], HRIR_0[1,:])     # Convolve the left signal
                s_0_R = convolveRight(audio_data[1,:], HRIR_0[0,:])    # Convolve the right signal

            # Combine the LEFT and RIGHT signals in a way that the audio stream expects
            # Bin_Mix = np.vstack([s_0_L[0:audio_data.shape[1]].astype(np.int16),s_0_R[0:audio_data.shape[1]].astype(np.int16)])
            Bin_Mix = np.vstack([s_0_L[0:audio_data.shape[1]],s_0_R[0:audio_data.shape[1]]])
            if debug: print(np.max(Bin_Mix))
        else:
            # Load the HRTF for the old and new angle
            if hrtf_set == "MIT" or hrtf_set == "LISTEN":
                HRIR_0 = hrtfs_dictionary[self.previousHRTF]
                HRIR_1 = hrtfs_dictionary[hrtf_name]
            else:
                HRIR_0, fs_H0 = librosa.load(self.previousHRTF,sr=44100,mono=False)
                HRIR_1, fs_H0 = librosa.load(hrtf_name,sr=44100,mono=False)

            if not hrtf_invert:
                temp = sliding_window_left                          # Save the sliding window to "reuse it" for the new HRIR
                s_0_L = convolveLeft(audio_data[0,:], HRIR_0[0,:])  # Convolve the left signal
                sliding_window_left = temp                          # Reinstate the sliding window after its use
                s_1_L = convolveLeft(audio_data[0,:], HRIR_1[0,:])  # Convolve the left signal

                temp = sliding_window_right                         # Save the sliding window to "reuse it" for the new HRIR
                s_0_R = convolveRight(audio_data[1,:], HRIR_0[1,:]) # Convolve the right signal
                sliding_window_right = temp                         # Reinstate the sliding window after its use
                s_1_R = convolveRight(audio_data[1,:], HRIR_1[1,:]) # Convolve the right signal

                # Create amplitude envelopes to fade from one HRTF to the next using sin^2
                n = np.arange(0, len(s_0_L))
                f_in = np.sin(0.5*n/max(n)*np.pi)
                f_in = f_in**2
                f_out = 1-f_in

                # Apply the fading from one HRTF to the new one on both L and R channels
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

            # Combine the LEFT and RIGHT signals in a way that the audio stream expects
            # Bin_Mix = np.vstack([s_out_L[0:audio_data.shape[1]].astype(np.int16),s_out_R[0:audio_data.shape[1]].astype(np.int16)])
            Bin_Mix = np.vstack([s_out_L[0:audio_data.shape[1]],s_out_R[0:audio_data.shape[1]]])
        self.previousHRTF = hrtf_name
        return Bin_Mix

# Function responsible for convolving the left channel
def convolveLeft(signal: np.ndarray[np.float32], hrtf: np.ndarray[np.float32]) -> np.ndarray[np.float32]:
    k = len(signal) + len(hrtf) - 1
    hrtf_padded = np.pad(hrtf, (0,k-len(hrtf)))
    global sliding_window_left
    if(len(sliding_window_left) != k):
        sliding_window_left = np.zeros(k)
        if debug: print("REINITIALIZING THE LEFT SLIDING WINDOW")
    sliding_window_left = np.delete(sliding_window_left, np.s_[0:len(signal)])
    sliding_window_left = np.append(sliding_window_left, signal)
    signal_ft = np.fft.fftn(sliding_window_left)
    hrtf_ft = np.fft.fftn(hrtf_padded)
    sig = np.multiply(signal_ft, hrtf_ft)
    inv_ft = np.fft.ifftn(sig)
    valid_samples = np.real(inv_ft[len(inv_ft)-len(signal):])
    # print(valid_samples)

    return valid_samples

# Function responsible for convolving the right channel
def convolveRight(signal: np.ndarray[np.float32], hrtf: np.ndarray[np.float32]) -> np.ndarray[np.float32]:
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
    valid_samples = np.real(inv_ft[len(inv_ft)-len(signal):])

    return valid_samples

# Function that creates the dictionaries mapping the directions to corresponding HRTFs for all HRTF datasets
def make_dictionaries():
    # Create a dictionary with all the HRTF provided by the database_MIT. key:value <=> elevation:horizontal_angle
    global database_MIT
    global database_LISTEN
    global hrtfs_dictionary

    hrtfs_dictionary = {}   # Dictionary whose keys are angles, and values are HRIR. Format: DATABASE_eXXX_hYYY

    hrtf2_dir_MIT = 'HRTFsets/MIT/diffuse/*/*.wav'
    lst = glob.glob(hrtf2_dir_MIT)
    database_MIT = {}
    for elem in lst:
        item = elem[elem.index('H', 22)+1:len(elem)-5] # Only keep the relevant characters of the filename in the list for easier processing
        
        # If the elevation is not yet a key, create it and assign the horizontal angle as a value
        if(database_MIT.get(int(item[:item.index('e')])) == None):  
            database_MIT[int(item[:item.index('e')])] = [int(item[item.index('e')+1:])]
            
            HRIR_5, fs_H0 = librosa.load(elem,sr=44100,mono=False)
            key1 = "MIT_e" + item[:item.index('e')] + "_h" + item[item.index('e')+1:]
            hrtfs_dictionary[key1] = HRIR_5
        
        # If the elevation is already a key, add the horizontal angle to the list of values
        else:
            database_MIT[int(item[:item.index('e')])].append(int(item[item.index('e')+1:]))

            HRIR_5, fs_H0 = librosa.load(elem,sr=44100,mono=False)
            key1 = "MIT_e" + item[:item.index('e')] + "_h" + item[item.index('e')+1:]
            hrtfs_dictionary[key1] = HRIR_5
    if debug : print(database_MIT)



    # Create a dictionary with all the HRTF provided by the database_LISTEN. key:value <=> elevation:horizontal_angle
    lst = glob.glob(hrtf_dir_LISTEN)
    database_LISTEN = {}
    for elem in lst:
        item = elem[elem.index('T', 60)+1:len(elem)-4] # Only keep the relevant characters of the filename in the list for easier processing
        if(database_LISTEN.get(int(item[item.index('P')+1:])) == None):
            database_LISTEN[int(item[item.index('P')+1:])] = [int(item[:item.index('_')])]

            HRIR_5, fs_H0 = librosa.load(elem,sr=44100,mono=False)
            key1 = "LISTEN_e" + item[item.index('P')+1:] + "_h" + item[:item.index('_')]
            hrtfs_dictionary[key1] = HRIR_5
        else:
            database_LISTEN[int(item[item.index('P')+1:])].append(int(item[:item.index('_')]))

            HRIR_5, fs_H0 = librosa.load(elem,sr=44100,mono=False)
            key1 = "LISTEN_e" + item[item.index('P')+1:] + "_h" + item[:item.index('_')]
            hrtfs_dictionary[key1] = HRIR_5
    if debug : print(database_LISTEN)      