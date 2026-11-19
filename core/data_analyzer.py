"""
Module: core/data_analyzer.py
Description: Advanced semantic column analysis, type classification, PII detection,
             statistical profiling, and automated data quality auditing.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd


class VariableType:
    NUMERIC_CONTINUOUS = "Numérique continu"
    NUMERIC_DISCRETE = "Numérique discret"
    CATEGORICAL_NOMINAL = "Catégoriel nominal"
    CATEGORICAL_ORDINAL = "Catégoriel ordinal"
    BOOLEAN = "Booléen"
    TEXT = "Texte libre"
    DATETIME = "Temporel (Date/Heure)"
    IDENTIFIER = "Identifiant technique"
    CONSTANT = "Constant ou quasi-constant"
    PII = "Donnée sensible / PII"


COMMON_MISSING_STRINGS = {
    "", "nan", "none", "null", "n/a", "na", "?", "-", "--", "missing", "inconnu", "unknown", "#n/a", "nil"
}

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
PHONE_REGEX = re.compile(r"^(?:\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$")
IP_REGEX = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
SSN_REGEX = re.compile(r"^[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}(?:\s?\d{2})?$")

ID_NAME_PATTERNS = ["id", "uuid", "guid", "code", "ref", "reference", "key", "num", "no", "matricule", "client_id", "customer_id", "user_id"]
DATE_NAME_PATTERNS = ["date", "time", "timestamp", "annee", "year", "mois", "month", "jour", "day", "created_at", "updated_at", "birth", "naissance", "dt", "datetime", "heure", "start", "end", "debut", "fin", "periode", "period"]
ORDINAL_PATTERNS = [
    {"low", "medium", "high"},
    {"faible", "moyen", "fort"},
    {"faible", "moyen", "eleve", "élevé"},
    {"bad", "neutral", "good"},
    {"mauvais", "neutre", "bon"},
    {"xs", "s", "m", "l", "xl", "xxl"},
    {"junior", "mid", "senior"},
    {"debutant", "intermediaire", "avance", "expert", "débutant", "intermédiaire", "avancé"},
    {"tier 1", "tier 2", "tier 3"},
    {"niveau 1", "niveau 2", "niveau 3", "niveau 4"}
]


class DataAnalyzer:
    """Intelligent semantic analyzer for tabular datasets."""

    def __init__(self):
        pass

    @staticmethod
    def is_datetime_series(series: pd.Series, sample_size: int = 50) -> Tuple[bool, float]:
        """Check if series represents datetime values."""
        if pd.api.types.is_datetime64_any_dtype(series):
            return True, 1.0

        non_null = series.dropna()
        if len(non_null) == 0:
            return False, 0.0

        sample = non_null.astype(str).str.strip().head(sample_size)
        success_count = 0
        for val in sample:
            if not val or val.lower() in COMMON_MISSING_STRINGS or len(val) < 4:
                continue
            # Try parsing with pd.to_datetime
            try:
                pd.to_datetime(val, errors="raise")
                success_count += 1
            except Exception:
                pass

        ratio = success_count / len(sample) if len(sample) > 0 else 0.0
        return (ratio >= 0.8), ratio

    @staticmethod
    def detect_pii(series: pd.Series, col_name: str, sample_size: int = 100) -> Tuple[bool, Optional[str], float]:
        """Detect personal identifiable information (PII)."""
        name_lower = col_name.lower()
        if any(w in name_lower for w in ["email", "courriel", "mail"]):
            return True, "Email (Nom colonne)", 0.95
        if any(w in name_lower for w in ["phone", "tel", "telephone", "mobile", "portable"]):
            return True, "Téléphone (Nom colonne)", 0.90
        if any(w in name_lower for w in ["ssn", "secu", "securite_sociale", "nir"]):
            return True, "Numéro Sécurité Sociale (Nom colonne)", 0.95

        non_null = series.dropna().astype(str).str.strip()
        sample = non_null.head(sample_size)
        if len(sample) == 0:
            return False, None, 0.0

        email_matches = sum(bool(EMAIL_REGEX.match(v)) for v in sample)
        if email_matches / len(sample) >= 0.5:
            return True, "Adresse Email", 0.95

        def is_phone_val(v: str) -> bool:
            if re.match(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$", v):
                return False
            digits = sum(c.isdigit() for c in v)
            return bool(PHONE_REGEX.match(v)) and 9 <= digits <= 15

        phone_matches = sum(is_phone_val(v) for v in sample)
        if phone_matches / len(sample) >= 0.6:
            return True, "Numéro de Téléphone", 0.85

        ip_matches = sum(bool(IP_REGEX.match(v)) for v in sample)
        if ip_matches / len(sample) >= 0.6:
            return True, "Adresse IP", 0.90

        ssn_matches = sum(bool(SSN_REGEX.match(v)) for v in sample)
        if ssn_matches / len(sample) >= 0.5:
            return True, "Numéro de Sécurité Sociale / NIR", 0.95

        return False, None, 0.0

    @staticmethod
    def detect_number_stored_as_text(series: pd.Series, sample_size: int = 100) -> Tuple[bool, float]:
        """Detect if object/string column is actually numeric."""
        if pd.api.types.is_numeric_dtype(series):
            return False, 0.0

        non_null = series.dropna().astype(str).str.strip()
        sample = non_null.head(sample_size)
        if len(sample) == 0:
            return False, 0.0

        convertible = 0
        for val in sample:
            clean = val.replace(" ", "").replace(",", ".").replace("€", "").replace("$", "").replace("%", "")
            try:
                float(clean)
                convertible += 1
            except ValueError:
                pass

        ratio = convertible / len(sample)
        return (ratio >= 0.85), ratio

    def infer_variable_type(self, series: pd.Series, col_name: str) -> Tuple[str, str, float, Dict[str, Any]]:
        """
        Determines the semantic nature of a column.
        
        Returns:
            (detected_type, confidence_label, confidence_score, extra_metadata)
        """
        n_total = len(series)
        non_null = series.dropna()
        n_non_null = len(non_null)
        name_lower = col_name.lower().strip()

        if n_non_null == 0:
            return VariableType.CONSTANT, "Élevée", 1.0, {"reason": "Colonne entièrement vide"}

        n_unique = non_null.nunique()
        unique_ratio = n_unique / n_non_null if n_non_null > 0 else 0.0

        # 1. Constant or Quasi-constant
        if n_unique <= 1:
            return VariableType.CONSTANT, "Élevée", 1.0, {"reason": "Valeur unique constante"}
        top_freq_ratio = non_null.value_counts(normalize=True).iloc[0]
        if top_freq_ratio >= 0.99 and n_non_null > 50:
            return VariableType.CONSTANT, "Élevée", 0.95, {"reason": f"Quasi-constant ({round(top_freq_ratio*100, 1)}% même valeur)"}

        # 2. PII Check
        is_pii, pii_type, pii_conf = self.detect_pii(non_null, col_name)
        if is_pii:
            return VariableType.PII, ("Élevée" if pii_conf > 0.85 else "Moyenne"), pii_conf, {"pii_type": pii_type}

        # 3. Datetime
        is_dt, dt_ratio = self.is_datetime_series(series)
        has_dt_name = any(k in name_lower for k in DATE_NAME_PATTERNS)
        if is_dt or (has_dt_name and dt_ratio > 0.5):
            conf_score = 0.95 if is_dt else 0.75
            conf_label = "Élevée" if conf_score >= 0.9 else "Moyenne"
            return VariableType.DATETIME, conf_label, conf_score, {"reason": "Format temporel détecté"}

        # 4. Boolean
        # Values like {0, 1}, {True, False}, {'yes', 'no'}, {'oui', 'non'}, etc.
        unique_vals = set(non_null.unique())
        if pd.api.types.is_bool_dtype(series) or unique_vals.issubset({True, False, 0, 1, 0.0, 1.0}):
            return VariableType.BOOLEAN, "Élevée", 0.98, {"reason": "Valeurs binaires {0, 1 / Vrai, Faux}"}
        if n_unique == 2:
            str_vals = {str(v).lower().strip() for v in unique_vals}
            bool_pairs = [{'yes', 'no'}, {'oui', 'non'}, {'y', 'n'}, {'o', 'n'}, {'true', 'false'}, {'vrai', 'faux'}, {'t', 'f'}, {'pos', 'neg'}, {'1', '0'}]
            if any(str_vals.issubset(pair) for pair in bool_pairs):
                return VariableType.BOOLEAN, "Élevée", 0.95, {"reason": "Deux valeurs booléennes distinctes"}

        # 5. Technical Identifier
        has_id_name = any(name_lower == pattern or name_lower.startswith(f"{pattern}_") or name_lower.endswith(f"_{pattern}") for pattern in ID_NAME_PATTERNS)
        if unique_ratio >= 0.99 and n_non_null >= 20:
            if has_id_name:
                return VariableType.IDENTIFIER, "Élevée", 0.98, {"reason": "Nom d'identifiant et 100% de valeurs distinctes"}
            # Check sequential integer or UUID pattern
            if pd.api.types.is_integer_dtype(series):
                diffs = non_null.sort_values().diff().dropna()
                if (diffs == 1).mean() > 0.9:
                    return VariableType.IDENTIFIER, "Élevée", 0.95, {"reason": "Index séquentiel incrémental"}
            elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
                sample_str = str(non_null.iloc[0])
                if len(sample_str) >= 8 and any(c.isdigit() for c in sample_str) and any(c.isalpha() for c in sample_str):
                    return VariableType.IDENTIFIER, "Moyenne", 0.85, {"reason": "Chaîne alphanumérique unique de type clé/UUID"}

        # 6. Ordinal Patterns Check
        if n_unique <= 10:
            val_strs = {str(v).lower().strip() for v in unique_vals}
            for ord_set in ORDINAL_PATTERNS:
                if val_strs.issubset(ord_set) or len(val_strs.intersection(ord_set)) >= 3:
                    return VariableType.CATEGORICAL_ORDINAL, "Élevée", 0.90, {"reason": "Hiérarchie ordinale sémantique détectée"}

        # 7. Check if numbers stored as string
        is_num_str, num_ratio = self.detect_number_stored_as_text(series)
        if is_num_str:
            return VariableType.NUMERIC_CONTINUOUS, "Moyenne", 0.80, {"reason": "Nombres stockés sous forme textuelle"}

        # 8. Numeric Continuous vs Discrete
        if pd.api.types.is_numeric_dtype(series):
            # Check if integer ratings like 1, 2, 3, 4, 5
            if pd.api.types.is_integer_dtype(series) and n_unique <= 7 and non_null.min() in [0, 1] and non_null.max() <= 10:
                return VariableType.CATEGORICAL_ORDINAL, "Moyenne", 0.70, {"reason": "Petite échelle d'entiers discrets (type notation/rating)"}

            if pd.api.types.is_float_dtype(series):
                # If all floats are actually integer representations (e.g. 1.0, 2.0)
                is_all_int = (non_null % 1 == 0).all()
                if is_all_int and n_unique <= 10:
                    return VariableType.NUMERIC_DISCRETE, "Moyenne", 0.75, {"reason": "Entiers stockés en float avec faible cardinalité"}
                return VariableType.NUMERIC_CONTINUOUS, "Élevée", 0.95, {"reason": "Variable numérique à virgule flottante continue"}

            # Integer
            if n_unique <= 15 or unique_ratio < 0.05:
                return VariableType.NUMERIC_DISCRETE, "Élevée", 0.90, {"reason": f"Entier discret à cardinalité limitée ({n_unique} valeurs)"}
            else:
                return VariableType.NUMERIC_CONTINUOUS, "Moyenne", 0.85, {"reason": "Entier à forte variabilité traité comme continu"}

        # 9. Free Text vs Nominal Category
        if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            str_series = non_null.astype(str).str.strip()
            avg_len = str_series.str.len().mean()
            avg_words = str_series.str.split().str.len().mean()

            if avg_words >= 4 or avg_len >= 40:
                return VariableType.TEXT, "Élevée", 0.92, {"reason": f"Texte long (moyenne {round(avg_words, 1)} mots, {round(avg_len, 1)} caractères)"}

            # Moderate text / descriptions
            if unique_ratio >= 0.7 and n_non_null > 20 and avg_words > 2:
                return VariableType.TEXT, "Moyenne", 0.75, {"reason": "Texte varié à cardinalité élevée"}

            return VariableType.CATEGORICAL_NOMINAL, "Élevée", 0.90, {"reason": f"Catégorie nominale discrète ({n_unique} modalités)"}

        return VariableType.CATEGORICAL_NOMINAL, "Faible", 0.50, {"reason": "Type par défaut non déterminé"}

    def profile_column(self, series: pd.Series, col_name: str) -> Dict[str, Any]:
        """Calculates full statistical profile, detects issues, and formulates recommendations."""
        n_total = len(series)
        missing_count = int(series.isna().sum())
        
        # Also check for empty strings or string-missing in object columns
        missing_strings_count = 0
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            clean_str = series.dropna().astype(str).str.strip().str.lower()
            missing_strings_count = int(clean_str.isin(COMMON_MISSING_STRINGS).sum())

        effective_missing = missing_count + missing_strings_count
        missing_pct = round((effective_missing / n_total) * 100, 2) if n_total > 0 else 0.0

        non_null = series.dropna()
        n_non_null = len(non_null)
        n_unique = int(non_null.nunique())
        unique_pct = round((n_unique / n_non_null) * 100, 2) if n_non_null > 0 else 0.0

        vtype, conf_label, conf_score, meta = self.infer_variable_type(series, col_name)

        stats = {
            "total_count": n_total,
            "non_null_count": len(non_null),
            "missing_count": effective_missing,
            "missing_pct": missing_pct,
            "unique_count": n_unique,
            "unique_pct": unique_pct,
        }

        issues: List[Dict[str, Any]] = []
        recommendations: List[Dict[str, Any]] = []

        # 1. Missing Values Issue & Recommendation
        if effective_missing > 0:
            severity = "Critique" if missing_pct > 60 else ("Élevée" if missing_pct > 25 else ("Moyenne" if missing_pct > 5 else "Faible"))
            issues.append({
                "issue": "Valeurs manquantes",
                "severity": severity,
                "count": effective_missing,
                "pct": missing_pct,
                "details": f"{effective_missing} cellules manquantes ({missing_pct}%)"
            })

            # Recommendation based on type and rate
            if missing_pct > 70:
                recommendations.append({
                    "action": "Suppression de la colonne",
                    "strategy": "drop_column",
                    "justification": f"Taux d'absence excessif ({missing_pct}%) rendant l'imputation risquée.",
                    "priority": "Haute"
                })
            elif vtype in [VariableType.NUMERIC_CONTINUOUS, VariableType.NUMERIC_DISCRETE]:
                stats_skew = float(non_null.skew()) if len(non_null) > 2 and pd.api.types.is_numeric_dtype(non_null) else 0.0
                if abs(stats_skew) > 1.0:
                    recommendations.append({
                        "action": "Imputation par la médiane",
                        "strategy": "median",
                        "justification": f"Distribution asymétrique (skewness={round(stats_skew, 2)}) : la médiane est plus robuste que la moyenne.",
                        "priority": "Haute"
                    })
                else:
                    recommendations.append({
                        "action": "Imputation par la moyenne",
                        "strategy": "mean",
                        "justification": "Distribution approximativement symétrique.",
                        "priority": "Haute"
                    })
            elif vtype in [VariableType.CATEGORICAL_NOMINAL, VariableType.CATEGORICAL_ORDINAL, VariableType.BOOLEAN]:
                if missing_pct > 15:
                    recommendations.append({
                        "action": "Imputation par catégorie 'Inconnu'",
                        "strategy": "constant",
                        "fill_value": "Inconnu",
                        "justification": f"Taux d'absence substantiel ({missing_pct}%) : l'absence peut constituer une information.",
                        "priority": "Haute"
                    })
                else:
                    recommendations.append({
                        "action": "Imputation par le mode (valeur la plus fréquente)",
                        "strategy": "mode",
                        "justification": "Taux d'absence faible sur variable catégorielle.",
                        "priority": "Haute"
                    })
            elif vtype == VariableType.TEXT:
                recommendations.append({
                    "action": "Remplacement par chaîne vide",
                    "strategy": "constant",
                    "fill_value": "",
                    "justification": "Préserve la structure du texte pour vectorisation sans lever d'erreur.",
                    "priority": "Moyenne"
                })

        # 2. Outliers (Numeric columns)
        if vtype in [VariableType.NUMERIC_CONTINUOUS, VariableType.NUMERIC_DISCRETE] and pd.api.types.is_numeric_dtype(non_null) and len(non_null) >= 10:
            q25 = float(non_null.quantile(0.25))
            q75 = float(non_null.quantile(0.75))
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr

            outliers_iqr = non_null[(non_null < lower_bound) | (non_null > upper_bound)]
            iqr_count = len(outliers_iqr)

            std_val = float(non_null.std())
            mean_val = float(non_null.mean())
            z_count = 0
            if std_val > 1e-8:
                z_scores = np.abs((non_null - mean_val) / std_val)
                z_count = int((z_scores > 3.0).sum())

            stats.update({
                "mean": round(mean_val, 4),
                "std": round(std_val, 4),
                "min": round(float(non_null.min()), 4),
                "q25": round(q25, 4),
                "median": round(float(non_null.median()), 4),
                "q75": round(q75, 4),
                "max": round(float(non_null.max()), 4),
                "iqr": round(iqr, 4),
                "iqr_lower": round(lower_bound, 4),
                "iqr_upper": round(upper_bound, 4),
                "outliers_iqr_count": iqr_count,
                "outliers_iqr_pct": round(iqr_count / len(non_null) * 100, 2),
                "outliers_zscore_count": z_count
            })

            if iqr_count > 0:
                severity = "Élevée" if (iqr_count / len(non_null)) > 0.05 else "Moyenne"
                issues.append({
                    "issue": "Valeurs aberrantes (Outliers IQR)",
                    "severity": severity,
                    "count": iqr_count,
                    "pct": round(iqr_count / len(non_null) * 100, 2),
                    "details": f"{iqr_count} valeurs hors intervalle [{round(lower_bound, 2)}, {round(upper_bound, 2)}]"
                })
                recommendations.append({
                    "action": "Winsorisation / Écrêtage (Clipping IQR)",
                    "strategy": "clip_iqr",
                    "justification": "Borne les valeurs extrêmes sans supprimer les observations afin d'éviter la perte d'information.",
                    "priority": "Moyenne"
                })

        # 3. Categorical / Textual Inconsistencies
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            str_series = non_null.astype(str)
            has_whitespace = (str_series != str_series.str.strip()).any()
            whitespace_count = int((str_series != str_series.str.strip()).sum())
            if has_whitespace:
                issues.append({
                    "issue": "Espaces superflus (début/fin)",
                    "severity": "Faible",
                    "count": whitespace_count,
                    "pct": round(whitespace_count / len(non_null) * 100, 2),
                    "details": f"{whitespace_count} entrées contiennent des espaces inutiles."
                })
                recommendations.append({
                    "action": "Suppression des espaces (strip)",
                    "strategy": "strip_whitespace",
                    "justification": "Évite la création de catégories dupliquées dues aux espaces.",
                    "priority": "Moyenne"
                })

            # Check casing differences
            raw_unique = set(str_series.unique())
            lower_unique = set(str_series.str.lower().str.strip().unique())
            if len(raw_unique) > len(lower_unique):
                casing_diff = len(raw_unique) - len(lower_unique)
                issues.append({
                    "issue": "Incohérence de casse (majuscules/minuscules)",
                    "severity": "Moyenne",
                    "count": casing_diff,
                    "pct": round(casing_diff / len(raw_unique) * 100, 2),
                    "details": f"{casing_diff} variations de casse pour des modalités identiques (ex: MAD / mad)."
                })
                recommendations.append({
                    "action": "Harmonisation de la casse",
                    "strategy": "normalize_case",
                    "justification": "Regroupe les catégories identiques écrites avec des casses différentes.",
                    "priority": "Moyenne"
                })

            # Rare categories for nominal
            if vtype == VariableType.CATEGORICAL_NOMINAL and n_unique > 5:
                freqs = str_series.value_counts(normalize=True)
                rare_cats = freqs[freqs < 0.01].index.tolist()
                if rare_cats:
                    issues.append({
                        "issue": "Modalités rares (<1% fréquence)",
                        "severity": "Faible",
                        "count": len(rare_cats),
                        "pct": round(len(rare_cats) / n_unique * 100, 2),
                        "details": f"{len(rare_cats)} modalités représentent chacune moins de 1% des données."
                    })
                    recommendations.append({
                        "action": "Regroupement des catégories rares",
                        "strategy": "group_rare",
                        "justification": "Évite l'explosion du nombre de colonnes lors du One-Hot Encoding.",
                        "priority": "Basse"
                    })

        # 4. Constant / Quasi-constant
        if vtype == VariableType.CONSTANT:
            issues.append({
                "issue": "Colonne constante ou quasi-invariable",
                "severity": "Critique",
                "count": n_total,
                "pct": 100.0,
                "details": meta.get("reason", "Variance nulle")
            })
            recommendations.append({
                "action": "Suppression de la colonne",
                "strategy": "drop_column",
                "justification": "N'apporte aucun pouvoir prédictif aux modèles de Machine Learning.",
                "priority": "Haute"
            })

        # 5. Technical Identifier
        if vtype == VariableType.IDENTIFIER:
            issues.append({
                "issue": "Identifiant technique",
                "severity": "Moyenne",
                "count": n_unique,
                "pct": unique_pct,
                "details": meta.get("reason", "Identifiant unique")
            })
            recommendations.append({
                "action": "Exclure des variables prédictives",
                "strategy": "drop_column",
                "justification": "Les identifiants causent du surapprentissage sans généralisation.",
                "priority": "Haute"
            })

        # 6. PII Warning
        if vtype == VariableType.PII:
            issues.append({
                "issue": f"Donnée Personnelle Sensible ({meta.get('pii_type')})",
                "severity": "Critique",
                "count": n_non_null,
                "pct": 100.0 - missing_pct,
                "details": f"Conforme RGPD : {meta.get('pii_type')} détecté."
            })
            recommendations.append({
                "action": "Anonymisation ou Exclusion",
                "strategy": "drop_column",
                "justification": "Protection des données privées (RGPD) et absence d'intérêt statistique direct.",
                "priority": "Haute"
            })

        # Calculate top value frequencies for preview
        top_vals = non_null.value_counts().head(5).to_dict()
        stats["top_values"] = {str(k): int(v) for k, v in top_vals.items()}

        is_candidate_drop = any(rec["strategy"] == "drop_column" for rec in recommendations)
        drop_reason = next((rec["justification"] for rec in recommendations if rec["strategy"] == "drop_column"), None)

        return {
            "name": col_name,
            "pandas_dtype": str(series.dtype),
            "detected_type": vtype,
            "confidence": conf_label,
            "confidence_score": conf_score,
            "meta": meta,
            "stats": stats,
            "issues": issues,
            "recommendations": recommendations,
            "is_candidate_drop": is_candidate_drop,
            "candidate_drop_reason": drop_reason
        }

    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes complete multi-dimensional audit of dataset.
        
        Returns:
            Dictionary containing:
            - summary: general dataset stats
            - profiles: per-column profiles
            - global_issues: consolidated list of all quality issues
            - correlations: Pearson correlation matrix for numeric columns
        """
        n_rows = len(df)
        n_cols = len(df.columns)
        n_duplicates = int(df.duplicated().sum())

        profiles: Dict[str, Dict[str, Any]] = {}
        global_issues: List[Dict[str, Any]] = []

        for col in df.columns:
            profile = self.profile_column(df[col], col)
            profiles[col] = profile
            
            for issue in profile["issues"]:
                # Map to audit table entry
                rec = profile["recommendations"][0] if profile["recommendations"] else {"action": "Conserver", "justification": "Aucune action critique requise"}
                global_issues.append({
                    "variable": col,
                    "issue": issue["issue"],
                    "affected_count": issue["count"],
                    "affected_pct": issue["pct"],
                    "severity": issue["severity"],
                    "action": rec.get("action", "Conserver"),
                    "strategy": rec.get("strategy", "keep"),
                    "justification": rec.get("justification", ""),
                    "status": "À traiter"
                })

        # Global dataset issues
        if n_duplicates > 0:
            dup_pct = round((n_duplicates / n_rows) * 100, 2) if n_rows > 0 else 0.0
            global_issues.insert(0, {
                "variable": "[Toutes / Dataset]",
                "issue": "Lignes entièrement dupliquées",
                "affected_count": n_duplicates,
                "affected_pct": dup_pct,
                "severity": "Moyenne" if dup_pct < 10 else "Élevée",
                "action": "Suppression des doublons",
                "strategy": "drop_duplicates",
                "justification": f"{n_duplicates} lignes ({dup_pct}%) répétées à l'identique pouvant fausser les estimations.",
                "status": "À traiter"
            })

        # Numeric correlations
        num_cols = [c for c, p in profiles.items() if p["detected_type"] in [VariableType.NUMERIC_CONTINUOUS, VariableType.NUMERIC_DISCRETE] and pd.api.types.is_numeric_dtype(df[c])]
        correlations = {}
        if len(num_cols) >= 2:
            try:
                corr_df = df[num_cols].corr(method="pearson").round(3)
                correlations = corr_df.to_dict()
            except Exception:
                correlations = {}

        summary = {
            "rows": n_rows,
            "cols": n_cols,
            "total_cells": n_rows * n_cols,
            "total_duplicates": n_duplicates,
            "duplicate_pct": round((n_duplicates / n_rows) * 100, 2) if n_rows > 0 else 0.0,
            "total_missing_cells": sum(p["stats"]["missing_count"] for p in profiles.values()),
            "type_counts": pd.Series([p["detected_type"] for p in profiles.values()]).value_counts().to_dict(),
            "candidate_drop_columns": [c for c, p in profiles.items() if p["is_candidate_drop"]]
        }

        return {
            "summary": summary,
            "profiles": profiles,
            "global_issues": global_issues,
            "correlations": correlations
        }
