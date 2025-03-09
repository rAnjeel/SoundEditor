import numpy as np

class AntiDistortion:
    def __init__(self):
        self.types = {
            'soft': {'threshold': -20, 'ratio': 2},
            'medium': {'threshold': -15, 'ratio': 3},
            'hard': {'threshold': -10, 'ratio': 4},
            'limit': {'threshold': -6, 'ratio': 10},
            'brick': {'threshold': -3, 'ratio': 20}
        }

    def process(self, audio_data, distortion_type='medium'):
        """
        Applique l'anti-distorsion sur les données audio
        :param audio_data: numpy array des données audio
        :param distortion_type: type d'anti-distorsion (soft/medium/hard/limit/brick)
        :return: audio traité
        """
        if distortion_type not in self.types:
            raise ValueError(f"Type de distorsion invalide. Choisir parmi: {list(self.types.keys())}")

        settings = self.types[distortion_type]
        threshold_db = settings['threshold']
        ratio = settings['ratio']

        # Convertir le seuil de dB en amplitude linéaire
        threshold = 10 ** (threshold_db / 20)

        # Copier les données pour ne pas modifier l'original
        processed_audio = np.copy(audio_data)

        # Appliquer l'anti-distorsion
        mask = np.abs(processed_audio) > threshold
        processed_audio[mask] = np.sign(processed_audio[mask]) * (
            threshold + (np.abs(processed_audio[mask]) - threshold) / ratio
        )

        return processed_audio 