import tkinter as tk
from tkinter import filedialog, messagebox
from audio_editor import AudioEditor
import pygame  # Ajout de pygame pour la lecture audio
import os
import tempfile

class AudioEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Éditeur Audio")
        self.editor = None
        self.playing = False
        self.temp_file = None  # Pour stocker le chemin du fichier temporaire
        self.current_amplitude = 1.0  # Garder trace de l'amplitude actuelle
        self.original_editor = None   # Garder une copie de l'audio original
        
        # Initialisation de pygame pour l'audio
        pygame.mixer.init()
        
        # Frame principale
        main_frame = tk.Frame(root, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        # Bouton pour charger un fichier
        self.load_button = tk.Button(main_frame, text="Charger un fichier WAV", command=self.load_file)
        self.load_button.pack(pady=10)
        
        # Label pour afficher le nom du fichier
        self.file_label = tk.Label(main_frame, text="Aucun fichier chargé")
        self.file_label.pack(pady=5)
        
        # Frame pour le contrôle d'amplitude
        amplitude_frame = tk.Frame(main_frame)
        amplitude_frame.pack(pady=20)
        
        # Label pour l'amplitude
        tk.Label(amplitude_frame, text="Facteur d'amplitude:").pack()
        
        # Frame pour le slider et la saisie
        slider_input_frame = tk.Frame(amplitude_frame)
        slider_input_frame.pack(fill='x')
        
        # Slider pour l'amplitude (plage augmentée)
        self.amplitude_slider = tk.Scale(slider_input_frame, 
                                       from_=0.1, to=10.0,  # Augmentation de la plage
                                       resolution=0.1, 
                                       orient=tk.HORIZONTAL, 
                                       length=200,
                                       command=self.on_slider_change)
        self.amplitude_slider.set(1.0)
        self.amplitude_slider.pack(side=tk.LEFT, padx=(0, 10))
        
        # Frame pour la saisie directe
        input_frame = tk.Frame(slider_input_frame)
        input_frame.pack(side=tk.LEFT, fill='y')
        
        # Champ de saisie pour l'amplitude
        self.amplitude_entry = tk.Entry(input_frame, width=8)
        self.amplitude_entry.insert(0, "1.0")
        self.amplitude_entry.pack(side=tk.LEFT, padx=5)
        
        # Bouton pour appliquer la valeur saisie
        tk.Button(input_frame, text="Valider", command=self.apply_entry_value).pack(side=tk.LEFT)
        
        # Bouton pour appliquer les modifications
        self.apply_button = tk.Button(main_frame, text="Appliquer les modifications", command=self.apply_changes)
        self.apply_button.pack(pady=10)
        self.apply_button['state'] = 'disabled'

        # Boutons de contrôle de lecture
        playback_frame = tk.Frame(main_frame)
        playback_frame.pack(pady=10)
        
        self.play_button = tk.Button(playback_frame, text="▶ Play", command=self.play_audio)
        self.play_button.pack(side=tk.LEFT, padx=5)
        self.play_button['state'] = 'disabled'
        
        self.stop_button = tk.Button(playback_frame, text="⏹ Stop", command=self.stop_audio)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button['state'] = 'disabled'
        
        
        # Bouton pour sauvegarder
        self.save_button = tk.Button(main_frame, text="Sauvegarder", command=self.save_file)
        self.save_button.pack(pady=10)
        self.save_button['state'] = 'disabled'

    def on_slider_change(self, value):
        """Met à jour le champ de saisie quand le slider change"""
        self.amplitude_entry.delete(0, tk.END)
        self.amplitude_entry.insert(0, str(float(value)))

    def apply_entry_value(self):
        """Applique la valeur saisie au slider"""
        try:
            value = float(self.amplitude_entry.get())
            if value <= 0:
                raise ValueError("La valeur doit être positive")
            if value > 10.0:  # Limite maximale
                if messagebox.askyesno("Attention", 
                    "Une valeur élevée peut causer de la distorsion. Continuer?"):
                    self.amplitude_slider.config(to=value)
                else:
                    self.amplitude_entry.delete(0, tk.END)
                    self.amplitude_entry.insert(0, str(self.amplitude_slider.get()))
                    return
            self.amplitude_slider.set(value)
        except ValueError as e:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre positif valide")
            self.amplitude_entry.delete(0, tk.END)
            self.amplitude_entry.insert(0, str(self.amplitude_slider.get()))

    def load_file(self):
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("Fichiers WAV", "*.wav")]
            )
            if filename:
                # Nettoyer les ressources existantes
                self.cleanup_resources()
                
                # Charger le nouveau fichier
                self.editor = AudioEditor(filename)
                self.original_editor = AudioEditor(filename)  # Garder une copie originale
                self.current_amplitude = 1.0  # Réinitialiser l'amplitude
                
                # Réinitialiser l'interface
                self.amplitude_slider.set(1.0)
                self.amplitude_entry.delete(0, tk.END)
                self.amplitude_entry.insert(0, "1.0")
                
                self.file_label.config(text=f"Fichier chargé: {filename.split('/')[-1]}")
                self.apply_button['state'] = 'normal'
                self.save_button['state'] = 'normal'
                self.play_button['state'] = 'normal'
                self.stop_button['state'] = 'normal'
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {str(e)}")

    def play_audio(self):
        try:
            if self.editor and not self.playing:
                # S'assurer que pygame est initialisé
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                
                # Utiliser le fichier temporaire s'il existe, sinon utiliser le fichier original
                audio_file = self.temp_file if self.temp_file else self.editor.filename
                
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                self.playing = True
                self.play_button.config(text="⏸ Pause")
            elif self.playing:
                pygame.mixer.music.pause()
                self.playing = False
                self.play_button.config(text="▶ Play")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la lecture: {str(e)}")

    def stop_audio(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            self.playing = False
            self.play_button.config(text="▶ Play")

    def apply_changes(self):
        try:
            if self.editor:
                # Arrêter la lecture avant d'appliquer les modifications
                self.stop_audio()
                
                # Calculer le facteur relatif par rapport à l'amplitude actuelle
                new_amplitude = self.amplitude_slider.get()
                relative_factor = new_amplitude / self.current_amplitude
                
                # Réinitialiser l'éditeur avec les données originales
                self.editor = AudioEditor(self.original_editor.filename)
                
                # Appliquer la nouvelle amplitude
                self.editor.adjust_amplitude(new_amplitude)
                self.current_amplitude = new_amplitude
                
                # Créer un nouveau fichier temporaire
                if self.temp_file:
                    try:
                        os.remove(self.temp_file)
                    except:
                        pass
                
                temp_fd, self.temp_file = tempfile.mkstemp(suffix='.wav')
                os.close(temp_fd)
                self.editor.save(self.temp_file)
                
                messagebox.showinfo("Succès", "Modifications appliquées!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'application: {str(e)}")

    def save_file(self):
        try:
            if self.editor:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".wav",
                    filetypes=[("Fichiers WAV", "*.wav")]
                )
                if filename:
                    self.editor.save(filename)
                    messagebox.showinfo("Succès", "Fichier sauvegardé avec succès!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def cleanup_resources(self):
        """Nettoie toutes les ressources avant de charger un nouveau fichier"""
        # Arrêter la lecture
        self.stop_audio()
        
        # Supprimer le fichier temporaire
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                self.temp_file = None
            except:
                pass
        
        # Réinitialiser les éditeurs
        if self.editor:
            self.editor = None
        if self.original_editor:
            self.original_editor = None

    def __del__(self):
        """Nettoyage à la fermeture"""
        self.cleanup_resources()
        pygame.mixer.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioEditorGUI(root)
    root.mainloop() 