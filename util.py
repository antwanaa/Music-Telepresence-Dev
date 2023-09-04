import numpy as np
from scipy.io import wavfile

def load_audio(fpath):
    sr, data = wavfile.read(fpath)

    # If data is an int array, normalize to [-1, 1].
    if np.issubdtype(data.dtype, np.integer):
        norm = np.iinfo(data.dtype).max + 1.0
        data = data.astype(np.float32) / norm

    return data, sr