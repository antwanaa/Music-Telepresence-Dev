import numpy as np
import librosa
import glob
import math

# Directory
source_dir = 'Impulse Response Database/AIR_1_4/AIR_wav_files/*.wav'
_ROOMS = glob.glob(source_dir)

audio_data_history = np.zeros((0, 2, 1))    # History of the incoming audio blocks
audio_ft_history = np.zeros((0, 2, 1))      # History of the FFT of the incoming audio 
numOfBlocks = 0                             # Length of the room FIR in blocks
room_fir_blocks = np.zeros((0, 2, 1))       # Room FIR in blocks
room_fir_ft_blocks = np.zeros((0, 2, 1))    # FFT of the room FIR blocks
room_fir = np.zeros(10)                     # Room FIR as a stereo array
room_fir_str = ""                           # Name of the room FIR
output = np.zeros((2, 1))                   # Output at the end of the iteration
CHUNK_SIZE = 1024                           # Size of the CHUNKS, is changed by the length of the incoming audio



class roomColor:
    def __init__(self, debug_state) -> None:
        global debug
        debug = debug_state
        

    def colorize_room(self, audio_data: np.ndarray[np.float32], room: str) -> np.ndarray[np.float32]:
        global audio_data_history
        global audio_ft_history
        global output
        global room_fir_str
        global room_fir_blocks
        global room_fir_ft_blocks
        global room_fir
        global numOfBlocks
        global CHUNK_SIZE
        CHUNK_SIZE = len(audio_data[0,:])
        
        # if the chunk size for the audio history is not correct, reinitialize the array
        if(audio_data_history.shape[2] != CHUNK_SIZE):  
            audio_data_history = np.zeros((0, 2, CHUNK_SIZE))
            audio_ft_history = np.zeros((0, 2, 2*CHUNK_SIZE-1))

        # As audio comes in, save it.
        audio_data_history = np.concatenate((audio_data_history, [audio_data]))

        # Pre-compute the fft of the audio data and save it for later use
        temp = np.vstack((np.fft.fft(audio_data[0,:], 2*CHUNK_SIZE-1), 
                          np.fft.fft(audio_data[1,:], 2*CHUNK_SIZE-1)))
        audio_ft_history = np.concatenate((audio_ft_history, [temp]))

        # if the room impulse function is the same as the previous iteration
        # then do not load it from memory again, otherwise:
        if(room != room_fir_str):
            if debug: print(room)
            print(_ROOMS[int(room)])
            room_fir, fs_H0 = librosa.load(_ROOMS[int(room)],sr=44100,mono=False)  # Load the room FIR
            room_fir_str = room                                             # Save the name of the FIR
                       
            # If the room_fir is single channel, then make it stereo by copying the channel into both L and R
            if(len(room_fir.shape) == 1):
                room_fir = np.vstack((room_fir, room_fir))
            
            # Compute the length of the room FIR in number of CHUNK_SIZES
            numOfBlocks = math.ceil(len(room_fir[0,:])/len(audio_data[0]))

            
            # Initialize the array that contains the FIR in blocks
            room_fir_blocks = np.zeros((numOfBlocks, 2, CHUNK_SIZE))
            
            # Initialize the array that will contain the pre-computed FFT
            room_fir_ft_blocks = np.zeros_like(np.zeros((numOfBlocks, 2, 2*CHUNK_SIZE-1)), 
                                               dtype=np.complex128)
            
            for k in range(numOfBlocks):
                # Finally, save the room FIR in chunks to the array.
                temp = room_fir[:, k*CHUNK_SIZE:(k+1)*CHUNK_SIZE]
                room_fir_blocks[k, :, :] = np.pad(temp, ((0,0),(0, CHUNK_SIZE-len(temp[0]))))
                # Compute the FFT of each block of the room FIR and save it
                room_fir_ft_blocks[k, :, :] = np.vstack((
                    np.fft.fft(room_fir_blocks[k,0,:], 2*CHUNK_SIZE-1), 
                    np.fft.fft(room_fir_blocks[k,1,:], 2*CHUNK_SIZE-1)))

        # If the history of the audio saved is longer than the filter, we
        # can discard the earliest parts of the audio to free up some memory
        if(audio_data_history.shape[0] > numOfBlocks):
            audio_data_history = audio_data_history[1:, :, :]
            audio_ft_history = audio_ft_history[1:, :, :]
        
        # output is longer than what is to be returned, but the extra contains
        # important information to be used for the next chunk (Overlap-Add) so
        # we must save the extra to apply it to the next bloc
        if len(output[0]) <= 1:
            output = np.zeros((2, 2*CHUNK_SIZE-1))
        else:
            output = np.append(output, np.zeros((2, len(audio_data[0,:]))), axis = 1)
            output = np.delete(output, np.s_[0:len(audio_data[0,:])], axis = 1)
            
        
        if True:
            # Using pre-computed np.fft and multiply (Most efficient)
            for j in range(min(len(audio_data_history), numOfBlocks)):
                # For each BLOCK of the filter, multiply it with the corresponding
                # block of audio. Y(n) = H(0)X(n) + H(1)X(n-1) + H(2)X(n-2)...
                audio_l_ft = audio_ft_history[len(audio_data_history)-1-j, 0, :]
                room_fir_l_ft = room_fir_ft_blocks[j, 0, :]
                left_ft = np.multiply(audio_l_ft, room_fir_l_ft)
                left = np.real(np.fft.ifft(left_ft))

                audio_r_ft = audio_ft_history[len(audio_data_history)-1-j, 1, :]
                room_fir_r_ft = room_fir_ft_blocks[j, 1, :]
                right_ft = np.multiply(audio_r_ft, room_fir_r_ft)
                right = np.real(np.fft.ifft(right_ft))

                # Adding up the results
                output[0, :] += left
                output[1, :] += right

        elif False:
            # Computing np.fft and multiply at each loop
            for j in range(min(len(audio_data_history), numOfBlocks)):
                # For each BLOCK of the filter, multiply it with the corresponding
                # block of audio. Y(n) = H(0)X(n) + H(1)X(n-1) + H(2)X(n-2)...
                audio_l_ft = np.fft.fft(audio_data_history[len(audio_data_history)-1-j, 0, :], 2*CHUNK_SIZE-1)
                room_fir_l_ft = np.fft.fft(room_fir_blocks[j, 0, :], 2*CHUNK_SIZE-1)
                left_ft = np.multiply(audio_l_ft, room_fir_l_ft)
                left = np.real(np.fft.ifft(left_ft))

                audio_r_ft = np.fft.fft(audio_data_history[len(audio_data_history)-1-j, 1, :], 2*CHUNK_SIZE-1)
                room_fir_r_ft = np.fft.fft(room_fir_blocks[j, 1, :], 2*CHUNK_SIZE-1)
                right_ft = np.multiply(audio_r_ft, room_fir_r_ft)
                right = np.real(np.fft.ifft(right_ft))

                # Adding up the results
                output[0, :] += left
                output[1, :] += right
        
        else:
            # Using np.convolve
            for j in range(min(len(audio_data_history), numOfBlocks)):
                # For each BLOCK of the filter, convolving it with the corresponding
                # block of audio. y(n) = h(0)*x(n) + h(1)*x(n-1) + h(2)*x(n-2)...
                left = np.convolve(audio_data_history[len(audio_data_history)-1-j, 0, :], room_fir_blocks[j, 0, :])
                right = np.convolve(audio_data_history[len(audio_data_history)-1-j, 1, :], room_fir_blocks[j, 1, :])

                if(len(left) != 2*CHUNK_SIZE-1):
                    left = np.pad(left, (0, 2*CHUNK_SIZE-1-len(left)))
                    right = np.pad(right, (0, 2*CHUNK_SIZE-1-len(right)))
                    if debug: print("HAD TO PAD")

                # Adding up the results
                output[0, :] += left
                output[1, :] += right

        return output[:, 0:CHUNK_SIZE]
