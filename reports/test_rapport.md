# AutoDataPrep - Rapport d'Audit & Préparation des Données

**Dataset :** data_test_ecommerce.csv  
**Date :** 05/11/2026 à 14:12:52  
**Dimensions :** 20 lignes × 17 colonnes  
**Mémoire approximative :** 0.1 Mo  

## 1. Caractéristiques Initiales & Identification Sémantique

| Variable | Type Sémantique | Confiance | Manquantes (%) | Distinctes (%) | Recommandation |
|---|---|---|---|---|---|
| `client_id` | Identifiant technique | Élevée | 0.0% | 100.0% | Exclure des variables prédictives |
| `age` | Numérique continu | Élevée | 5.0% | 100.0% | Imputation par la moyenne |
| `salaire` | Numérique continu | Élevée | 5.0% | 100.0% | Imputation par la moyenne |
| `ville` | Catégoriel nominal | Élevée | 0.0% | 70.0% | Suppression des espaces (strip) |
| `date_inscription` | Temporel (Date/Heure) | Élevée | 0.0% | 100.0% | Conserver |
| `est_fidele` | Booléen | Élevée | 0.0% | 10.0% | Conserver |
| `commentaire` | Texte libre | Élevée | 0.0% | 100.0% | Conserver |
| `score_satisfaction` | Numérique continu | Élevée | 0.0% | 60.0% | Conserver |
| `email_client` | Donnée sensible / PII | Élevée | 0.0% | 100.0% | Anonymisation ou Exclusion |
| `statut_tier` | Catégoriel nominal | Élevée | 0.0% | 20.0% | Conserver |
| `churn` | Booléen | Élevée | 0.0% | 10.0% | Conserver |


## 2. Audit de Qualité des Données

| Variable | Problème | Gravité | Action Proposée | État |
|---|---|---|---|---|
| `client_id` | Identifiant technique | Moyenne | Exclure des variables prédictives | À traiter |
| `age` | Valeurs manquantes | Faible | Imputation par la moyenne | À traiter |
| `salaire` | Valeurs manquantes | Faible | Imputation par la moyenne | À traiter |
| `ville` | Espaces superflus (début/fin) | Faible | Suppression des espaces (strip) | À traiter |
| `ville` | Incohérence de casse (majuscules/minuscules) | Moyenne | Suppression des espaces (strip) | À traiter |
| `email_client` | Donnée Personnelle Sensible (Email (Nom colonne)) | Critique | Anonymisation ou Exclusion | À traiter |


## 3. Opérations de Nettoyage Exécutées

| Horodatage | Opération | Colonne | Stratégie | Détails |
|---|---|---|---|---|
| 2026-11-05 14:12:51 | Imputation Valeurs Manquantes | `age` | mean | 1 valeurs imputées par la moyenne (39.158). |
| 2026-11-05 14:12:51 | Nettoyage Textuel | `ville` | strip=True, case=lower | Espaces nettoyés et casse normalisée ('lower'). |
| 2026-11-05 14:12:51 | Traitement Outliers | `salaire` | IQR (clip) | Aucun outlier détecté en dehors de l'intervalle [1750.0, 107750.0]. |
| 2026-11-05 14:12:51 | Suppression Doublons | `[Toutes]` | Conserver 'first' | 0 lignes dupliquées supprimées. |
| 2026-11-05 14:12:51 | Ingénierie Temporelle | `date_inscription` | Décomposition temporelle | Création de 6 variables : date_inscription_year, date_inscription_month, date_inscription_day, date_inscription_dayofweek, date_inscription_quarter, date_inscription_is_weekend |


## 4. Nouvelles Caractéristiques Créées

| Type | Source | Nouvelles Colonnes | Justification |
|---|---|---|---|
| Temporel | `date_inscription` | `date_inscription_year, date_inscription_month, date_inscription_day, date_inscription_dayofweek, date_inscription_quarter, date_inscription_is_weekend` | Décomposition temporelle de date_inscription en variables exploitables par les modèles ML. |


## 5. Préparation Machine Learning

*Aucune configuration ML appliquée.*

