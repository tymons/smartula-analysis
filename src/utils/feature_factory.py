import logging

from enum import Enum
from torch.utils.data import DataLoader, random_split

from utils.dataset.periodogram_dataset import PeriodogramDataset
from utils.dataset.spectrogram_dataset import SpectrogramDataset
from utils.dataset.mfcc_dataset import MfccDataset
from utils.dataset.melspectrogram_dataset import MelSpectrogramDataset
from utils.dataset.bioacustics_indicies.sound_indicies_dataset import SoundIndiciesDataset
from utils.dataset.double_feature_dataset import DoubleFeatureDataset 

class SoundFeatureFactory():        
    """ Factory for data loaders """
    def _get_spectrogram_dataset(sound_filenames, labels, features_params_dict):
        """ Function for getting spectrogram """
        nfft = features_params_dict.get('nfft', 4096)
        hop_len = features_params_dict.get('hop_len', (4096//3)+30)
        fmax = features_params_dict.get('fmax', 2750)
        should_scale = features_params_dict.get('scale', True)

        logging.info(f'building spectrogram dataset with params: nfft({nfft}), hop_len({hop_len}), fmax({fmax}), min_max_scale({should_scale})')
        return SpectrogramDataset(sound_filenames, labels, nfft=nfft, hop_len=hop_len, scale=should_scale, fmax=fmax, truncate_power_two=True)

    def _get_melspectrogram_dataset(sound_filenames, labels, features_params_dict):
        """ Function for getting melspectrogram dataset """
        nfft = features_params_dict.get('nfft', 4096)
        hop_len = features_params_dict.get('hop_len', (4096//3)+30)
        no_mels = features_params_dict.get('mels', 64)
        should_scale = features_params_dict.get('scale', True)

        logging.info(f'building melspectrogram dataset with params: nfft({nfft}), hop_len({hop_len}), no_mels({no_mels}), min_max_scale({should_scale})')
        return MelSpectrogramDataset(sound_filenames, labels, nfft=nfft, hop_len=hop_len, scale=should_scale, mels=no_mels, truncate_power_two=True)

    def _get_periodogram_dataset(sound_filenames, labels, features_params_dict):
        """ Function for getting periodogram dataset """
        start_freq = features_params_dict.get('slice_frequency_start', 0)
        stop_freq = features_params_dict.get('slice_frequency_stop', 2048)
        db_scale = features_params_dict.get('scale_db', False)
        should_scale = features_params_dict.get('scale', True)

        logging.info(f'building periodogram dataset with params: db_scale({db_scale}), min_max_scale({should_scale}), slice_freq({(start_freq, stop_freq)})')
        return PeriodogramDataset(sound_filenames, labels, scale_db=db_scale, scale=should_scale, slice_freq=(start_freq, stop_freq))

    def _get_mfcc_dataset(sound_filenames, labels, features_params_dict):
        """ Function for getting mfcc from sound """
        nfft = features_params_dict.get('nfft', 4096)
        hop_len = features_params_dict.get('hop_len', (4096//3)+30)
        no_mels = features_params_dict.get('mels', 64)
        should_scale = features_params_dict.get('scale', True)

        logging.info(f'building mfcc dataset with params: nfft({nfft}), hop_len({hop_len}), no_mels({no_mels}), min_max_scale({should_scale})')
        return MfccDataset(sound_filenames, labels, nfft=nfft, hop_len=hop_len, scale=should_scale, mels=no_mels)

    def _get_indicies_dataset(sound_filenames, labels, features_params_dict):
        """ Function for getting indicies from sounds """
        sound_indicies_params = features_params_dict.get('sound_indicies', {})
        indicator_type = sound_indicies_params.get('type', 'aci')
        config = sound_indicies_params.get('config', {'j_samples': 512})

        logging.info(f'building sound bio indicies dataset with params: type({indicator_type}), config({config})')
        return SoundIndiciesDataset(sound_filenames, labels, SoundIndiciesDataset.SoundIndicator(indicator_type), **config)


    @classmethod
    def build_dataset(cls, input_type, sound_filenames, labels, features_params_dict, background_filenames=[], background_labels=[]):
        """ Function for building dataset based on sound filenames and defined feature 
        
        Parameters:
            input_type (Enum): input type
            sound_filenames (list(str)): list with sound filenames
            labels (list(str)): label names
            features_params_dict (dictionary): dictionary from config.json for particular feature
            background_filenames (list): background filenames for contrastive learning
            background_labels (list): background labels for contrastive learning

        Returns:
            dataset (nn.Dataset): dataset
            fparams (dict): params used to build dataset
        """
        method_name = f'_get_{input_type.value.lower()}_dataset'
        function = getattr(cls, method_name, lambda: 'invalid dataset')
        dataset = function(sound_filenames, labels, features_params_dict)
        if background_filenames and background_labels:
            background = function(background_filenames, background_labels, features_params_dict)
            dataset = DoubleFeatureDataset(dataset, background)

        feature_params_dict = {f"FEATURE_{key}": val for key, val in dataset.get_params().items()}

        return dataset, feature_params_dict

    @classmethod
    def build_dataloaders(cls, dataset, batch_size, ratio=0.15, num_workers=4):
        """ Function for getting dataloaders 
        
        Parameters:
            dataset (nn.Dataset): dataset from which dataloader should be build
            batch_size (int): batch size for loader
            ratio (int): ratio between train dataset and validation dataset
            num_workers (int): num workers for dataloaders

        Returns:
            (train_loader, val_loader) (tuple(Dataloader, Dataloader)): train dataloader, validation dataloder
        """
        val_amount = int(dataset.__len__() * ratio)
        train_set, val_set = random_split(dataset, [(dataset.__len__() - val_amount), val_amount])

        train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, drop_last=True, num_workers=num_workers)
        val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=True, drop_last=True, num_workers=num_workers)
        
        return train_loader, val_loader


class SoundFeatureType(Enum):
    SPECTROGRAM = 'spectrogram'
    MELSPECTROGRAM = 'melspectrogram'
    PERIODOGRAM = 'periodogram'
    MFCC = 'mfcc'
    BIOINDICIES = 'indicies'

    @classmethod
    def from_name(cls, name):
        for _, feature in SoundFeatureType.__members__.items():
            if feature.value == name:
                return feature
        raise ValueError(f"{name} is not a valid station name")