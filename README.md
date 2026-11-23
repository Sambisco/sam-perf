# SAM-PERF

Application web de gestion pour le Programme de Formation École-Entreprise (PFPE) - Ministère de la Formation Professionnelle et Technique du Sénégal.

Développée en Python / Flask.

## Ce que fait l'application

### 1. Connexion
- Page de connexion "Bienvenue à SAM-PERF"
- Connexion par Email ou Téléphone + Mot de passe
- Compte utilisateur avec rôle (ex: Directeur, Admin...)

### 2. Service GM - Gestion des Matières
Tableau de bord dynamique "Bienvenue au Service GM" :
- Matière, Stock, Entrée, Sortie
- Carburant, Réception, Dotation, Affectation
- Indicateurs par année (2024, 2025...) et par mois
- Changement de thème / couleur de l'interface

Gestion complète :
- Catégorie
- Matière
- Entrée (Bons d'Entrée - B.E)
- Sortie
- Affectation
- Mutation
- Fournisseur
- Carburant

### 3. Service RH - Gestion des Ressources Humaines
Tableau de bord "Bienvenue au Service RH" :
- Recrutement, Contrat, Employé, Départ
- Affectation, Congé, Congé maternité
- Pointage, Salaire de base, Indemnité, Charges

Gestion complète :
- Antenne Régionale
- Service
- Recrutement
- Contrat
- Employé
- Départ
- G. administratif
- Rémunération
- Pointage

### 4. Pointage par Reconnaissance Faciale
- Page "Pointage jour"
- Détection du visage par webcam
- Reconnaissance faciale automatique de l'employé
- Message : "Pointage enregistré"
- Affichage de la fiche de l'employé pointé

### 5. Tableaux de bord et Graphiques
- Graphiques en barres, courbes, camembert
- Par mois : Octobre, Novembre, Décembre...
- Visualisation des entrées, sorties, salaires...
- Possibilité de télécharger les graphiques en image

### 6. Export et Documents PDF
- Export des listes en EXCEL et PDF
- Génération de Bon d'Entrée en PDF avec en-tête officiel PFPE
- Génération de Bulletin de Paie / Bulletin de Salaire en PDF
- Filtre par date (De / À)
- Recherche, pagination

## Technologies
- Python
- Flask (app.py)
- HTML / CSS / JS (templates/ + static/)
- InsightFace (reconnaissance faciale)
- Génération PDF
- Export Excel

## Structure du projet
- app.py : Fichier principal Flask
- controller_g/ : Logique métier
- templates/ : Pages HTML
- static/ : CSS, JS, images
- pdf/ : Génération des PDF
- aff.py : Affichage
- portail.html : Portail
- generate_cert.py : Génération certificat HTTPS
- requirements.txt : Dépendances

## Installation
pip install -r requirements.txt

## Lancer le projet
python app.py

Puis ouvrir :
http://127.0.0.1:5000

## Auteur
Developed by Sam Perf
Copyright 2025 - Sam Perf
