# Interface Graphique de l'Éditeur Audio

## Vue d'ensemble

L'interface graphique permet de tester facilement les fonctionnalités de l'éditeur audio avec une interface utilisateur simple et intuitive.

## Fonctionnalités

- Chargement de fichiers WAV via une boîte de dialogue
- Lecture audio avec contrôles Play/Pause et Stop
- Contrôle d'amplitude double :
  - Slider visuel (0.1 à 10.0 par défaut)
  - Saisie directe de valeurs personnalisées
- Prévisualisation des modifications
- Sauvegarde du fichier modifié

## Composants de l'interface

1. **Bouton de chargement**

   - Ouvre une boîte de dialogue pour sélectionner un fichier WAV
   - Affiche le nom du fichier chargé

2. **Contrôle d'amplitude**

   - Slider permettant d'ajuster le facteur d'amplitude
   - Champ de saisie pour entrer une valeur précise
   - Bouton pour appliquer la valeur saisie
   - Validation des entrées avec messages d'erreur
   - Avertissement pour les valeurs élevées

3. **Contrôles de lecture**

   - Bouton Play/Pause pour contrôler la lecture
   - Bouton Stop pour arrêter la lecture

4. **Boutons d'action**
   - "Appliquer les modifications" : applique les changements
   - "Sauvegarder" : enregistre le fichier modifié

## Utilisation

1. Lancer l'application : `python interface.py`
2. Charger un fichier WAV
3. Ajuster l'amplitude :
   - Utiliser le slider pour des ajustements visuels
   - OU entrer une valeur précise dans le champ de saisie
4. Écouter le résultat avec les contrôles de lecture
5. Appliquer les modifications
6. Sauvegarder le fichier modifié

## Gestion des erreurs

- Validation des entrées numériques
- Messages d'erreur explicites
- Avertissements pour les valeurs extrêmes
- Protection contre les valeurs invalides

## Dépendances

- tkinter : interface graphique
- pygame : lecture audio
- numpy : traitement audio
