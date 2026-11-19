"""
Module: core/feature_transformer.py
Description: Feature engineering and transformation engine supporting numerical scalers,
             categorical encodings, temporal decomposition, text feature extraction,
             and feature combinations.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
    OneHotEncoder,
    OrdinalEncoder,
    PowerTransformer
)
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer


class FeatureTransformer:
    """Handles feature transformations and automated feature generation."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.created_features: List[Dict[str, Any]] = []

    def extract_datetime_features(
        self,
        column: str,
        extract_year: bool = True,
        extract_month: bool = True,
        extract_day: bool = True,
        extract_dayofweek: bool = True,
        extract_hour: bool = True,
        extract_is_weekend: bool = True,
        extract_quarter: bool = True,
        reference_date: Optional[str] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Extracts temporal features from a datetime column.
        
        Returns:
            Tuple of (updated DataFrame, list of new feature names)
        """
        if column not in self.df.columns:
            raise KeyError(f"Colonne introuvable : {column}")

        try:
            dt_series = pd.to_datetime(self.df[column], errors="coerce", format="mixed")
        except Exception:
            try:
                dt_series = pd.to_datetime(self.df[column], errors="coerce", dayfirst=True)
            except Exception:
                dt_series = pd.to_datetime(self.df[column], errors="coerce")

        if dt_series.isna().all() and len(self.df) > 0:
            raise ValueError(f"La colonne '{column}' ne contient pas de valeurs de dates valides identifiables.")
        new_cols = []

        if extract_year:
            col_name = f"{column}_year"
            self.df[col_name] = dt_series.dt.year
            new_cols.append(col_name)

        if extract_month:
            col_name = f"{column}_month"
            self.df[col_name] = dt_series.dt.month
            new_cols.append(col_name)

        if extract_day:
            col_name = f"{column}_day"
            self.df[col_name] = dt_series.dt.day
            new_cols.append(col_name)

        if extract_dayofweek:
            col_name = f"{column}_dayofweek"
            self.df[col_name] = dt_series.dt.dayofweek
            new_cols.append(col_name)

        if extract_quarter:
            col_name = f"{column}_quarter"
            self.df[col_name] = dt_series.dt.quarter
            new_cols.append(col_name)

        if extract_is_weekend:
            col_name = f"{column}_is_weekend"
            self.df[col_name] = dt_series.dt.dayofweek.isin([5, 6]).astype(int)
            new_cols.append(col_name)

        if extract_hour:
            # Check if timestamps have non-zero hours
            has_hours = (dt_series.dt.hour != 0).any() or (dt_series.dt.minute != 0).any()
            if has_hours:
                col_name = f"{column}_hour"
                self.df[col_name] = dt_series.dt.hour
                new_cols.append(col_name)

        if reference_date is not None:
            ref_dt = pd.to_datetime(reference_date)
            col_name = f"{column}_days_since_ref"
            self.df[col_name] = (dt_series - ref_dt).dt.days
            new_cols.append(col_name)

        self.created_features.append({
            "type": "Temporel",
            "source_column": column,
            "created_columns": new_cols,
            "justification": f"Décomposition temporelle de {column} en variables exploitables par les modèles ML."
        })

        return self.df.copy(), new_cols

    def compute_date_difference(
        self,
        start_col: str,
        end_col: str,
        unit: str = "days",
        output_name: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Calculates duration between two datetime columns.
        unit: 'days', 'hours', 'minutes'
        """
        if start_col not in self.df.columns or end_col not in self.df.columns:
            raise KeyError("Colonnes de dates introuvables.")

        dt_start = pd.to_datetime(self.df[start_col], errors="coerce")
        dt_end = pd.to_datetime(self.df[end_col], errors="coerce")
        diff = dt_end - dt_start

        col_name = output_name or f"duration_{start_col}_{end_col}_{unit}"

        if unit == "days":
            self.df[col_name] = diff.dt.total_seconds() / 86400.0
        elif unit == "hours":
            self.df[col_name] = diff.dt.total_seconds() / 3600.0
        elif unit == "minutes":
            self.df[col_name] = diff.dt.total_seconds() / 60.0
        else:
            self.df[col_name] = diff.dt.total_seconds()

        self.created_features.append({
            "type": "Durée Temporelle",
            "source_column": f"{start_col} -> {end_col}",
            "created_columns": [col_name],
            "justification": f"Calcul du délai ({unit}) entre les événements."
        })

        return self.df.copy(), col_name

    def extract_text_features(
        self,
        column: str,
        extract_char_length: bool = True,
        extract_word_count: bool = True,
        vectorize_method: Optional[str] = None,
        max_features: int = 50
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Extracts features from a free-text column.
        vectorize_method: 'tfidf', 'bow', or None
        """
        if column not in self.df.columns:
            raise KeyError(f"Colonne introuvable : {column}")

        text_series = self.df[column].fillna("").astype(str)
        new_cols = []

        if extract_char_length:
            col_name = f"{column}_char_len"
            self.df[col_name] = text_series.str.len()
            new_cols.append(col_name)

        if extract_word_count:
            col_name = f"{column}_word_count"
            self.df[col_name] = text_series.apply(lambda s: len(s.split()))
            new_cols.append(col_name)

        if vectorize_method in ["tfidf", "bow"]:
            if vectorize_method == "tfidf":
                vec = TfidfVectorizer(max_features=max_features, stop_words="english")
            else:
                vec = CountVectorizer(max_features=max_features, stop_words="english")

            transformed = vec.fit_transform(text_series).toarray()
            feature_names = [f"{column}_vec_{name}" for name in vec.get_feature_names_out()]

            for idx, f_name in enumerate(feature_names):
                self.df[f_name] = transformed[:, idx]
                new_cols.append(f_name)

        self.created_features.append({
            "type": "Textuel",
            "source_column": column,
            "created_columns": new_cols,
            "justification": f"Extraction d'indicateurs textuels et vectorisation ({vectorize_method or 'longueur'})."
        })

        return self.df.copy(), new_cols

    def create_numeric_interaction(
        self,
        col_a: str,
        col_b: str,
        operation: str = "ratio",
        output_name: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Combines two numeric columns.
        operation: 'ratio' (A / B), 'multiply' (A * B), 'sum' (A + B), 'diff' (A - B)
        """
        if col_a not in self.df.columns or col_b not in self.df.columns:
            raise KeyError("Colonnes numériques introuvables.")

        a = pd.to_numeric(self.df[col_a], errors="coerce")
        b = pd.to_numeric(self.df[col_b], errors="coerce")

        if operation == "ratio":
            col_name = output_name or f"ratio_{col_a}_{col_b}"
            # Avoid division by zero: replace 0 with NaN or small epsilon
            self.df[col_name] = a / b.replace(0, np.nan)
        elif operation == "multiply":
            col_name = output_name or f"prod_{col_a}_{col_b}"
            self.df[col_name] = a * b
        elif operation == "sum":
            col_name = output_name or f"sum_{col_a}_{col_b}"
            self.df[col_name] = a + b
        elif operation == "diff":
            col_name = output_name or f"diff_{col_a}_{col_b}"
            self.df[col_name] = a - b
        else:
            raise ValueError(f"Opération inconnue : {operation}")

        self.created_features.append({
            "type": "Combinaison Numérique",
            "source_column": f"{col_a} {operation} {col_b}",
            "created_columns": [col_name],
            "justification": f"Création d'une variable d'interaction ({operation}) entre {col_a} et {col_b}."
        })

        return self.df.copy(), col_name

    def bin_numeric_column(
        self,
        column: str,
        n_bins: int = 5,
        strategy: str = "quantile",
        output_name: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Discretizes a continuous numeric column into intervals/bins.
        strategy: 'quantile' (equal frequency) or 'uniform' (equal width)
        """
        if column not in self.df.columns:
            raise KeyError(f"Colonne introuvable : {column}")

        series = pd.to_numeric(self.df[column], errors="coerce")
        col_name = output_name or f"{column}_bin_{strategy}"

        if strategy == "quantile":
            try:
                self.df[col_name] = pd.qcut(series, q=n_bins, duplicates="drop").astype(str)
            except Exception:
                self.df[col_name] = pd.cut(series, bins=n_bins).astype(str)
        else:
            self.df[col_name] = pd.cut(series, bins=n_bins).astype(str)

        self.created_features.append({
            "type": "Discrétisation (Binning)",
            "source_column": column,
            "created_columns": [col_name],
            "justification": f"Discrétisation de la variable continue {column} en {n_bins} intervalles ({strategy})."
        })

        return self.df.copy(), col_name

    def get_created_features_log(self) -> List[Dict[str, Any]]:
        """Returns metadata log of all newly engineered features."""
        return self.created_features
