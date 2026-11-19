# AutoDataPrep — Studio Intelligent de Préparation des Données pour le Machine Learning

**AutoDataPrep** est une application complète, professionnelle, modulaire et générique de préparation des données pour les projets de Data Science et Machine Learning. Elle automatise l'ensemble des étapes de préparation des données tout en offrant un contrôle visuel et interactif à l'utilisateur.

L'application est disponible en **deux versions** :
- **Version Bureau** : Interface Tkinter classique (existant)
- **Version Web** : Interface React.js moderne avec API FastAPI (nouveau)

---

## 🌟 Fonctionnalités Principales

1. **Importation Multi-Format avec Auto-Détection Intelligente** :
   - Prise en charge des formats CSV, TSV, TXT, Excel (`.xlsx`, `.xls`), JSON structuré et Parquet.
   - Sniffer automatique de délimiteur (`,`, `;`, `\t`, `|`), de l'encodage (`utf-8`, `latin-1`, `cp1252`) et du séparateur décimal (`.` vs `,`).
   - Possibilité de corriger manuellement les paramètres de lecture.

2. **Analyse Sémantique Approfondie des Variables** :
   - Identification intelligente dépassant les types techniques Pandas :
     - *Numérique continu*
     - *Numérique discret*
     - *Catégoriel nominal*
     - *Catégoriel ordinal* (détection de hiérarchies sémantiques comme `faible/moyen/fort`, ratings)
     - *Booléen*
     - *Texte libre*
     - *Temporel (Date/Heure)*
     - *Identifiant technique* (UUID, index séquentiel)
     - *Constant ou quasi-constant*
     - *Données personnelles sensibles / PII* (emails, numéros de téléphone, NIR/sécu, adresses IP).
   - Fiche d'audit détaillée par variable avec niveau de confiance (`Élevée`, `Moyenne`, `Faible`).

3. **Audit de Qualité & Nettoyage Avancé** :
   - Tableau d'audit avec classification par niveau de gravité (`Critique`, `Élevée`, `Moyenne`, `Faible`).
   - Traitement des valeurs manquantes : médiane (pour distributions asymétriques), moyenne, mode, modalité `'Inconnu'`, KNN Imputer, ou suppression justifiée.
   - Détection et suppression des doublons.
   - Normalisation textuelle (espaces superflus, harmonisation de casse, modalités rares).
   - Détection et traitement des outliers par les méthodes IQR (Interquartile Range) et Z-Score (écrêtage/winsorisation ou filtrage).
   - Journalisation complète des opérations (Changelog) avec fonction **Annuler (Undo)** et **Réinitialiser**.

4. **Ingénierie & Transformation des Variables (Feature Engineering)** :
   - Décomposition temporelle (année, mois, jour, jour de semaine, week-end, heure, trimestre, jours écoulés).
   - Calcul de durées entre deux colonnes temporelles.
   - Extraction textuelle (longueur en caractères, nombre de mots, TF-IDF).
   - Interactions numériques (ratios, produits, sommes, différences).
   - Discrétisation continue (Binning par quantiles ou intervalles uniformes).

5. **Préparation Machine Learning avec Garantie "Zéro Fuite" (Zero Data Leakage)** :
   - Mode Supervisé : Détection automatique de la nature de la tâche (*Classification Binaire*, *Classification Multiclasse*, *Régression*), contrôle d'absence sur la cible, analyse du déséquilibre de classes et alertes de fuite de données (*Data Leakage*).
   - Partitionnement Train/Test (stratifié, aléatoire ou chronologique).
   - Pipelines Scikit-learn (`ColumnTransformer`, `Pipeline`) ajustées **strictement sur l'ensemble d'entraînement (`X_train`)** et appliquées sur le test.
   - Mode Non-Supervisé (mise à l'échelle pour K-Means, PCA).
   - Recommandations d'algorithmes adaptées à la tâche.

6. **Exportation & Traçabilité Complète** :
   - Export du dataset nettoyé (CSV, Excel).
   - Export des splits ML (`X_train`, `X_test`, `y_train`, `y_test`) en CSV séparés ou Excel multi-feuilles.
   - Sérialisation de la pipeline Scikit-learn entraînée (`.joblib`).
   - Génération automatique d'un script Python autonome de production (`run_inference.py`) pour appliquer la pipeline sur de nouvelles données entrantes.
   - Génération de rapports d'audit exhaustifs au format **HTML** (avec design responsive, KPIs et badges) et **Markdown** (`.md`).

---

## 📁 Architecture du Projet

```
AutoDataPrep/
│
├── main.py                     # Point d'entrée Tkinter (version bureau)
├── api_server.py               # Point d'entrée FastAPI (version web)
├── requirements.txt            # Dépendances Python requises
├── README.md                   # Documentation technique et guide d'utilisation
│
├── core/                       # Moteur métier indépendant de l'interface
│   ├── __init__.py
│   ├── data_loader.py          # Chargement multi-format et sniffing CSV
│   ├── data_analyzer.py        # Analyse sémantique, types et audit de qualité
│   ├── data_cleaner.py         # Moteur de nettoyage, imputation et traçabilité
│   ├── feature_transformer.py  # Feature engineering (dates, texte, interactions)
│   ├── ml_preprocessor.py      # Pipelines Scikit-learn et garantie zéro-leakage
│   ├── export_manager.py       # Exportations (données, pipeline joblib, script)
│   └── report_generator.py     # Générateur de rapports HTML et Markdown
│
├── api/                        # API FastAPI pour la version web
│   ├── main.py                 # Application FastAPI
│   ├── routes/                 # Endpoints API
│   │   ├── dataset.py
│   │   ├── analysis.py
│   │   ├── cleaning.py
│   │   ├── transforms.py
│   │   ├── ml.py
│   │   └── export.py
│   └── models/                 # Pydantic models
│
├── frontend/                   # Application React.js (version web)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/                # Client API
│       ├── context/            # Contexte d'état global
│       ├── components/         # Composants UI
│       └── pages/              # Pages de l'application
│
├── ui/                         # Composants de l'interface graphique Tkinter
│   ├── __init__.py
│   └── main_window.py          # Fenêtre principale, navigation à 7 sections et graphiques
│
├── tests/                      # Suite de tests automatisés
│   └── test_preprocessing.py   # Tests unitaires et d'intégration (Pytest)
│
├── exports/                    # Répertoire généré pour les fichiers exportés
└── reports/                    # Répertoire généré pour les rapports d'audit
```

---

## 🚀 Installation & Exécution

### Prérequis
- Python 3.9 ou version supérieure.
- Node.js 18+ (pour la version web uniquement).
- Tkinter (inclus par défaut avec l'installateur standard de Python sur Windows/macOS).

### 1. Cloner ou ouvrir le dossier du projet
```powershell
cd "c:\Users\ST PRO\AutoDataPrep"
```

### 2. Créer et activer un environnement virtuel
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances Python
```powershell
pip install -r requirements.txt
```

---

## 📱 Version Web (Interface React.js Moderne)

### Installation des dépendances Frontend
```powershell
cd frontend
npm install
```

### Lancement de l'application Web

**Terminal 1 - API FastAPI :**
```powershell
# Retournez à la racine du projet
cd ..
python api_server.py
```

**Terminal 2 - Frontend React :**
```powershell
cd frontend
npm run dev
```

L'application sera accessible à l'adresse : **http://localhost:5173**

La documentation API est disponible à : **http://localhost:8001/docs**

---

## 🖥️ Version Bureau (Interface Tkinter)

### Lancement de l'application de bureau
```powershell
python main.py
```

---

## 🧪 Exécution des Tests Automatisés

La suite de tests vérifie l'ensemble des modules (chargement, analyse sémantique, nettoyage, feature engineering, pipelines sans fuite de données, exports, interface) :

```powershell
python -m pytest -v tests/test_preprocessing.py
```

---

## 🖥️ Guide d'Utilisation de l'Interface

L'application s'organise autour d'une barre latérale ergonomique donnant accès à 7 sections :

1. **📁 1. Accueil & Import** :
   - Cliquez sur **« Charger un fichier... »** pour importer votre fichier (CSV, Excel, JSON...).
   - L'application détecte automatiquement le séparateur, l'encodage et le format décimal. Si nécessaire, cliquez sur **« Paramètres CSV »** pour ajuster manuellement.
   - Les cartes KPI affichent les dimensions, la mémoire et le volume de valeurs manquantes/doublons.
   - Parcourez les données avec les boutons **« Précédent »** et **« Suivant »**.
   - Cliquez sur le bouton vert **« 🚀 Lancer l'Analyse Intelligente Complète »**.

2. **📊 2. Analyse Exploratoire** :
   - Sélectionnez n'importe quelle variable dans le menu déroulant à gauche pour afficher sa **Fiche Variable** (type sémantique, confiance, statistiques descriptives, problèmes détectés, recommandations).
   - Visualisez les distributions sur le volet droit : *Histogramme avec distribution*, *Boîte à moustaches (Boxplot)*, *Bar Chart des fréquences* ou *Matrice de corrélation*.

3. **🔍 3. Audit de Qualité** :
   - Tableau synthétique de l'audit de qualité avec codes couleur de gravité : Critique (rouge), Élevée (orange), Moyenne (jaune), Faible (vert).
   - Cliquez sur **« ✨ Nettoyer Automatiquement les Recommandations Sûres »** pour appliquer en un clic les corrections sans risque méthodologique (suppression des doublons exacts, nettoyage des espaces, suppression des colonnes constantes).

4. **🧹 4. Nettoyage** :
   - Sélectionnez un onglet d'action à gauche :
     - **Imputation** : médiane, moyenne, mode, constante, suppression.
     - **Outliers** : détection IQR ou Z-Score avec écrêtage (clip) ou suppression.
     - **Texte & Doublons** : strip, normalisation minuscules/majuscules, suppression de doublons.
   - Consultez le **Journal des opérations** à droite.
   - Utilisez **« ↩️ Annuler (Undo) »** pour revenir en arrière ou **« 🔄 Réinitialiser »** pour restaurer l'état brut initial.

5. **⚙️ 5. Transformations** :
   - **Temporel** : Décomposez une date en année, mois, jour, indicateur week-end, heure.
   - **Combinaison** : Créez des interactions numériques (ratios, produits, sommes, différences).
   - **Discrétisation** : Découpez une variable continue en classes/quantiles.
   - Le journal consigne chaque nouvelle colonne générée avec sa justification.

6. **🤖 6. Configuration ML** :
   - Choisissez entre **Apprentissage Supervisé** et **Non Supervisé**.
   - En mode supervisé, sélectionnez votre colonne cible : l'application détecte s'il s'agit d'une classification binaire, multiclasse ou d'une régression, et contrôle le déséquilibre de classe.
   - Configurez la proportion de test (ex: 20%) et la stratégie de split (*Stratifié*, *Aléatoire*, *Chronologique*).
   - Sélectionnez la normalisation numérique (*StandardScaler*, *MinMaxScaler*, *RobustScaler*, *Aucun*) et l'encodage (*One-Hot*, *Ordinal*).
   - Cliquez sur **« ⚙️ Générer Pipeline & Préparer les Données »**.

7. **💾 7. Résultats & Export** :
   - Visualisez les jeux d'entraînement (`X_train`, `y_train`) et de test (`X_test`, `y_test`) prêts pour vos algorithmes.
   - Exportez en un clic :
     - Les données nettoyées (CSV ou Excel)
     - Les splits ML (fichiers CSV séparés ou Excel multi-feuilles)
     - La pipeline Scikit-learn sérialisée (`.joblib`)
     - Le script d'inférence autonome (`run_inference.py`)
     - Le rapport complet de préparation (ouvert directement dans votre navigateur web).

---

## 🛠️ Comment Ajouter de Nouvelles Transformations ?

L'architecture découplée permet d'ajouter très simplement de nouvelles fonctionnalités :

1. **Ajouter un nouvel encodeur ou scaler** :
   - Ouvrez `core/ml_preprocessor.py`.
   - Dans `build_supervised_pipeline`, ajoutez la condition dans `num_transformers` (ex: `QuantileTransformer`) ou `cat_transformers` (ex: `TargetEncoder`).
   - Mettez à jour les valeurs de `cb_scaler` dans `ui/main_window.py`.

2. **Ajouter une nouvelle transformation dans `core/feature_transformer.py`** :
   - Définissez votre méthode, par exemple :
     ```python
     def compute_custom_log(self, column: str) -> Tuple[pd.DataFrame, str]:
         new_col = f"log_{column}"
         self.df[new_col] = np.log1p(self.df[column].clip(lower=0))
         self.created_features.append({
             "type": "Logarithmique",
             "source_column": column,
             "created_columns": [new_col],
             "justification": f"Transformation log1p pour stabiliser la variance de {column}."
         })
         return self.df.copy(), new_col
     ```
   - Liez un bouton ou une option dans `ui/main_window.py` (Section 5).

---

## 🔒 Qualité, Sécurité & Bonnes Pratiques

- **Préservation des originaux** : Aucune modification destructrice n'affecte vos fichiers sources sur le disque.
- **Zéro fuite d'information** : Les transformateurs et imputeurs sont systématiquement ajustés (`fit`) sur les données d'entraînement uniquement, évitant le surapprentissage optimiste.
- **Protection des données sensibles** : Les colonnes contenant des PII (emails, téléphones, sécurité sociale) sont détectées et isolées avec alertes de conformité RGPD.
- **Réactivité de l'interface** : Tous les calculs lourds sont exécutés dans des threads d'arrière-plan avec indicateurs visuels de progression.
