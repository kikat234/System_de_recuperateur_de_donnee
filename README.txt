# Systéme de Récuperateur de Données

## Description


## Fonctionnalités
- Restaurer des fichiers supprimés
- Analyse d'un disque ou dossier
- Estimation du taux de recuperabilité des fichiers
- Extraction des fichier restaurés vers un dossier ou disque
- Gestion des erreurs et des logs

## Technologies utilisées
- python 3.12
- Tkinter: Conception de l'interface graphique
- os : Gestion des opérations système (chemins de fichiers, variables d'environnement, création/suppression de dossiers)
- datetime : Manipulation des dates et heures (horodatage, calculs de durée, formatage de dates)
- pathlib (Path) : Gestion moderne et orientée objet des chemins de fichiers et répertoires
- threading : Gestion du multithreading pour exécuter plusieurs tâches en parallèle
- platform : Détection d'informations sur le système d'exploitation et la plateforme d'exécution

### Étapes
1. Cloner le dépôt
```bash
   git clone https://github.com/kikat234/System_de_recuperateur_de_donnee.git
```
2. Creer un environnement virtuel
**Créer un environnement virtuel**
```bash
   python -m venv venv
   venv\Scripts\activate
```

3. Lancer le projet
```bash
   # python src/main.py 
```

## Utilisation
   ##Suppression  
1. Créer un dossier avec 4-5 fichiers (PDF, JPG, PNG, DOCX)
2. Copier sur une clé USB
3. Sélectionner tous les fichiers
4. Appuyer : Shift + Suppr
5. Confirmer la suppression
6. La clé est maintenant vide

  ##Restauration avec tonio recovery
1. Lancee le programme comme Administrateur
2. Onglet "Sélection & Analyse"
3. Choisir "Disque/USB"
4. Parcourir → Sélectionner la clé USB
5. Cliquer "Charger et Analyser"
6. Attendre 30-60 secondes

  ##Verification
1. Score de récupérabilité : >70% (VERT) = Données intactes
2. Fichiers détectés : 4-5 fichiers dans l'onglet "Récupération"
3. Extraction : 
   - Sélectionner les fichiers
   - "Extraire sélection"
   - Choisir un dossier
4. Ouvrir les fichiers extraits → Identiques aux originaux


## **📊 TABLEAU RÉCAPITULATIF**

| Test | Durée | Résultat Attendu | Preuve de Succès |
|------|-------|------------------|------------------|
| **Suppression** | 5 min | Score >70% (VERT) | Hash identiques |
| **Corruption** | 5 min | Score 40-60% (ORANGE) | Corruption visible dans image |


## Documentation
Le rapport complet du projet est disponible [ici](./rapport.pdf).
