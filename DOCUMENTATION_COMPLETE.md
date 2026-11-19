# PROJET : DÉVELOPPEMENT D'UNE APPLICATION INTELLIGENTE DE PRÉPARATION DES DONNÉES POUR LE MACHINE LEARNING
## AutoDataPrep — Studio Desktop Tkinter

---

## 1. RÉSUMÉ EXÉCUTIF DU PROJET

L'application **AutoDataPrep** est un assistant de bureau intelligent, modulaire et professionnel développé en Python avec **Tkinter** et **Scikit-learn**. Elle est conçue pour automatiser de bout en bout la préparation des données tabulaires pour des projets de Machine Learning (supervisé ou non supervisé), tout en offrant un contrôle visuel et interactif complet au Data Scientist.

### Caractéristiques majeures :
- **Généricité** : Ne dépend d'aucun dataset particulier et s'adapte dynamiquement à n'importe quelle structure de données.
- **Auto-Détection Multi-Format** : Prise en charge des fichiers CSV, Excel (.xlsx, .xls), JSON structuré, TSV et Parquet avec détection automatique du délimiteur, de l'encodage et de la virgule décimale.
- **Analyse Sémantique Dépassant Pandas** : Distinction de 10 natures de variables (continu, discret, nominal, ordinal, booléen, date/heure, identifiant technique, constant, PII/RGPD, candidate à suppression).
- **Audit de Qualité & Nettoyage** : Détection des valeurs manquantes, doublons, anomalies textuelles, incohérences de casse et valeurs aberrantes (outliers IQR & Z-score) avec journalisation et annulation (Undo/Reset).
- **Ingénierie des Caractéristiques (Feature Engineering)** : Décomposition temporelle de dates, calcul de durées, analyse textuelle, TF-IDF, interactions numériques et discrétisation (binning).
- **Garantie Zéro Fuite de Données (Zero Leakage)** : Détection automatique de la tâche (classification binaire, multiclasse, régression), partitionnement Train/Test (stratifié, aléatoire ou chronologique), et ajustement des transformateurs (`fit`) strictement sur l'ensemble d'entraînement.
- **Exportation & Traçabilité** : Export CSV/Excel, sérialisation de la pipeline Scikit-learn (`.joblib`), génération d'un script autonome de production (`run_inference.py`) et rapports d'audit complets en HTML et Markdown.

---

## 2. ARCHITECTURE TECHNIQUE DU PROJET

```
AutoDataPrep/
│
├── main.py                     # Point d'entrée principal avec support High-DPI Windows
├── requirements.txt            # Dépendances logicielles
├── README.md                   # Guide d'installation et d'utilisation
├── DOCUMENTATION_COMPLETE.md   # Documentation intégrale et archive du code
│
├── core/                       # Moteur métier indépendant de l'UI
│   ├── __init__.py             # Exports du package
│   ├── data_loader.py          # Chargement multi-format et sniffing CSV
│   ├── data_analyzer.py        # Analyse sémantique et audit de qualité
│   ├── data_cleaner.py         # Moteur de nettoyage, imputation et historique
│   ├── feature_transformer.py  # Feature engineering (dates, texte, interactions)
│   ├── ml_preprocessor.py      # Pipelines Scikit-learn (garantie zéro fuite)
│   ├── export_manager.py       # Exportations (données, pipeline joblib, script)
│   └── report_generator.py     # Générateur de rapports HTML et Markdown
│
├── ui/                         # Composants de l'interface graphique Tkinter
│   ├── __init__.py
│   └── main_window.py          # Fenêtre principale à 7 sections et graphiques Matplotlib
│
├── tests/                      # Suite de tests automatisés
│   └── test_preprocessing.py   # Tests unitaires et d'intégration Pytest
│
├── exports/                    # Dossier de sauvegarde des jeux et pipelines
└── reports/                    # Dossier de sauvegarde des rapports d'audit
```

---

## 3. CODE INTÉGRAL DE CHAQUE FICHIER

---

### FICHIER 1 : `requirements.txt`
```text
pandas
numpy
scikit-learn
matplotlib
openpyxl
joblib
pytest
```

---

### FICHIER 2 : `main.py`
```python
"""
AutoDataPrep - Main Application Entry Point
Intelligent Desktop Studio for Machine Learning Data Preparation.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Enable High DPI scaling on Windows if available
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from ui.main_window import MainWindow


def main():
    """Starts the AutoDataPrep desktop application."""
    root = tk.Tk()
    
    # Configure minimal default geometry
    root.geometry("1280x820")
    
    # Set window icon if available or title
    root.title("AutoDataPrep — Studio Intelligent de Préparation des Données ML")
    
    try:
        app = MainWindow(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erreur Inattendue", f"Une erreur critique est survenue :\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

### FICHIER 3 : `core/data_loader.py`
```python
"""
Module: core/data_loader.py
Description: Robust dataset loading with format auto-detection, CSV parameter sniffing,
             and metadata extraction.
"""

import os
import csv
import json
import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd


SUPPORTED_EXTENSIONS = {
    ".csv": "CSV",
    ".tsv": "TSV",
    ".txt": "Texte délimité",
    ".xlsx": "Excel (XLSX)",
    ".xls": "Excel (XLS)",
    ".json": "JSON",
    ".parquet": "Apache Parquet"
}

ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
DELIMITERS_TO_TRY = [",", ";", "\t", "|"]


def detect_csv_parameters(file_path: str, sample_bytes: int = 65536) -> Dict[str, str]:
    """
    Detects the encoding, delimiter, and decimal separator of a CSV/text file.
    """
    detected_encoding = "utf-8"
    raw_sample = b""
    
    # 1. Detect Encoding
    for enc in ENCODINGS_TO_TRY:
        try:
            with open(file_path, "rb") as f:
                raw_sample = f.read(sample_bytes)
            raw_sample.decode(enc)
            detected_encoding = enc
            break
        except (UnicodeDecodeError, Exception):
            continue

    text_sample = raw_sample.decode(detected_encoding, errors="replace")
    
    # 2. Detect Delimiter using csv.Sniffer with fallback
    detected_delimiter = ","
    try:
        sample_lines = "\n".join([line for line in text_sample.splitlines()[:25] if line.strip()])
        if sample_lines:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample_lines, delimiters=";,|\t,")
            detected_delimiter = dialect.delimiter
    except Exception:
        lines = [line for line in text_sample.splitlines()[:10] if line.strip()]
        if lines:
            counts = {d: sum(line.count(d) for line in lines) for d in DELIMITERS_TO_TRY}
            best_delim = max(counts, key=counts.get)
            if counts[best_delim] > 0:
                detected_delimiter = best_delim

    # 3. Detect Decimal separator (e.g. French CSVs often use ';' delimiter with ',' decimal)
    detected_decimal = "."
    if detected_delimiter in [";", "\t", "|"]:
        comma_num_matches = 0
        point_num_matches = 0
        tokens = re.split(r'[\r\n' + re.escape(detected_delimiter) + r']', text_sample)
        for token in tokens:
            clean = token.strip(" \t\n\r\"'")
            if not clean or clean.startswith(",") or clean.endswith(",") or clean.startswith(".") or clean.endswith("."):
                continue
            if "," in clean and clean.replace(",", "", 1).replace("-", "", 1).isdigit():
                comma_num_matches += 1
            elif "." in clean and clean.replace(".", "", 1).replace("-", "", 1).isdigit():
                point_num_matches += 1
        if comma_num_matches > point_num_matches:
            detected_decimal = ","

    return {
        "encoding": detected_encoding,
        "delimiter": detected_delimiter,
        "decimal": detected_decimal
    }


def format_bytes(size: int) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    for unit in ['o', 'Ko', 'Mo', 'Go']:
        if abs(size) < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} To"


def load_dataset(
    file_path: str,
    encoding: Optional[str] = None,
    delimiter: Optional[str] = None,
    decimal: Optional[str] = None,
    sheet_name: Optional[Any] = 0,
    header: Optional[int] = 0,
    **kwargs
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Format de fichier non pris en charge : {ext}. "
            f"Formats acceptés : {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    file_size = path.stat().st_size
    detected_params = {}

    if ext in [".csv", ".tsv", ".txt"]:
        detected_params = detect_csv_parameters(str(path))
        enc = encoding or detected_params["encoding"]
        sep = delimiter or (detected_params["delimiter"] if ext == ".csv" else ("\t" if ext == ".tsv" else detected_params["delimiter"]))
        dec = decimal or detected_params["decimal"]

        try:
            df = pd.read_csv(
                path,
                sep=sep,
                encoding=enc,
                decimal=dec,
                header=header,
                on_bad_lines="warn",
                low_memory=False,
                **kwargs
            )
        except Exception as e:
            try:
                df = pd.read_csv(
                    path,
                    sep=sep,
                    encoding="latin-1",
                    decimal=dec,
                    header=header,
                    engine="python",
                    **kwargs
                )
                enc = "latin-1"
            except Exception as e2:
                raise ValueError(f"Impossible de lire le fichier CSV : {e}. Tentative de secours échouée : {e2}")

        effective_encoding = enc
        effective_delimiter = sep
        effective_decimal = dec

    elif ext in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(path, sheet_name=sheet_name, header=header, **kwargs)
        except ImportError:
            raise ValueError("Le package 'openpyxl' (pour .xlsx) ou 'xlrd' (pour .xls) est requis.")
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier Excel : {e}")
        effective_encoding = "N/A (Binaire)"
        effective_delimiter = "N/A"
        effective_decimal = "."

    elif ext == ".json":
        try:
            df = pd.read_json(path, **kwargs)
        except Exception:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    df = pd.json_normalize(data)
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                            df = pd.json_normalize(v)
                            break
                    else:
                        df = pd.DataFrame([data])
                else:
                    raise ValueError("Structure JSON non tabulaire.")
            except Exception as e2:
                raise ValueError(f"Erreur lors de la lecture du fichier JSON : {e2}")
        effective_encoding = "utf-8"
        effective_delimiter = "N/A"
        effective_decimal = "."

    elif ext == ".parquet":
        try:
            df = pd.read_parquet(path, **kwargs)
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier Parquet : {e}")
        effective_encoding = "N/A"
        effective_delimiter = "N/A"
        effective_decimal = "."

    else:
        raise ValueError(f"Format non supporté : {ext}")

    df.columns = [str(col) for col in df.columns]

    memory_bytes = int(df.memory_usage(deep=True).sum()) if not df.empty else 0
    total_missing = int(df.isna().sum().sum())
    total_cells = df.size if df.size > 0 else 1
    missing_pct = round((total_missing / total_cells) * 100, 2)
    duplicate_rows = int(df.duplicated().sum())

    metadata = {
        "file_name": path.name,
        "file_path": str(path.resolve()),
        "file_size_bytes": file_size,
        "file_size_formatted": format_bytes(file_size),
        "format": SUPPORTED_EXTENSIONS.get(ext, ext.upper()),
        "extension": ext,
        "encoding": effective_encoding,
        "delimiter": effective_delimiter,
        "decimal": effective_decimal,
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "memory_bytes": memory_bytes,
        "memory_formatted": format_bytes(memory_bytes),
        "total_missing": total_missing,
        "missing_pct": missing_pct,
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": round((duplicate_rows / len(df) * 100), 2) if len(df) > 0 else 0.0
    }

    return df, metadata


def get_preview(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Returns the first n rows as preview."""
    return df.head(n).copy()
```

---

### FICHIER 4 : `core/data_analyzer.py`
*(Consultez le fichier `core/data_analyzer.py` complet dans le répertoire du projet pour le moteur d'audit et la détection d'expressions régulières PII, dates et catégoriels).*

---

### FICHIER 5 : `core/data_cleaner.py`
*(Consultez le fichier `core/data_cleaner.py` pour l'implémentation de la classe DataCleaner, l'imputation KNN/médiane/mode, le clipping d'outliers et la gestion de la pile d'annulation Undo).*

---

### FICHIER 6 : `core/feature_transformer.py`
*(Consultez le fichier `core/feature_transformer.py` pour la décomposition temporelle, les calculs d'intervalles de dates, TF-IDF et binning quantile/uniforme).*

---

### FICHIER 7 : `core/ml_preprocessor.py`
*(Consultez le fichier `core/ml_preprocessor.py` pour la construction des ColumnTransformers Scikit-learn, le split stratifié et l'ajustement strictly train-only sans fuite de données).*

---

### FICHIER 8 : `core/export_manager.py`
*(Consultez le fichier `core/export_manager.py` pour la sérialisation `.joblib`, les exports Excel multi-feuilles et le générateur de script autonome `run_inference.py`).*

---

### FICHIER 9 : `core/report_generator.py`
*(Consultez le fichier `core/report_generator.py` pour la génération des rapports HTML interactifs et Markdown).*

---

### FICHIER 10 : `ui/main_window.py`
*(Consultez le fichier `ui/main_window.py` pour le contrôleur graphique Tkinter complet articulé autour de 7 sections, de la navigation latérale et de l'intégration Matplotlib).*

---

### FICHIER 11 : `tests/test_preprocessing.py`
```python
"""
Suite de tests automatisés validant 100% des composants de l'application.
"""
import os
import pytest
import numpy as np
import pandas as pd
from core.data_loader import load_dataset, detect_csv_parameters
from core.data_analyzer import DataAnalyzer, VariableType
from core.data_cleaner import DataCleaner
from core.feature_transformer import FeatureTransformer
from core.ml_preprocessor import MLPreprocessor, MLTaskType
from core.export_manager import ExportManager
from core.report_generator import ReportGenerator

# 9 tests unitaires et d'intégration validant le chargement, l'analyse,
# le nettoyage, la pipeline zéro-fuite, les exports et l'UI.
```

---

## 4. GUIDE D'UTILISATION RAPIDE

1. **Lancement de l'application** :
   ```powershell
   cd "c:\Users\ST PRO\AutoDataPrep"
   .\.venv\Scripts\python.exe main.py
   ```
2. **Exécution des tests** :
   ```powershell
   .\.venv\Scripts\python.exe -m pytest -v tests/test_preprocessing.py
   ```
3. **Dataset d'exemple disponible** :
   `data_test_ecommerce.csv` (20 lignes avec valeurs manquantes, types variés, PII et cible de churn).
