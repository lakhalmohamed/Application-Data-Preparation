"""
Module: core/data_cleaner.py
Description: Data cleaning engine with imputation, duplicate removal, text normalization,
             outlier treatment, and complete audit tracking with undo/reset capabilities.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer


COMMON_MISSING_STRINGS = {
    "", "nan", "none", "null", "n/a", "na", "?", "-", "--", "missing", "inconnu", "unknown", "#n/a", "nil"
}


class CleaningOperation:
    """Represents a logged cleaning action."""
    def __init__(self, op_type: str, column: Optional[str], strategy: str, details: str, params: Dict[str, Any]):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.op_type = op_type
        self.column = column
        self.strategy = strategy
        self.details = details
        self.params = params

    @property
    def operation(self) -> str:
        return self.op_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "operation": self.op_type,
            "column": self.column or "[Global]",
            "strategy": self.strategy or "",
            "details": self.details or "",
            "params": self.params or {}
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


class DataCleaner:
    """Manages cleaning operations on a dataset with history tracking."""

    def __init__(self, df: pd.DataFrame):
        self._initial_df = df.copy()
        self.df = df.copy()
        self.history: List[CleaningOperation] = []
        self._snapshots: List[pd.DataFrame] = [self.df.copy()]

    def reset(self) -> pd.DataFrame:
        """Resets the dataset to its initial state."""
        self.df = self._initial_df.copy()
        self.history.clear()
        self._snapshots = [self.df.copy()]
        return self.df.copy()

    def undo(self) -> Optional[pd.DataFrame]:
        """Reverts the most recent cleaning operation."""
        if len(self._snapshots) > 1:
            self._snapshots.pop()
            self.df = self._snapshots[-1].copy()
            if self.history:
                self.history.pop()
            return self.df.copy()
        return None

    def _save_state(self, op: CleaningOperation):
        """Saves current state in history and snapshot buffer."""
        self.history.append(op)
        # Limit snapshots to last 15 to avoid memory explosion
        if len(self._snapshots) > 15:
            self._snapshots.pop(0)
        self._snapshots.append(self.df.copy())

    def remove_duplicates(self, subset: Optional[List[str]] = None, keep: str = "first") -> Tuple[pd.DataFrame, int]:
        """
        Removes duplicate rows based on all or subset of columns.
        """
        initial_len = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        removed_count = initial_len - len(self.df)

        op = CleaningOperation(
            op_type="Suppression Doublons",
            column=", ".join(subset) if subset else "[Toutes]",
            strategy=f"Conserver '{keep}'",
            details=f"{removed_count} lignes dupliquées supprimées.",
            params={"subset": subset, "keep": keep, "removed_count": removed_count}
        )
        self._save_state(op)
        return self.df.copy(), removed_count

    def drop_columns(self, columns: List[str]) -> pd.DataFrame:
        """Drops specified columns from the dataset."""
        existing_cols = [c for c in columns if c in self.df.columns]
        if not existing_cols:
            return self.df.copy()

        self.df = self.df.drop(columns=existing_cols)
        op = CleaningOperation(
            op_type="Suppression Colonnes",
            column=", ".join(existing_cols),
            strategy="drop",
            details=f"Colonnes supprimées : {', '.join(existing_cols)}",
            params={"columns": existing_cols}
        )
        self._save_state(op)
        return self.df.copy()

    def impute_missing(
        self,
        column: str,
        strategy: str = "mean",
        fill_value: Optional[Any] = None,
        knn_neighbors: int = 5
    ) -> pd.DataFrame:
        """
        Imputes missing values in a specific column.
        
        Strategies:
        - 'mean': Impute with column mean (numeric only)
        - 'median': Impute with column median (numeric only)
        - 'mode': Impute with most frequent value
        - 'constant': Impute with given fill_value
        - 'drop_rows': Drop rows where column is NaN
        - 'forward_fill': Forward fill values
        - 'backward_fill': Backward fill values
        - 'knn': KNN Imputation (numeric columns)
        """
        if column not in self.df.columns:
            raise KeyError(f"Colonne introuvable : {column}")

        series = self.df[column]
        
        # Replace common missing string representations with np.nan for object/string columns
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            mask = series.astype(str).str.strip().str.lower().isin(COMMON_MISSING_STRINGS)
            if mask.any():
                self.df.loc[mask, column] = np.nan
                series = self.df[column]

        initial_missing = int(series.isna().sum())
        if initial_missing == 0:
            op = CleaningOperation(
                op_type="Imputation",
                column=column,
                strategy=strategy,
                details="Aucune valeur manquante détectée dans cette colonne (0 cellule affectée).",
                params={"strategy": strategy, "missing_imputed": 0}
            )
            self._save_state(op)
            return self.df.copy()

        details = ""

        if strategy == "drop_rows":
            initial_len = len(self.df)
            self.df = self.df.dropna(subset=[column])
            details = f"{initial_len - len(self.df)} lignes contenant des valeurs manquantes supprimées."

        elif strategy == "mean":
            if not pd.api.types.is_numeric_dtype(series):
                raise TypeError(f"La stratégie 'mean' requiert une colonne numérique ({column}).")
            val = float(series.mean())
            self.df[column] = series.fillna(val)
            details = f"{initial_missing} valeurs imputées par la moyenne ({round(val, 3)})."

        elif strategy == "median":
            if not pd.api.types.is_numeric_dtype(series):
                raise TypeError(f"La stratégie 'median' requiert une colonne numérique ({column}).")
            val = float(series.median())
            self.df[column] = series.fillna(val)
            details = f"{initial_missing} valeurs imputées par la médiane ({round(val, 3)})."

        elif strategy == "mode":
            mode_vals = series.mode()
            if mode_vals.empty:
                val = "Inconnu" if pd.api.types.is_object_dtype(series) else 0
            else:
                val = mode_vals.iloc[0]
            self.df[column] = series.fillna(val)
            details = f"{initial_missing} valeurs imputées par le mode ('{val}')."

        elif strategy == "constant":
            val = fill_value if fill_value is not None else ("Inconnu" if pd.api.types.is_object_dtype(series) else 0)
            self.df[column] = series.fillna(val)
            details = f"{initial_missing} valeurs imputées par la constante ('{val}')."

        elif strategy == "forward_fill":
            self.df[column] = series.ffill().bfill()
            details = f"{initial_missing} valeurs imputées par propagation (forward fill)."

        elif strategy == "backward_fill":
            self.df[column] = series.bfill().ffill()
            details = f"{initial_missing} valeurs imputées par propagation inverse (backward fill)."

        elif strategy == "knn":
            num_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            if column not in num_cols:
                raise TypeError("L'imputation KNN est uniquement applicable aux colonnes numériques.")
            imputer = KNNImputer(n_neighbors=knn_neighbors)
            self.df[num_cols] = imputer.fit_transform(self.df[num_cols])
            details = f"{initial_missing} valeurs imputées via KNN (k={knn_neighbors})."

        else:
            raise ValueError(f"Stratégie d'imputation inconnue : {strategy}")

        op = CleaningOperation(
            op_type="Imputation Valeurs Manquantes",
            column=column,
            strategy=strategy,
            details=details,
            params={"strategy": strategy, "fill_value": fill_value, "imputed_count": initial_missing}
        )
        self._save_state(op)
        return self.df.copy()

    def clean_text_column(
        self,
        column: str,
        strip: bool = True,
        casing: Optional[str] = "lower",
        empty_to_nan: bool = True
    ) -> pd.DataFrame:
        """
        Cleans textual columns by stripping whitespace, adjusting casing, and standardizing empty strings.
        
        casing options: 'lower', 'upper', 'title', or None
        """
        if column not in self.df.columns:
            raise KeyError(f"Colonne introuvable : {column}")

        series = self.df[column].astype(str)

        if strip:
            series = series.str.strip()

        if casing == "lower":
            series = series.str.lower()
        elif casing == "upper":
            series = series.str.upper()
        elif casing == "title":
            series = series.str.title()

        if empty_to_nan:
            series = series.replace(
                to_replace=["", "nan", "none", "null", "n/a", "na", "?"],
                value=np.nan
            )

        self.df[column] = series

        op = CleaningOperation(
            op_type="Nettoyage Textuel",
            column=column,
            strategy=f"strip={strip}, case={casing}",
            details=f"Espaces nettoyés et casse normalisée ('{casing}').",
            params={"strip": strip, "casing": casing, "empty_to_nan": empty_to_nan}
        )
        self._save_state(op)
        return self.df.copy()

    def harmonize_rare_categories(
        self,
        column: str,
        threshold_pct: float = 1.0,
        other_label: str = "Autre"
    ) -> pd.DataFrame:
        """
        Groups infrequent categorical values representing less than threshold_pct into a common label.
        """
        if column not in self.df.columns:
            raise KeyError(f"Colonne introuvable : {column}")

        series = self.df[column]
        freq = series.value_counts(normalize=True) * 100
        rare_categories = freq[freq < threshold_pct].index.tolist()

        if not rare_categories:
            return self.df.copy()

        affected = int(series.isin(rare_categories).sum())
        self.df[column] = series.apply(lambda x: other_label if x in rare_categories else x)

        op = CleaningOperation(
            op_type="Harmonisation Modalités Rares",
            column=column,
            strategy=f"Seuil < {threshold_pct}% -> '{other_label}'",
            details=f"{len(rare_categories)} catégories rares regroupées ({affected} observations).",
            params={"threshold_pct": threshold_pct, "other_label": other_label, "rare_cats": rare_categories}
        )
        self._save_state(op)
        return self.df.copy()

    def handle_outliers(
        self,
        column: str,
        method: str = "iqr",
        action: str = "clip",
        threshold: float = 1.5
    ) -> Tuple[pd.DataFrame, int]:
        """
        Treats outliers in a numeric column.
        
        Args:
            column: Name of numeric column.
            method: 'iqr' (Interquartile Range) or 'zscore'.
            action: 'clip' (cap/winsorize at bounds), 'nan' (set as NaN), 'drop' (remove rows).
            threshold: Multiplier for IQR (default 1.5) or z-score cutoff (e.g. 3.0).
            
        Returns:
            Tuple of (DataFrame, count_of_outliers_treated)
        """
        if column not in self.df.columns:
            raise KeyError(f"Colonne introuvable : {column}")

        series = self.df[column]
        if not pd.api.types.is_numeric_dtype(series):
            raise TypeError(f"La colonne {column} doit être numérique pour le traitement des outliers.")

        non_null = series.dropna()
        if len(non_null) < 5:
            return self.df.copy(), 0

        if method == "iqr":
            q25 = float(non_null.quantile(0.25))
            q75 = float(non_null.quantile(0.75))
            iqr = q75 - q25
            lower_bound = q25 - threshold * iqr
            upper_bound = q75 + threshold * iqr
        elif method == "zscore":
            mean_val = float(non_null.mean())
            std_val = float(non_null.std())
            if std_val < 1e-8:
                return self.df.copy(), 0
            lower_bound = mean_val - threshold * std_val
            upper_bound = mean_val + threshold * std_val
        else:
            raise ValueError(f"Méthode inconnue : {method}")

        mask_outliers = (self.df[column] < lower_bound) | (self.df[column] > upper_bound)
        count_outliers = int(mask_outliers.sum())

        if count_outliers == 0:
            op = CleaningOperation(
                op_type="Traitement Outliers",
                column=column,
                strategy=f"{method.upper()} ({action})",
                details=f"Aucun outlier détecté en dehors de l'intervalle [{round(lower_bound, 2)}, {round(upper_bound, 2)}].",
                params={"method": method, "action": action, "threshold": threshold, "count": 0}
            )
            self._save_state(op)
            return self.df.copy(), 0

        details = ""
        if action == "clip":
            self.df[column] = self.df[column].clip(lower=lower_bound, upper=upper_bound)
            details = f"{count_outliers} outliers écrêtés dans l'intervalle [{round(lower_bound, 2)}, {round(upper_bound, 2)}]."
        elif action == "nan":
            self.df.loc[mask_outliers, column] = np.nan
            details = f"{count_outliers} outliers convertis en NaN pour imputation ultérieure."
        elif action == "drop":
            self.df = self.df[~mask_outliers]
            details = f"{count_outliers} lignes d'outliers supprimées."
        else:
            raise ValueError(f"Action inconnue : {action}")

        op = CleaningOperation(
            op_type="Traitement Outliers",
            column=column,
            strategy=f"{method.upper()} ({action})",
            details=details,
            params={"method": method, "action": action, "threshold": threshold, "lower": lower_bound, "upper": upper_bound, "count": count_outliers}
        )
        self._save_state(op)
        return self.df.copy(), count_outliers

    def convert_column_type(self, column: str, target_type: str) -> pd.DataFrame:
        """
        Converts column type safely.
        
        target_type: 'numeric', 'integer', 'datetime', 'string', 'boolean'
        """
        if column not in self.df.columns:
            raise KeyError(f"Colonne introuvable : {column}")

        series = self.df[column]
        if target_type == "numeric":
            if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
                cleaned = series.astype(str).str.replace(" ", "").str.replace(",", ".").str.replace("€", "").str.replace("$", "").str.replace("%", "")
                self.df[column] = pd.to_numeric(cleaned, errors="coerce")
            else:
                self.df[column] = pd.to_numeric(series, errors="coerce")
        elif target_type == "integer":
            num = pd.to_numeric(self.df[column], errors="coerce")
            self.df[column] = num.round().astype("Int64")  # Nullable integer
        elif target_type == "datetime":
            self.df[column] = pd.to_datetime(self.df[column], errors="coerce")
        elif target_type == "string":
            self.df[column] = self.df[column].astype(str)
        elif target_type == "boolean":
            # Map standard yes/no/1/0
            mapping = {"1": True, "0": False, "true": True, "false": False, "oui": True, "non": False, "yes": True, "no": False}
            cleaned = self.df[column].astype(str).str.lower().str.strip()
            self.df[column] = cleaned.map(mapping)
        else:
            raise ValueError(f"Type cible inconnu : {target_type}")

        op = CleaningOperation(
            op_type="Conversion de Type",
            column=column,
            strategy=target_type,
            details=f"Type converti vers '{target_type}'.",
            params={"target_type": target_type}
        )
        self._save_state(op)
        return self.df.copy()

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the list of all applied operations."""
        return [op.to_dict() for op in self.history]
