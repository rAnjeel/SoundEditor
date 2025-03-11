import numpy as np
from scipy import signal
from scipy.signal import windows
from scipy.ndimage import gaussian_filter

class NoiseReducer:
    def __init__(self):
        self.noise_profile = None
        self.fft_size = 4096  # Augmenté pour une meilleure résolution fréquentielle
        self.hop_size = 1024
        self.window = windows.hann(self.fft_size)
        self.last_processed = None
        self.noise_threshold = -40  # dB
        
    def set_noise_profile(self, noise_sample):
        """Définit le profil de bruit à partir d'un échantillon"""
        # Normalisation du signal de bruit
        noise_sample = noise_sample.astype(np.float32)
        max_val = np.iinfo(np.int16).max
        noise_sample = noise_sample / max_val
        
        # Calcul du spectrogramme du bruit
        _, _, Zxx = signal.stft(
            noise_sample,
            window=self.window,
            nperseg=self.fft_size,
            noverlap=self.fft_size - self.hop_size
        )
        
        # Estimation du profil de bruit
        self.noise_profile = np.mean(np.abs(Zxx), axis=1)
        self.noise_std = np.std(np.abs(Zxx), axis=1)
        self.noise_peak = np.percentile(np.abs(Zxx), 95, axis=1)
        
        # Calcul des statistiques de bruit
        self.noise_stats = {
            'mean_power': 10 * np.log10(np.mean(np.abs(Zxx)**2)),
            'peak_power': 10 * np.log10(np.max(np.abs(Zxx)**2)),
            'spectral_floor': 10 * np.log10(np.percentile(np.abs(Zxx)**2, 10))
        }
        
        return self.noise_stats
        
    def process(self, audio_data, reduction_strength=1.0, smoothing=0.1):
        """Applique la réduction de bruit avec retour d'informations"""
        if self.noise_profile is None:
            raise ValueError("Profil de bruit non défini")
        
        # Normalisation
        audio_data = audio_data.astype(np.float32)
        max_val = np.iinfo(np.int16).max
        audio_data = audio_data / max_val
        
        # STFT
        f, t, Zxx = signal.stft(
            audio_data,
            window=self.window,
            nperseg=self.fft_size,
            noverlap=self.fft_size - self.hop_size
        )
        
        # Calcul des masques de réduction
        noise_mask = np.abs(Zxx) < (self.noise_profile[:, np.newaxis] * reduction_strength)
        
        # SNR instantané
        snr = 10 * np.log10(np.abs(Zxx)**2 / (self.noise_profile[:, np.newaxis]**2 + 1e-10))
        
        # Calcul du gain adaptatif
        reduction_factor = np.clip(reduction_strength * 2, 0.1, 10.0)
        gain = 1.0 - np.exp(-np.maximum(snr - self.noise_threshold, 0) / reduction_factor)
        
        # Application du lissage spectral
        gain = gaussian_filter(gain, sigma=(2, 1))
        
        # Lissage temporel
        smoothed_gain = np.zeros_like(gain)
        alpha = smoothing
        smoothed_gain[:, 0] = gain[:, 0]
        for i in range(1, gain.shape[1]):
            smoothed_gain[:, i] = alpha * gain[:, i] + (1 - alpha) * smoothed_gain[:, i-1]
        
        # Application du gain avec préservation de phase
        Zxx_cleaned = Zxx * smoothed_gain
        
        # Reconstruction
        _, cleaned = signal.istft(
            Zxx_cleaned,
            window=self.window,
            nperseg=self.fft_size,
            noverlap=self.fft_size - self.hop_size
        )
        
        # Normalisation et mise à l'échelle
        cleaned = np.clip(cleaned, -1, 1)
        cleaned = cleaned * max_val
        
        # Calcul des statistiques de réduction
        reduction_stats = {
            'noise_reduction_db': 10 * np.log10(np.mean(noise_mask.astype(float))),
            'avg_gain_db': 20 * np.log10(np.mean(smoothed_gain)),
            'signal_preserved': np.mean(1 - noise_mask.astype(float))
        }
        
        self.last_processed = cleaned.copy()
        
        return cleaned.astype(np.int16), reduction_stats

    def reset(self):
        self.last_processed = None 