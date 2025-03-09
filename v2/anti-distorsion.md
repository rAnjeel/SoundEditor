# Éditeur Audio avec Anti-Distorsion

## Description

Cet éditeur audio est un outil permettant de manipuler des fichiers WAV avec une attention particulière portée sur le contrôle de la distorsion. Il intègre plusieurs types d'anti-distorsion et des outils de visualisation en temps réel.

## Fonctionnalités Anti-Distorsion

### Types d'Anti-Distorsion Disponibles

1. **Soft** (-20 dB, ratio 2:1)

   - Compression douce pour une transition naturelle
   - Idéal pour le traitement vocal et instruments acoustiques
   - Seuil bas pour une action préventive

2. **Medium** (-15 dB, ratio 3:1)

   - Compression moyenne pour un contrôle équilibré
   - Bon compromis pour la plupart des sources audio
   - Préserve la dynamique tout en évitant la distorsion

3. **Hard** (-10 dB, ratio 4:1)

   - Compression plus agressive
   - Adapté aux signaux nécessitant un contrôle strict
   - Utile pour les instruments percussifs

4. **Limit** (-6 dB, ratio 10:1)

   - Limitation douce des pics
   - Excellent pour le mastering
   - Maintient la transparence sonore

5. **Brick** (-3 dB, ratio 20:1)
   - Limitation stricte
   - Protection maximale contre la distorsion
   - Idéal pour la diffusion broadcast

## Guide d'Utilisation

### Interface Principale

1. **Chargement du Fichier**

   - Cliquez sur "Charger un fichier WAV"
   - Sélectionnez votre fichier audio WAV

2. **Contrôle d'Amplitude**

   - Utilisez le slider pour ajuster l'amplitude (0.1 à 10.0)
   - Entrez une valeur précise dans le champ numérique
   - Cliquez sur "Valider" pour appliquer

3. **Anti-Distorsion**

   - Sélectionnez le type d'anti-distorsion dans le menu déroulant
   - Cliquez sur "Appliquer" pour traiter l'audio

4. **Visualisation**
   - Graphique supérieur : signal original
   - Graphique inférieur : signal traité
   - VU-mètres en temps réel pour les niveaux

### Monitoring des Niveaux

Le système inclut deux VU-mètres :

- **Original** : Affiche les niveaux du signal d'entrée
- **Traité** : Affiche les niveaux après traitement

Codes Couleurs :

- **Vert** : Niveaux normaux (-∞ à -10 dB)
- **Jaune** : Niveaux élevés (-10 à -3 dB)
- **Rouge** : Risque de distorsion (-3 à 0 dB)

### Lecture et Sauvegarde

- **Contrôles de lecture** : Play/Pause et Stop
- **Sauvegarde** : Exportez votre fichier traité en WAV

## Conseils d'Utilisation

1. **Choix du Type d'Anti-Distorsion**

   - Commencez par "Medium" pour un traitement général
   - Utilisez "Soft" pour les sources délicates
   - Passez à "Hard" ou "Limit" si nécessaire

2. **Monitoring**

   - Surveillez les VU-mètres pendant la lecture
   - Évitez les segments rouges prolongés
   - Utilisez le graphique pour visualiser l'impact du traitement

3. **Optimisation**
   - Ajustez l'amplitude avant d'appliquer l'anti-distorsion
   - Testez différents types pour trouver le meilleur résultat
   - Sauvegardez régulièrement vos modifications

## Notes Techniques

- Format supporté : WAV (8, 16, 24, 32 bits)
- Fréquences d'échantillonnage : toutes
- Traitement en temps réel
- Visualisation synchronisée
- Peak holding sur les VU-mètres

## Dépendances

- Python 3.x
- NumPy
- Matplotlib
- Tkinter
- PyAudio
- Pygame
