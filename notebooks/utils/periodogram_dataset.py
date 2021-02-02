import os
import torch
import random 
import numpy as np

from math import sqrt
from torch.utils.data import Dataset
from scipy.fftpack import fft, fftfreq
from scipy.io import wavfile
from sklearn.preprocessing import MinMaxScaler

class PeriodogramDataset(Dataset):
    """ Periodogram dataset """
    def __init__(self, filenames, hives, slice_freq=None):
        self.files = filenames
        self.labels = hives
        self.slice_freq = slice_freq

    def __getitem__(self, idx):
        filename = self.files[idx]
        sample_rate, sound_samples = wavfile.read(filename)
        hive_name = filename.split(os.sep)[-2].split("_")[0]
        label = next(index for index, name in enumerate(self.labels) if name == hive_name)
        if len(sound_samples.shape) > 1:
            # 2-channel recording
            sound_samples = sound_samples.T[0]
        sound_samples = sound_samples/(2.0**31)
        periodogram = fft(sound_samples, n=sample_rate)
        periodogram = abs(periodogram[1:int(len(periodogram)/2)])
        if self.slice_freq:
            periodogram = periodogram[self.slice_freq[0]:self.slice_freq[1]]
        scaled_perio = MinMaxScaler().fit_transform(periodogram.reshape(-1, 1)).T
        scaled_perio = scaled_perio.astype(np.float32)
        return (scaled_perio, label)
        
    def __len__(self):
        return len(self.files)