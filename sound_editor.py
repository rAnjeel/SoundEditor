import wave
import numpy as np
import tkinter as tk
from tkinter import filedialog
import pyaudio

class SoundEditor:
    def __init__(self):
        self.audio_file = None
        self.audio_data = None
        self.sample_width = None
        self.framerate = None
        self.n_channels = None
        
        # Créer l'interface graphique
        self.window = tk.Tk()
        self.window.title("Éditeur Audio Anjely")
        self.window.geometry("400x300")
        
        # Boutons et contrôles
        self.load_button = tk.Button(self.window, text="Charger fichier WAV", command=self.load_file)
        self.load_button.pack(pady=10)
        
        self.amplitude_label = tk.Label(self.window, text="Amplification (1.0 = normal):")
        self.amplitude_label.pack()
        
        self.amplitude_scale = tk.Scale(self.window, from_=0.0, to=5.0, resolution=0.1, 
                                      orient=tk.HORIZONTAL, length=300)
        self.amplitude_scale.set(1.0)
        self.amplitude_scale.pack()
        
        self.play_button = tk.Button(self.window, text="Jouer", command=self.play_audio)
        self.play_button.pack(pady=10)
        
        self.save_button = tk.Button(self.window, text="Sauvegarder", command=self.save_file)
        self.save_button.pack(pady=10)
    
    def load_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Fichiers WAV", "*.wav")])
        if filename:
            self.audio_file = wave.open(filename, 'rb')
            self.sample_width = self.audio_file.getsampwidth()
            self.framerate = self.audio_file.getframerate()
            self.n_channels = self.audio_file.getnchannels()
            
            # Lire les données audio
            audio_bytes = self.audio_file.readframes(self.audio_file.getnframes())
            self.audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            self.audio_file.close()
    
    def modify_amplitude(self, amplitude_factor):
        if self.audio_data is not None:
            return (self.audio_data * amplitude_factor).astype(np.int16)
        return None
    
    def play_audio(self):
        if self.audio_data is not None:
            modified_data = self.modify_amplitude(self.amplitude_scale.get())
            
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(self.sample_width),
                          channels=self.n_channels,
                          rate=self.framerate,
                          output=True)
            
            # Jouer l'audio modifié
            stream.write(modified_data.tobytes())
            
            stream.stop_stream()
            stream.close()
            p.terminate()
    
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
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    editor = SoundEditor()
    editor.run() 