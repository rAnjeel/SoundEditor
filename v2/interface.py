import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from audio_editor import AudioEditor
import pygame  # Ajout de pygame pour la lecture audio
import os
import tempfile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

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

        # Frame pour l'anti-distorsion
        self.distortion_frame = ttk.LabelFrame(main_frame, text="Anti-distorsion", padding="5")
        self.distortion_frame.pack(pady=5, fill=tk.X)
        
        # Menu déroulant pour les types d'anti-distorsion
        self.distortion_types = ['soft', 'medium', 'hard', 'limit', 'brick']
        self.selected_distortion = tk.StringVar(value='medium')
        self.distortion_combo = ttk.Combobox(self.distortion_frame, 
                                           textvariable=self.selected_distortion,
                                           values=self.distortion_types,
                                           state='readonly',
                                           width=10)
        self.distortion_combo.pack(side=tk.LEFT, padx=5)
        
        self.distortion_button = ttk.Button(self.distortion_frame, 
                                          text="Appliquer", 
                                          command=self.apply_anti_distortion)
        self.distortion_button.pack(side=tk.LEFT, padx=5)

        # Frame pour le graphique
        self.plot_frame = ttk.LabelFrame(main_frame, text="Visualisation", padding="5")
        self.plot_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        # Création de la figure matplotlib
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Configuration initiale des axes
        self.ax1.set_title("Signal Original")
        self.ax2.set_title("Signal Traité")
        self.fig.tight_layout()

        # Frame pour les indicateurs de niveau
        self.meters_frame = ttk.LabelFrame(main_frame, text="Niveaux", padding="5")
        self.meters_frame.pack(pady=5, fill=tk.X)
        
        # VU-mètre pour le signal original
        self.original_meter_label = tk.Label(self.meters_frame, text="Original:")
        self.original_meter_label.pack(anchor=tk.W)
        
        self.original_meter_canvas = tk.Canvas(self.meters_frame, width=300, height=20, bg='black')
        self.original_meter_canvas.pack(fill=tk.X, padx=5)
        
        # VU-mètre pour le signal traité
        self.processed_meter_label = tk.Label(self.meters_frame, text="Traité:")
        self.processed_meter_label.pack(anchor=tk.W)
        
        self.processed_meter_canvas = tk.Canvas(self.meters_frame, width=300, height=20, bg='black')
        self.processed_meter_canvas.pack(fill=tk.X, padx=5)
        
        # Création des segments des VU-mètres avec plus de paramètres
        self.vu_meter_config = {
            'num_segments': 30,
            'segment_width': 8,
            'segment_spacing': 2,
            'warning_threshold': 0.7,  # 70% pour le jaune
            'critical_threshold': 0.9,  # 90% pour le rouge
            'update_interval': 50,  # ms
            'peak_hold_time': 1000,  # ms
            'colors': {
                'normal': '#00ff00',    # Vert
                'warning': '#ffff00',    # Jaune
                'critical': '#ff0000',   # Rouge
                'inactive': 'darkgrey',
                'peak': '#ffffff'        # Blanc pour les pics
            }
        }
        
        self.original_segments = self.create_vu_segments(self.original_meter_canvas)
        self.processed_segments = self.create_vu_segments(self.processed_meter_canvas)
        
        # Stockage des valeurs de pic
        self.peak_values = {'original': 0.0, 'processed': 0.0}
        self.peak_hold_timers = {'original': None, 'processed': None}
        
        # Label pour l'indicateur de distorsion avec plus d'informations
        self.distortion_label = tk.Label(self.meters_frame, 
                                       text="Niveau: -∞ dB | Pic: -∞ dB", 
                                       fg='green')
        self.distortion_label.pack(pady=5)

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
                self.original_editor = AudioEditor(filename)
                self.current_amplitude = 1.0
                
                # Mise à jour du graphique
                self.update_plot()
                
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
                
                # Démarrer les mises à jour des VU-mètres
                self.update_vu_meters()
                
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
            self.update_vu_meters()  # Mise à jour finale des VU-mètres

    def apply_changes(self):
        try:
            if self.editor:
                # Arrêter la lecture avant d'appliquer les modifications
                self.stop_audio()
                
                # Calculer le facteur relatif par rapport à l'amplitude actuelle
                new_amplitude = self.amplitude_slider.get()
                
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
                
                # Mettre à jour le graphique et les VU-mètres
                self.update_plot()
                self.update_vu_meters()
                
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

    def apply_anti_distortion(self):
        try:
            distortion_type = self.selected_distortion.get()
            self.editor.apply_anti_distortion(distortion_type)
            
            # Mettre à jour le graphique après l'application de l'anti-distorsion
            self.update_plot()
            
            messagebox.showinfo("Succès", f"Anti-distorsion '{distortion_type}' appliquée avec succès!")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def update_plot(self):
        """Met à jour les graphiques avec les données audio actuelles"""
        if self.editor and self.original_editor:
            # Nettoyer les graphiques
            self.ax1.clear()
            self.ax2.clear()
            
            # Configurer les titres
            self.ax1.set_title("Signal Original")
            self.ax2.set_title("Signal Traité")
            
            # S'assurer que les deux signaux ont la même longueur
            min_length = min(len(self.original_editor.audio_data), len(self.editor.audio_data))
            
            # Calculer le pas d'échantillonnage pour avoir environ 1000 points
            sample_size = min(1000, min_length)
            step = max(1, min_length // sample_size)
            
            # Créer le vecteur temps
            time = np.arange(min_length // step) * step / self.original_editor.params.framerate
            
            # Échantillonner les données avec le même pas
            original_data = self.original_editor.audio_data[:min_length:step]
            processed_data = self.editor.audio_data[:min_length:step]
            
            # S'assurer que time et les données ont la même longueur
            plot_length = min(len(time), len(original_data), len(processed_data))
            time = time[:plot_length]
            original_data = original_data[:plot_length]
            processed_data = processed_data[:plot_length]
            
            # Tracer les données
            self.ax1.plot(time, original_data, 'b-', linewidth=0.5)
            self.ax1.set_xlabel('Temps (s)')
            self.ax1.set_ylabel('Amplitude')
            
            self.ax2.plot(time, processed_data, 'r-', linewidth=0.5)
            self.ax2.set_xlabel('Temps (s)')
            self.ax2.set_ylabel('Amplitude')
            
            # Ajuster les limites des axes y pour une meilleure visualisation
            max_amplitude = max(
                np.abs(original_data).max(),
                np.abs(processed_data).max()
            )
            y_limit = max_amplitude * 1.1  # Ajouter une marge de 10%
            
            self.ax1.set_ylim(-y_limit, y_limit)
            self.ax2.set_ylim(-y_limit, y_limit)
            
            # Ajouter une grille
            self.ax1.grid(True, alpha=0.3)
            self.ax2.grid(True, alpha=0.3)
            
            # Ajuster la mise en page
            self.fig.tight_layout()
            
            # Rafraîchir le canvas
            self.canvas.draw()
            
            # Mettre à jour les VU-mètres
            self.update_vu_meters()
            
            # Programmer la prochaine mise à jour si en lecture
            if self.playing:
                self.root.after(50, self.update_vu_meters)

    def create_vu_segments(self, canvas):
        """Crée les segments du VU-mètre avec une configuration améliorée"""
        segments = []
        cfg = self.vu_meter_config
        
        for i in range(cfg['num_segments']):
            x = i * (cfg['segment_width'] + cfg['segment_spacing']) + 5
            ratio = i / cfg['num_segments']
            
            if ratio < cfg['warning_threshold']:
                color = cfg['colors']['normal']
            elif ratio < cfg['critical_threshold']:
                color = cfg['colors']['warning']
            else:
                color = cfg['colors']['critical']
                
            segment = canvas.create_rectangle(
                x, 5, 
                x + cfg['segment_width'], 15,
                fill=cfg['colors']['inactive'], 
                outline='grey'
            )
            segments.append((segment, color))
        return segments

    def update_vu_meters(self):
        """Met à jour les VU-mètres avec gestion améliorée des niveaux"""
        if self.editor and self.original_editor:
            try:
                # Utiliser une fenêtre glissante plus grande pour plus de précision
                window_size = min(2048, len(self.editor.audio_data))
                
                # Calculer les niveaux RMS et les pics
                original_data = self.original_editor.audio_data[-window_size:]
                processed_data = self.editor.audio_data[-window_size:]
                
                # Normaliser selon le format audio (en tenant compte du type de données)
                dtype_info = np.iinfo(original_data.dtype)
                max_value = float(dtype_info.max)
                
                # Conversion en float32 pour les calculs
                original_data = original_data.astype(np.float32) / max_value
                processed_data = processed_data.astype(np.float32) / max_value
                
                # Calculer RMS et pics
                original_rms = np.sqrt(np.mean(np.square(original_data)))
                processed_rms = np.sqrt(np.mean(np.square(processed_data)))
                
                original_peak = np.max(np.abs(original_data))
                processed_peak = np.max(np.abs(processed_data))
                
                # Mettre à jour les pics avec hold
                self.update_peak_values('original', original_peak)
                self.update_peak_values('processed', processed_peak)
                
                # Mettre à jour les VU-mètres
                self.update_meter_segments(self.original_meter_canvas, 
                                        self.original_segments, 
                                        original_rms, 
                                        self.peak_values['original'])
                
                self.update_meter_segments(self.processed_meter_canvas, 
                                         self.processed_segments, 
                                         processed_rms,
                                         self.peak_values['processed'])
                
                # Mettre à jour le label avec les informations détaillées
                rms_db = 20 * np.log10(max(processed_rms, 1e-10))
                peak_db = 20 * np.log10(max(self.peak_values['processed'], 1e-10))
                
                if processed_peak > self.vu_meter_config['critical_threshold']:
                    color = 'red'
                    status = "DISTORSION"
                elif processed_peak > self.vu_meter_config['warning_threshold']:
                    color = '#FFA500'  # Orange
                    status = "ATTENTION"
                else:
                    color = 'green'
                    status = "OK"
                
                self.distortion_label.config(
                    text=f"{status} | RMS: {rms_db:.1f} dB | Pic: {peak_db:.1f} dB",
                    fg=color
                )
                
                # Programmer la prochaine mise à jour si en lecture
                if self.playing:
                    self.root.after(50, self.update_vu_meters)
                    
            except Exception as e:
                print(f"Erreur dans update_vu_meters: {str(e)}")

    def update_peak_values(self, meter_type, new_peak):
        """Gère la mise à jour des valeurs de pic avec hold"""
        if new_peak > self.peak_values[meter_type]:
            self.peak_values[meter_type] = new_peak
            
            # Annuler le timer précédent s'il existe
            if self.peak_hold_timers[meter_type]:
                self.root.after_cancel(self.peak_hold_timers[meter_type])
            
            # Créer un nouveau timer pour réinitialiser le pic
            self.peak_hold_timers[meter_type] = self.root.after(
                self.vu_meter_config['peak_hold_time'],
                lambda: self.reset_peak(meter_type)
            )

    def reset_peak(self, meter_type):
        """Réinitialise la valeur de pic pour un mètre donné"""
        self.peak_values[meter_type] = 0.0
        self.peak_hold_timers[meter_type] = None

    def update_meter_segments(self, canvas, segments, level, peak_level):
        """Met à jour les segments d'un VU-mètre avec affichage des pics"""
        try:
            cfg = self.vu_meter_config
            
            # Ajuster le niveau pour une meilleure visualisation
            level = min(1.0, level * 1.5)  # Amplifier légèrement pour une meilleure visibilité
            peak_level = min(1.0, peak_level * 1.5)
            
            active_segments = int(level * len(segments))
            peak_segment = int(peak_level * len(segments))
            
            for i, (segment, color) in enumerate(segments):
                if i < active_segments:
                    canvas.itemconfig(segment, fill=color)
                elif i == peak_segment:
                    canvas.itemconfig(segment, fill=cfg['colors']['peak'])
                else:
                    canvas.itemconfig(segment, fill=cfg['colors']['inactive'])
                    
        except Exception as e:
            print(f"Erreur dans update_meter_segments: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioEditorGUI(root)
    root.mainloop() 