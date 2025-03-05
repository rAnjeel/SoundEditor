import wave
import numpy as np
import tkinter as tk
from tkinter import filedialog
import pyaudio
import threading
import queue
import time
import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import math

class SoundEditor:
    def __init__(self):
        self.audio_file = None
        self.audio_data = None
        self.sample_width = None
        self.framerate = None
        self.n_channels = None
        self.is_playing = False
        self.is_paused = False
        self.stream = None
        self.p = None
        self.audio_thread = None
        self.chunk_size = 1024 * 4
        self.current_file_path = None  # Pour stocker le chemin du fichier
        
        # Créer l'interface graphique
        self.window = tk.Tk()
        self.window.title("Éditeur Audio Anjely")
        self.window.geometry("400x450")  # Augmenté pour le nouveau label
        
        # Label pour afficher le nom du fichier
        self.file_label = tk.Label(self.window, text="Aucun fichier chargé", wraplength=350)
        self.file_label.pack(pady=5)
        
        # Boutons et contrôles
        self.load_button = tk.Button(self.window, text="Charger fichier WAV", command=self.load_file)
        self.load_button.pack(pady=10)
        
        self.amplitude_label = tk.Label(self.window, text="Amplification (1.0 = normal):")
        self.amplitude_label.pack()
        
        self.amplitude_scale = tk.Scale(self.window, from_=0.0, to=20.0, resolution=0.5, 
                                      orient=tk.HORIZONTAL, length=300)
        self.amplitude_scale.set(1.0)
        self.amplitude_scale.pack()
        
        # Modification du contrôle du seuil
        self.threshold_label = tk.Label(self.window, text="Seuil de compression (dB):")
        self.threshold_label.pack()
        
        self.threshold_scale = tk.Scale(self.window, from_=-60, to=0, resolution=1,
                                      orient=tk.HORIZONTAL, length=300)
        self.threshold_scale.set(-12)  # Valeur par défaut en dB
        self.threshold_scale.pack()
        
        # Label pour afficher la valeur en pourcentage
        self.threshold_value_label = tk.Label(self.window, text="Seuil: -12 dB (25%)")
        self.threshold_value_label.pack()
        
        # Bind l'événement de changement de valeur
        self.threshold_scale.config(command=self.update_threshold_label)
        
        # Menu pour choisir le type d'anti-distorsion
        self.distortion_type_label = tk.Label(self.window, text="Type d'anti-distorsion:")
        self.distortion_type_label.pack()
        
        self.distortion_types = {
            "Compression douce (Soft Clip)": "soft_clip",
            "Limitation dure (Hard Clip)": "hard_clip",
            "Saturation Tanh": "tanh",
        }
        
        self.distortion_var = tk.StringVar(value="Compression douce (Soft Clip)")
        self.distortion_menu = tk.OptionMenu(self.window, self.distortion_var, 
                                           *self.distortion_types.keys())
        self.distortion_menu.pack()
        
        # Création d'un frame pour les boutons de contrôle
        self.control_frame = tk.Frame(self.window)
        self.control_frame.pack(pady=10)
        
        self.play_button = tk.Button(self.control_frame, text="Jouer", command=self.play_audio)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = tk.Button(self.control_frame, text="Pause", command=self.pause_audio)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop_audio)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = tk.Button(self.window, text="Sauvegarder", command=self.save_file)
        self.save_button.pack(pady=10)
        
        # Frame pour les indicateurs de niveau
        self.meters_frame = tk.Frame(self.window)
        self.meters_frame.pack(pady=5)
        
        # Création du VU-mètre
        self.level_canvas = tk.Canvas(self.meters_frame, width=300, height=20, bg='black')
        self.level_canvas.pack()
        
        # Création des segments du VU-mètre
        self.level_segments = []
        num_segments = 30
        segment_width = 8
        segment_spacing = 2
        for i in range(num_segments):
            x = i * (segment_width + segment_spacing) + 5
            segment = self.level_canvas.create_rectangle(
                x, 5, x + segment_width, 15,
                fill='darkgrey', outline='grey'
            )
            self.level_segments.append(segment)
        
        # Label pour l'indicateur de distorsion
        self.distortion_label = tk.Label(self.meters_frame, text="Pas de distorsion", 
                                       fg='green')
        self.distortion_label.pack()
        
        # Style pour les scales
        self.style = ttk.Style()
        self.style.configure("Red.Horizontal.TScale", troughcolor='pink')
        self.style.configure("Green.Horizontal.TScale", troughcolor='lightgreen')
    
    def update_threshold_label(self, value):
        """Met à jour le label avec la valeur en dB et pourcentage"""
        db_value = float(value)
        percent = round(10 ** (db_value/20) * 100)  # Conversion dB vers pourcentage
        self.threshold_value_label.config(text=f"Seuil: {db_value} dB ({percent}%)")

    def load_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Fichiers WAV", "*.wav")])
        if filename:
            self.current_file_path = filename
            self.audio_file = wave.open(filename, 'rb')
            self.sample_width = self.audio_file.getsampwidth()
            self.framerate = self.audio_file.getframerate()
            self.n_channels = self.audio_file.getnchannels()
            
            # Lire les données audio
            audio_bytes = self.audio_file.readframes(self.audio_file.getnframes())
            self.audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            self.audio_file.close()
            
            # Mettre à jour le label avec le nom du fichier
            file_name = filename.split('/')[-1]  # Extrait juste le nom du fichier
            self.file_label.config(text=f"Fichier chargé: {file_name}")
    
    def apply_threshold(self, audio_data, threshold_db):
        """Applique un seuil avec le type de compression choisi"""
        max_value = np.iinfo(np.int16).max
        threshold_ratio = 10 ** (threshold_db/20)
        threshold = max_value * threshold_ratio
        
        distortion_type = self.distortion_types[self.distortion_var.get()]
        
        if distortion_type == "hard_clip":
            return self.hard_clip(audio_data, threshold)
        elif distortion_type == "tanh":
            return self.tanh_clip(audio_data, threshold)
        else:  # soft_clip par défaut
            return self.soft_clip(audio_data, threshold)

    def soft_clip(self, audio_data, threshold):
        """Compression douce avec knee"""
        ratio = 4.0
        knee_width = threshold * 0.3
        
        # Zone sous le seuil
        mask_below = np.abs(audio_data) <= (threshold - knee_width/2)
        result = np.zeros_like(audio_data)
        result[mask_below] = audio_data[mask_below]
        
        # Zone de transition (knee)
        mask_knee = (np.abs(audio_data) > (threshold - knee_width/2)) & (np.abs(audio_data) < (threshold + knee_width/2))
        x_knee = audio_data[mask_knee]
        factor = 1.0 - (1.0 - 1.0/ratio) * ((np.abs(x_knee) - (threshold - knee_width/2)) / knee_width) ** 2
        result[mask_knee] = x_knee * factor
        
        # Zone au-dessus du seuil
        mask_above = np.abs(audio_data) >= (threshold + knee_width/2)
        x_above = audio_data[mask_above]
        sign = np.sign(x_above)
        compressed = threshold + (np.abs(x_above) - threshold) / ratio
        result[mask_above] = sign * compressed
        
        return result

    def hard_clip(self, audio_data, threshold):
        """Limitation dure à la valeur seuil"""
        return np.clip(audio_data, -threshold, threshold)

    def tanh_clip(self, audio_data, threshold):
        """Saturation douce utilisant la fonction tanh"""
        # Normaliser les données pour tanh
        normalized = audio_data / threshold
        # Appliquer tanh et remettre à l'échelle
        return threshold * np.tanh(normalized)

    def modify_amplitude(self, amplitude_factor):
        if self.audio_data is not None:
            # Normalisation avant amplification
            max_current = np.max(np.abs(self.audio_data))
            if max_current > 0:
                normalized = self.audio_data * (0.9 * np.iinfo(np.int16).max / max_current)
            else:
                normalized = self.audio_data
            
            # Applique l'amplification
            modified = normalized * amplitude_factor
            
            # Applique la compression douce (utilise maintenant la valeur en dB)
            threshold_db = self.threshold_scale.get()
            modified = self.apply_threshold(modified, threshold_db)
            
            return modified.astype(np.int16)
        return None
    
    def update_vu_meter(self, audio_data):
        """Met à jour le VU-mètre avec les niveaux actuels"""
        if audio_data is not None:
            max_value = np.iinfo(np.int16).max
            level = np.max(np.abs(audio_data)) / max_value
            
            # Mise à jour des segments
            num_active = int(level * len(self.level_segments))
            for i, segment in enumerate(self.level_segments):
                if i < num_active:
                    if i < len(self.level_segments) * 0.7:
                        color = '#00ff00'
                    elif i < len(self.level_segments) * 0.9:
                        color = '#ffff00'
                    else:
                        color = '#ff0000'
                else:
                    color = 'darkgrey'
                self.level_canvas.itemconfig(segment, fill=color)
            
            # Mise à jour de l'indicateur de distorsion avec le type actuel
            distortion_type = self.distortion_types[self.distortion_var.get()]
            if level > 0.9:
                self.distortion_label.config(
                    text=f"⚠️ Distorsion détectée! (Mode: {self.distortion_var.get()})", 
                    fg='red'
                )
            else:
                self.distortion_label.config(
                    text=f"Pas de distorsion (Mode: {self.distortion_var.get()})", 
                    fg='green'
                )
            
            # Mise à jour des couleurs des scales
            if level > 0.9:
                self.amplitude_scale.config(troughcolor='red')
            elif level > 0.7:
                self.amplitude_scale.config(troughcolor='yellow')
            else:
                self.amplitude_scale.config(troughcolor='lightgreen')

    def play_audio_thread(self):
        """Fonction exécutée dans un thread séparé pour la lecture audio"""
        modified_data = self.modify_amplitude(self.amplitude_scale.get())
        data = modified_data.tobytes()
        
        if self.p is None:
            self.p = pyaudio.PyAudio()
        
        if self.stream is None:
            self.stream = self.p.open(format=self.p.get_format_from_width(self.sample_width),
                                    channels=self.n_channels,
                                    rate=self.framerate,
                                    output=True)

        # Lecture par chunks
        chunks = [data[i:i+self.chunk_size] for i in range(0, len(data), self.chunk_size)]
        
        for chunk in chunks:
            if not self.is_playing:
                break
            while self.is_paused:
                time.sleep(0.1)
                if not self.is_playing:
                    break
            if self.stream and chunk:
                self.stream.write(chunk)
                # Mise à jour du VU-mètre
                chunk_data = np.frombuffer(chunk, dtype=np.int16)
                self.window.after(0, self.update_vu_meter, chunk_data)
        
        self.cleanup_audio_resources()

    def cleanup_audio_resources(self):
        """Nettoie les ressources audio sans toucher au thread"""
        self.is_playing = False
        self.is_paused = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.p:
            self.p.terminate()
            self.p = None
        
        self.pause_button.config(text="Pause")
        
        # Réinitialisation du VU-mètre
        for segment in self.level_segments:
            self.level_canvas.itemconfig(segment, fill='darkgrey')
        
        # Réinitialisation des indicateurs
        self.distortion_label.config(text="Pas de distorsion", fg='green')
        self.amplitude_scale.config(troughcolor='lightgreen')

    def play_audio(self):
        if self.audio_data is not None and not self.is_playing:
            self.is_playing = True
            self.is_paused = False
            
            # Démarrer la lecture dans un thread séparé
            self.audio_thread = threading.Thread(target=self.play_audio_thread)
            self.audio_thread.daemon = True  # Le thread s'arrêtera quand le programme principal s'arrête
            self.audio_thread.start()
    
    def pause_audio(self):
        if self.is_playing:
            self.is_paused = not self.is_paused
            if self.stream:
                if self.is_paused:
                    self.pause_button.config(text="Reprendre")
                else:
                    self.pause_button.config(text="Pause")
    
    def stop_audio(self):
        """Arrête la lecture audio"""
        self.is_playing = False
        self.is_paused = False
        
        # Attendre que le thread se termine si on n'est pas dans le thread audio
        if self.audio_thread and self.audio_thread.is_alive() and self.audio_thread != threading.current_thread():
            self.audio_thread.join(timeout=1.0)
            
        self.cleanup_audio_resources()
    
    def save_file(self):
        if self.audio_data is not None:
            filename = filedialog.asksaveasfilename(defaultextension=".wav",
                                                  filetypes=[("Fichiers WAV", "*.wav")])
            if filename:
                modified_data = self.modify_amplitude(self.amplitude_scale.get())
                
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(self.n_channels)
                    wf.setsampwidth(self.sample_width)
                    wf.setframerate(self.framerate)
                    wf.writeframes(modified_data.tobytes())
    
    def __del__(self):
        """Nettoyage des ressources à la fermeture"""
        self.stop_audio()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    editor = SoundEditor()
    editor.run() 