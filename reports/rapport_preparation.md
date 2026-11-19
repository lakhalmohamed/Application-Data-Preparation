# AutoDataPrep - Rapport d'Audit & Préparation des Données

**Dataset :** session_1793628535866_2nuw5rfxl_Test.xlsx  
**Date :** 02/11/2026 à 06:10:47  
**Dimensions :** 20 lignes × 8 colonnes  
**Mémoire approximative :** 7.2 Ko  

## 1. Caractéristiques Initiales & Identification Sémantique

| Variable | Type Sémantique | Confiance | Manquantes (%) | Distinctes (%) | Recommandation |
|---|---|---|---|---|---|
| `ID` | Identifiant technique | Élevée | 0.0% | 100.0% | Exclure des variables prédictives |
| `Name` | Catégoriel nominal | Élevée | 5.0% | 100.0% | Imputation par le mode (valeur la plus fréquente) |
| `Age` | Numérique continu | Moyenne | 10.0% | 83.33% | Imputation par la moyenne |
| `Gender` | Catégoriel nominal | Élevée | 5.0% | 21.05% | Imputation par le mode (valeur la plus fréquente) |
| `Email` | Donnée sensible / PII | Élevée | 5.0% | 89.47% | Anonymisation ou Exclusion |
| `Salary` | Numérique continu | Élevée | 10.0% | 83.33% | Imputation par la médiane |
| `Joining_Date` | Temporel (Date/Heure) | Élevée | 0.0% | 90.0% | Conserver |
| `Department` | Catégoriel nominal | Élevée | 0.0% | 30.0% | Harmonisation de la casse |


## 2. Audit de Qualité des Données

| Variable | Problème | Gravité | Action Proposée | État |
|---|---|---|---|---|
| `ID` | Identifiant technique | Moyenne | Exclure des variables prédictives | À traiter |
| `Name` | Valeurs manquantes | Faible | Imputation par le mode (valeur la plus fréquente) | À traiter |
| `Name` | Espaces superflus (début/fin) | Faible | Imputation par le mode (valeur la plus fréquente) | À traiter |
| `Name` | Incohérence de casse (majuscules/minuscules) | Moyenne | Imputation par le mode (valeur la plus fréquente) | À traiter |
| `Age` | Valeurs manquantes | Moyenne | Imputation par la moyenne | À traiter |
| `Gender` | Valeurs manquantes | Faible | Imputation par le mode (valeur la plus fréquente) | À traiter |
| `Email` | Valeurs manquantes | Faible | Anonymisation ou Exclusion | À traiter |
| `Email` | Donnée Personnelle Sensible (Email (Nom colonne)) | Critique | Anonymisation ou Exclusion | À traiter |
| `Salary` | Valeurs manquantes | Moyenne | Imputation par la médiane | À traiter |
| `Salary` | Valeurs aberrantes (Outliers IQR) | Élevée | Imputation par la médiane | À traiter |
| `Department` | Incohérence de casse (majuscules/minuscules) | Moyenne | Harmonisation de la casse | À traiter |


## 3. Opérations de Nettoyage Exécutées

*Aucune opération de nettoyage manuelle exécutée.*


## 4. Nouvelles Caractéristiques Créées

*Aucune nouvelle caractéristique créée.*


## 5. Préparation Machine Learning

*Aucune configuration ML appliquée.*

