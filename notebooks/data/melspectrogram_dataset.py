import os
import torch
import random 
import librosa
import numpy as np

from torch.utils.data import Dataset
from scipy.io import wavfile
from sklearn.preprocessing import MinMaxScaler

class MelSpectrogramDataset(Dataset):
    """ MelSpectrogram dataset """
    def __init__(self, filenames, hives, nfft, hop_len, mels):
        """ Constructor for MelSepctrogram Dataset

        Parameters:
            filenames (list): list of strings with filenames
            hives (list): list of strings with hive names as it will server as lables
            nfft (int): how many samples for nfft
            hop_len (int): overlapping, samples for hop to next fft
            mels (int): mels
            fmax (int): constraint on maximum frequency
        """
        self.files = filenames
        self.labels = hives
        self.nfft = nfft
        self.hop_len = hop_len
        self.mels = mels

    def __getitem__(self, idx):
        """ Wrapper for getting item from Spectrogram dataset """
        filename = self.files[idx]
        sampling_rate, sound_samples = wavfile.read(filename)
        hive_name = filename.split(os.sep)[-2].split("_")[0]
        label = next(index for index, name in enumerate(self.labels) if name == hive_name) if self.labels else 0
        if len(sound_samples.shape) > 1:
            # 2-channel recording
            sound_samples = sound_samples.T[0]
        sound_samples = sound_samples/(2.0**31)

        mel = librosa.feature.melspectrogram(y=sound_samples, sr=sampling_rate, \
                                             n_fft=self.nfft, hop_length=self.hop_len, n_mels=self.mels)
        mel = librosa.power_to_db(mel, np.max)
        
        initial_shape = mel.shape
        mel_scaled_spectrogram_db = MinMaxScaler().fit_transform(mel.reshape(-1, 1)).reshape((1, *initial_shape))
        mel_scaled_spectrogram_db = mel_scaled_spectrogram_db.astype(np.float32)

        return (mel_scaled_spectrogram_db, label)
 
    def __len__(self):
        return len(self.files)

    def sample(self, idx=None):
        """ Function for sampling dataset 
        
        Parameters:
            idx (int): sample idx
        Returns:
            (spectrogram_db, freqs, time)
        """
        if not idx:
            idx = random.uniform(0, len(self.files))
        return self.__getitem__(idx)
        