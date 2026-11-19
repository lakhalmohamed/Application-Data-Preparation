"""
Module: core/ml_preprocessor.py
Description: Machine Learning preparation engine constructing Scikit-learn Pipelines
             and ColumnTransformers with zero train-to-test data leakage, task inference,
             class imbalance auditing, and model recommendation.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
    OneHotEncoder,
    OrdinalEncoder,
    LabelEncoder
)


class MLTaskType:
    BINARY_CLASSIFICATION = "Classification Binaire"
    MULTICLASS_CLASSIFICATION = "Classification Multiclasse"
    REGRESSION = "Régression"
    UNSUPERVISED = "Apprentissage Non Supervisé"


MODEL_RECOMMENDATIONS = {
    MLTaskType.BINARY_CLASSIFICATION: [
        {"name": "Régression Logistique", "type": "Linéaire", "scaling_needed": True, "notes": "Interprétable, rapide, nécessite mise à l'échelle (Standard/Robust)."},
        {"name": "Random Forest", "type": "Ensemble (Arbres)", "scaling_needed": False, "notes": "Robuste aux outliers, capture les non-linéarités, pas besoin de scaling."},
        {"name": "SVM (Support Vector Machine)", "type": "Géométrique", "scaling_needed": True, "notes": "Efficace en haute dimension, très sensible à la mise à l'échelle."},
        {"name": "KNN (K-Nearest Neighbors)", "type": "Basé sur les distances", "scaling_needed": True, "notes": "Sensible aux échelles et à la dimensionnalité."},
        {"name": "Arbre de Décision", "type": "Arbre", "scaling_needed": False, "notes": "Très lisible, sensible au surapprentissage, pas besoin de scaling."}
    ],
    MLTaskType.MULTICLASS_CLASSIFICATION: [
        {"name": "Random Forest", "type": "Ensemble (Arbres)", "scaling_needed": False, "notes": "Excellente généralisation multiclasse sans scaling obligatoire."},
        {"name": "Régression Logistique (Multinomiale)", "type": "Linéaire", "scaling_needed": True, "notes": "Solide référence linéaire, normalisation requise."},
        {"name": "Naive Bayes", "type": "Probabiliste", "scaling_needed": False, "notes": "Très rapide, performant sur données textuelles ou catégorielles."},
        {"name": "Arbre de Décision", "type": "Arbre", "scaling_needed": False, "notes": "Facilement interprétable."}
    ],
    MLTaskType.REGRESSION: [
        {"name": "Régression Linéaire / Ridge", "type": "Linéaire", "scaling_needed": True, "notes": "Indispensable d'harmoniser les échelles pour régularisation Ridge/Lasso."},
        {"name": "Random Forest Regressor", "type": "Ensemble (Arbres)", "scaling_needed": False, "notes": "Gère naturellement les non-linéarités et interactions."},
        {"name": "Gradient Boosting (GBR)", "type": "Ensemble (Boosting)", "scaling_needed": False, "notes": "Hautes performances prédictives."},
        {"name": "SVR (Support Vector Regression)", "type": "Géométrique", "scaling_needed": True, "notes": "Nécessite impérativement des variables standardisées."}
    ],
    MLTaskType.UNSUPERVISED: [
        {"name": "K-Means", "type": "Clustering", "scaling_needed": True, "notes": "Calcule des distances euclidiennes : Standardisation impérative."},
        {"name": "PCA (Analyse en Composantes Principales)", "type": "Réduction de dimension", "scaling_needed": True, "notes": "Standardisation nécessaire pour éviter la domination des fortes variances."},
        {"name": "DBSCAN", "type": "Clustering basé sur la densité", "scaling_needed": True, "notes": "Sensible au choix d'epsilon et aux différentes échelles des variables."}
    ]
}


class MLPreprocessor:
    """Prepares datasets for ML ensuring zero train-to-test leakage."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    @staticmethod
    def infer_task_type(target_series: pd.Series) -> Tuple[str, Dict[str, Any]]:
        """
        Infers whether the task is binary classification, multiclass, or regression.
        """
        non_null = target_series.dropna()
        n_unique = non_null.nunique()

        if n_unique == 2:
            task = MLTaskType.BINARY_CLASSIFICATION
        elif pd.api.types.is_numeric_dtype(non_null):
            if n_unique > 20 or (pd.api.types.is_float_dtype(non_null) and n_unique > 10):
                task = MLTaskType.REGRESSION
            else:
                task = MLTaskType.MULTICLASS_CLASSIFICATION
        else:
            task = MLTaskType.MULTICLASS_CLASSIFICATION

        # Imbalance analysis for classification
        imbalance_info = {}
        if task in [MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION]:
            counts = non_null.value_counts()
            pcts = non_null.value_counts(normalize=True) * 100
            min_pct = pcts.min()
            max_pct = pcts.max()
            ratio = round(max_pct / min_pct, 2) if min_pct > 0 else 0
            is_imbalanced = ratio >= 3.0

            imbalance_info = {
                "class_counts": counts.to_dict(),
                "class_percentages": pcts.round(2).to_dict(),
                "imbalance_ratio": ratio,
                "is_imbalanced": is_imbalanced,
                "warning": f"Déséquilibre notable des classes (ratio 1:{ratio})." if is_imbalanced else "Classes équilibrées."
            }

        return task, imbalance_info

    def check_data_leakage(self, target_col: str, feature_cols: List[str]) -> List[Dict[str, Any]]:
        """
        Scans feature columns for potential data leakage indicators:
        - Perfect or near-perfect correlation (> 0.98) with target
        - Column name containing target name or ID
        """
        leakage_warnings = []
        target = self.df[target_col]

        for col in feature_cols:
            # Name leak check
            if target_col.lower() in col.lower() and col.lower() != target_col.lower():
                leakage_warnings.append({
                    "column": col,
                    "type": "Fuite par intitulé",
                    "reason": f"Le nom '{col}' contient l'intitulé de la cible '{target_col}'."
                })

            # High correlation check
            if pd.api.types.is_numeric_dtype(target) and pd.api.types.is_numeric_dtype(self.df[col]):
                try:
                    corr = abs(self.df[[col, target_col]].dropna().corr().iloc[0, 1])
                    if corr >= 0.98:
                        leakage_warnings.append({
                            "column": col,
                            "type": "Corrélation quasi-parfaite",
                            "reason": f"Corrélation de {round(corr, 4)} avec la variable cible (probable variable dérivée ou identique)."
                        })
                except Exception:
                    pass

        return leakage_warnings

    def build_supervised_pipeline(
        self,
        target_col: str,
        feature_cols: Optional[List[str]] = None,
        test_size: float = 0.2,
        split_strategy: str = "stratified",
        temporal_col: Optional[str] = None,
        numeric_scaler: str = "standard",
        categorical_encoder: str = "onehot",
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Builds and fits Scikit-learn Pipeline on training split with zero data leakage.
        
        Args:
            target_col: Name of target variable y.
            feature_cols: List of features X (auto-selected if None).
            test_size: Test split proportion (e.g. 0.2).
            split_strategy: 'stratified', 'random', or 'chronological'.
            temporal_col: Column name used if split_strategy is 'chronological'.
            numeric_scaler: 'standard', 'minmax', 'robust', or 'none'.
            categorical_encoder: 'onehot', 'ordinal', or 'none'.
            random_state: Random seed for reproducibility.
            
        Returns:
            Dictionary with prepared splits (X_train_df, X_test_df, y_train, y_test),
            pipeline, task_type, feature_names, leakage_warnings, etc.
        """
        if target_col not in self.df.columns:
            raise KeyError(f"Variable cible introuvable : {target_col}")

        # Drop rows where target is NaN
        clean_df = self.df.dropna(subset=[target_col]).copy()
        dropped_target_na = len(self.df) - len(clean_df)

        # Infer task
        task_type, imbalance_info = self.infer_task_type(clean_df[target_col])

        # Determine feature columns
        if feature_cols is None:
            feature_cols = [c for c in clean_df.columns if c != target_col]
        else:
            feature_cols = [c for c in feature_cols if c in clean_df.columns and c != target_col]

        leakage_warnings = self.check_data_leakage(target_col, feature_cols)

        X = clean_df[feature_cols].copy()
        y = clean_df[target_col].copy()

        # Handle target label encoding for classification if non-numeric
        label_encoder = None
        if task_type in [MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION]:
            if not pd.api.types.is_numeric_dtype(y) or pd.api.types.is_object_dtype(y):
                label_encoder = LabelEncoder()
                y_encoded = label_encoder.fit_transform(y.astype(str))
                y = pd.Series(y_encoded, index=clean_df.index, name=target_col)

        # Split Data with Zero Leakage
        if split_strategy == "chronological" and temporal_col and temporal_col in clean_df.columns:
            # Sort by temporal column and split sequentially
            sorted_indices = clean_df[temporal_col].sort_values().index
            split_idx = int(len(sorted_indices) * (1.0 - test_size))
            train_idx = sorted_indices[:split_idx]
            test_idx = sorted_indices[split_idx:]
            X_train, X_test = X.loc[train_idx], X.loc[test_idx]
            y_train, y_test = y.loc[train_idx], y.loc[test_idx]
        elif split_strategy == "stratified" and task_type in [MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION]:
            # Stratified split ensures equal class representation in train and test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )

        # Separate numeric and categorical features
        numeric_features = X_train.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = [c for c in X_train.columns if c not in numeric_features]

        # Build Numeric Pipeline
        num_transformers = [("imputer", SimpleImputer(strategy="median"))]
        if numeric_scaler == "standard":
            num_transformers.append(("scaler", StandardScaler()))
        elif numeric_scaler == "minmax":
            num_transformers.append(("scaler", MinMaxScaler()))
        elif numeric_scaler == "robust":
            num_transformers.append(("scaler", RobustScaler()))
        num_pipeline = Pipeline(steps=num_transformers)

        # Build Categorical Pipeline
        cat_transformers = [("imputer", SimpleImputer(strategy="most_frequent"))]
        if categorical_encoder == "onehot":
            try:
                encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            except TypeError:
                encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
            cat_transformers.append(("encoder", encoder))
        elif categorical_encoder == "ordinal":
            encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
            cat_transformers.append(("encoder", encoder))
        cat_pipeline = Pipeline(steps=cat_transformers)

        # Combine into ColumnTransformer
        transformers = []
        if numeric_features:
            transformers.append(("num", num_pipeline, numeric_features))
        if categorical_features:
            transformers.append(("cat", cat_pipeline, categorical_features))

        if not transformers:
            raise ValueError("Aucune variable exploitable sélectionnée pour la préparation.")

        preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")

        # FIT STRICTLY ON TRAIN SPLIT ONLY (ZERO DATA LEAKAGE)
        X_train_prep_arr = preprocessor.fit_transform(X_train)
        X_test_prep_arr = preprocessor.transform(X_test)

        # Extract generated feature names
        try:
            out_features = preprocessor.get_feature_names_out()
            # Clean prefixes like 'num__' and 'cat__'
            clean_names = [name.replace("num__", "").replace("cat__", "") for name in out_features]
        except Exception:
            clean_names = [f"feat_{i}" for i in range(X_train_prep_arr.shape[1])]

        X_train_prep_df = pd.DataFrame(X_train_prep_arr, columns=clean_names, index=X_train.index)
        X_test_prep_df = pd.DataFrame(X_test_prep_arr, columns=clean_names, index=X_test.index)

        recommended_models = MODEL_RECOMMENDATIONS.get(task_type, [])

        return {
            "mode": "supervised",
            "task_type": task_type,
            "target_col": target_col,
            "dropped_target_na": dropped_target_na,
            "imbalance_info": imbalance_info,
            "leakage_warnings": leakage_warnings,
            "split_strategy": split_strategy,
            "test_size": test_size,
            "random_state": random_state,
            "numeric_scaler": numeric_scaler,
            "categorical_encoder": categorical_encoder,
            "pipeline": preprocessor,
            "label_encoder": label_encoder,
            "feature_names_in": feature_cols,
            "feature_names_out": clean_names,
            "X_train": X_train_prep_df,
            "X_test": X_test_prep_df,
            "y_train": y_train,
            "y_test": y_test,
            "recommended_models": recommended_models
        }

    def build_unsupervised_pipeline(
        self,
        feature_cols: Optional[List[str]] = None,
        numeric_scaler: str = "standard",
        categorical_encoder: str = "onehot"
    ) -> Dict[str, Any]:
        """
        Builds and fits an unsupervised preparation pipeline (e.g. for K-Means or PCA).
        """
        if feature_cols is None:
            # Auto-select non-constant columns
            feature_cols = [c for c in self.df.columns if self.df[c].nunique() > 1]

        X = self.df[feature_cols].copy()
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = [c for c in X.columns if c not in numeric_features]

        num_transformers = [("imputer", SimpleImputer(strategy="median"))]
        if numeric_scaler == "standard":
            num_transformers.append(("scaler", StandardScaler()))
        elif numeric_scaler == "minmax":
            num_transformers.append(("scaler", MinMaxScaler()))
        elif numeric_scaler == "robust":
            num_transformers.append(("scaler", RobustScaler()))
        num_pipeline = Pipeline(steps=num_transformers)

        cat_transformers = [("imputer", SimpleImputer(strategy="most_frequent"))]
        if categorical_encoder == "onehot":
            try:
                encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            except TypeError:
                encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
            cat_transformers.append(("encoder", encoder))
        elif categorical_encoder == "ordinal":
            encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
            cat_transformers.append(("encoder", encoder))
        cat_pipeline = Pipeline(steps=cat_transformers)

        transformers = []
        if numeric_features:
            transformers.append(("num", num_pipeline, numeric_features))
        if categorical_features:
            transformers.append(("cat", cat_pipeline, categorical_features))

        preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
        X_prep_arr = preprocessor.fit_transform(X)

        try:
            out_features = preprocessor.get_feature_names_out()
            clean_names = [name.replace("num__", "").replace("cat__", "") for name in out_features]
        except Exception:
            clean_names = [f"feat_{i}" for i in range(X_prep_arr.shape[1])]

        X_prep_df = pd.DataFrame(X_prep_arr, columns=clean_names, index=X.index)
        recommended_models = MODEL_RECOMMENDATIONS.get(MLTaskType.UNSUPERVISED, [])

        return {
            "mode": "unsupervised",
            "task_type": MLTaskType.UNSUPERVISED,
            "numeric_scaler": numeric_scaler,
            "categorical_encoder": categorical_encoder,
            "pipeline": preprocessor,
            "feature_names_in": feature_cols,
            "feature_names_out": clean_names,
            "X_prepared": X_prep_df,
            "recommended_models": recommended_models
        }
