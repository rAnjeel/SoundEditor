import wave
import numpy as np
import struct
from anti_distortion import AntiDistortion

class AudioEditor:
    def __init__(self, filename):
        """
        Initialise l'éditeur audio avec un fichier WAV
        """
        self.filename = filename
        self.wave_file = None
        self.params = None
        self.raw_data = None
        self.audio_data = None
        self.load_file()
        self.anti_distortion = AntiDistortion()

    def load_file(self):
        """
        Charge le fichier WAV et extrait ses paramètres et données
        """
        try:
            self.wave_file = wave.open(self.filename, 'rb')
            self.params = self.wave_file.getparams()
            
            # Affichage des informations du fichier pour le débogage
            print(f"Informations du fichier audio:")
            print(f"- Canaux: {self.params.nchannels}")
            print(f"- Taille échantillon: {self.params.sampwidth} bytes")
            print(f"- Fréquence: {self.params.framerate} Hz")
            print(f"- Nombre de frames: {self.params.nframes}")
            print(f"- Taille attendue: {self.params.nframes * self.params.nchannels} échantillons")
            
            # Lecture des données brutes
            self.raw_data = self.wave_file.readframes(self.params.nframes)
            actual_size = len(self.raw_data) // self.params.sampwidth
            print(f"- Taille réelle: {actual_size} échantillons")
            
            # Détermination du format en fonction du nombre de bits
            if self.params.sampwidth == 1:  # 8 bits
                self.audio_data = np.frombuffer(self.raw_data, dtype=np.uint8)
                # Conversion de 8 bits unsigned en signed
                self.audio_data = self.audio_data.astype(np.float32) - 128
                self.audio_data = self.audio_data.astype(np.int8)
            
            elif self.params.sampwidth == 2:  # 16 bits
                self.audio_data = np.frombuffer(self.raw_data, dtype=np.int16)
            
            elif self.params.sampwidth == 4:  # 32 bits
                self.audio_data = np.frombuffer(self.raw_data, dtype=np.int32)
            
            else:
                raise ValueError(f"Format audio non supporté: {self.params.sampwidth * 8} bits")

            # Vérification de la cohérence des données avec tolérance
            expected_length = self.params.nframes * self.params.nchannels
            actual_length = len(self.audio_data)
            
            # Accepter une différence de moins de 0.1% de la taille totale
            tolerance = max(1, int(expected_length * 0.001))
            if abs(actual_length - expected_length) > tolerance:
                print(f"Attention: Différence de taille détectée")
                print(f"- Attendu: {expected_length} échantillons")
                print(f"- Obtenu: {actual_length} échantillons")
                print(f"- Différence: {abs(actual_length - expected_length)} échantillons")
                
                # Ajuster la taille si nécessaire
                if actual_length < expected_length:
                    # Padding avec des zéros
                    padding = np.zeros(expected_length - actual_length, dtype=self.audio_data.dtype)
                    self.audio_data = np.concatenate([self.audio_data, padding])
                    print("Padding ajouté pour atteindre la taille attendue")
                else:
                    # Tronquer aux dimensions attendues
                    self.audio_data = self.audio_data[:expected_length]
                    print("Données tronquées à la taille attendue")
        
        except Exception as e:
            if self.wave_file:
                self.wave_file.close()
            raise ValueError(f"Erreur lors du chargement du fichier WAV: {str(e)}")

    def adjust_amplitude(self, factor):
        """
        Modifie l'amplitude du signal audio par un facteur donné
        :param factor: facteur de multiplication de l'amplitude (1.0 = pas de changement)
        """
        if factor <= 0:
            raise ValueError("Le facteur d'amplitude doit être positif")
        
        # Conversion en float32 pour les calculs
        audio_float = self.audio_data.astype(np.float32)
        
        # Application du facteur
        audio_float = audio_float * factor
        
        # Écrêtage selon le format
        if self.params.sampwidth == 1:  # 8 bits
            np.clip(audio_float, -128, 127, out=audio_float)
            self.audio_data = audio_float.astype(np.int8)
        elif self.params.sampwidth == 2:  # 16 bits
            np.clip(audio_float, -32768, 32767, out=audio_float)
            self.audio_data = audio_float.astype(np.int16)
        elif self.params.sampwidth == 4:  # 32 bits
            np.clip(audio_float, -2147483648, 2147483647, out=audio_float)
            self.audio_data = audio_float.astype(np.int32)

    def save(self, output_filename):
        """
        Sauvegarde le signal audio modifié dans un nouveau fichier WAV
        """
        try:
            with wave.open(output_filename, 'wb') as wave_output:
                wave_output.setparams(self.params)
                
                # Conversion selon le format
                if self.params.sampwidth == 1:
                    # Conversion en unsigned pour le format 8 bits
                    output_data = (self.audio_data + 128).astype(np.uint8).tobytes()
                else:
                    output_data = self.audio_data.tobytes()
                
                wave_output.writeframes(output_data)
                
        except Exception as e:
            raise ValueError(f"Erreur lors de la sauvegarde du fichier: {str(e)}")

    def apply_anti_distortion(self, distortion_type='medium'):
        """
        Applique l'anti-distorsion à l'audio chargé
        :param distortion_type: type d'anti-distorsion (soft/medium/hard/limit/brick)
        """
        if self.audio_data is None:
            raise ValueError("Aucun fichier audio n'est chargé")

        self.audio_data = self.anti_distortion.process(self.audio_data, distortion_type)
        print(f"Anti-distorsion de type '{distortion_type}' appliquée")

    def __del__(self):
        """
        Ferme proprement le fichier WAV à la destruction de l'objet
        """
        if self.wave_file:
            self.wave_file.close() 