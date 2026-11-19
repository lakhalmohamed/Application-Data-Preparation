"""
Module: core/export_manager.py
Description: Manages exports of cleaned datasets, train/test splits, serialized Scikit-learn
             pipelines (.joblib), and ready-to-use Python inference code templates.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import joblib


class ExportManager:
    """Handles export of datasets, Scikit-learn pipelines, and code artifacts."""

    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_cleaned_dataset(
        self,
        df: pd.DataFrame,
        filename: str = "dataset_cleaned",
        format_type: str = "csv"
    ) -> str:
        """
        Exports cleaned dataset to CSV or Excel.
        format_type: 'csv' or 'excel'
        """
        if format_type.lower() == "csv":
            path = self.output_dir / f"{filename}.csv"
            df.to_csv(path, index=False, encoding="utf-8")
        elif format_type.lower() in ["excel", "xlsx"]:
            path = self.output_dir / f"{filename}.xlsx"
            df.to_excel(path, index=False, engine="openpyxl")
        else:
            raise ValueError(f"Format non supporté : {format_type}")

        return str(path.resolve())

    def export_ml_splits(
        self,
        ml_prep_results: Dict[str, Any],
        prefix: str = "ml_data",
        format_type: str = "csv"
    ) -> Dict[str, str]:
        """
        Exports ML train/test splits or prepared unsupervised dataset.
        """
        saved_paths = {}
        mode = ml_prep_results.get("mode", "supervised")

        if mode == "supervised":
            X_train = ml_prep_results["X_train"]
            X_test = ml_prep_results["X_test"]
            y_train = ml_prep_results["y_train"]
            y_test = ml_prep_results["y_test"]

            if format_type.lower() == "csv":
                p_xtrain = self.output_dir / f"{prefix}_X_train.csv"
                p_xtest = self.output_dir / f"{prefix}_X_test.csv"
                p_ytrain = self.output_dir / f"{prefix}_y_train.csv"
                p_ytest = self.output_dir / f"{prefix}_y_test.csv"

                X_train.to_csv(p_xtrain, index=False)
                X_test.to_csv(p_xtest, index=False)
                pd.DataFrame(y_train).to_csv(p_ytrain, index=False)
                pd.DataFrame(y_test).to_csv(p_ytest, index=False)

                saved_paths["X_train"] = str(p_xtrain.resolve())
                saved_paths["X_test"] = str(p_xtest.resolve())
                saved_paths["y_train"] = str(p_ytrain.resolve())
                saved_paths["y_test"] = str(p_ytest.resolve())

            elif format_type.lower() in ["excel", "xlsx"]:
                path_excel = self.output_dir / f"{prefix}_splits.xlsx"
                with pd.ExcelWriter(path_excel, engine="openpyxl") as writer:
                    X_train.to_excel(writer, sheet_name="X_train", index=False)
                    X_test.to_excel(writer, sheet_name="X_test", index=False)
                    pd.DataFrame(y_train).to_excel(writer, sheet_name="y_train", index=False)
                    pd.DataFrame(y_test).to_excel(writer, sheet_name="y_test", index=False)
                saved_paths["excel_splits"] = str(path_excel.resolve())

        else:
            # Unsupervised
            X_prep = ml_prep_results["X_prepared"]
            if format_type.lower() == "csv":
                path_csv = self.output_dir / f"{prefix}_X_prepared.csv"
                X_prep.to_csv(path_csv, index=False)
                saved_paths["X_prepared"] = str(path_csv.resolve())
            else:
                path_excel = self.output_dir / f"{prefix}_prepared.xlsx"
                X_prep.to_excel(path_excel, sheet_name="X_prepared", index=False)
                saved_paths["excel_prepared"] = str(path_excel.resolve())

        return saved_paths

    def export_pipeline_joblib(
        self,
        ml_prep_results: Dict[str, Any],
        filename: str = "fitted_pipeline.joblib"
    ) -> str:
        """
        Serializes the fitted Scikit-learn Pipeline and metadata via Joblib.
        """
        path = self.output_dir / filename
        bundle = {
            "mode": ml_prep_results.get("mode"),
            "task_type": ml_prep_results.get("task_type"),
            "target_col": ml_prep_results.get("target_col"),
            "pipeline": ml_prep_results["pipeline"],
            "label_encoder": ml_prep_results.get("label_encoder"),
            "feature_names_in": ml_prep_results.get("feature_names_in"),
            "feature_names_out": ml_prep_results.get("feature_names_out"),
            "scaler": ml_prep_results.get("numeric_scaler"),
            "encoder": ml_prep_results.get("categorical_encoder")
        }
        joblib.dump(bundle, path)
        return str(path.resolve())

    def generate_inference_script(
        self,
        pipeline_joblib_name: str = "fitted_pipeline.joblib",
        output_script_name: str = "run_inference.py"
    ) -> str:
        """
        Generates a standalone Python script demonstrating how to reload
        the joblib preprocessor pipeline and transform new raw data.
        """
        script_code = f'''"""
Production Inference Script
Generated by AutoDataPrep.
Demonstrates loading the serialized preprocessing pipeline and transforming new incoming data.
"""

import joblib
import pandas as pd

def transform_new_data(raw_data_path: str):
    # 1. Load the serialized preprocessor bundle
    print("Loading pipeline bundle from {pipeline_joblib_name}...")
    bundle = joblib.load("{pipeline_joblib_name}")
    pipeline = bundle["pipeline"]
    features_in = bundle["feature_names_in"]
    features_out = bundle["feature_names_out"]
    
    print(f"Expected input features ({{len(features_in)}}): {{features_in}}")
    
    # 2. Read new incoming raw dataset
    df_new = pd.read_csv(raw_data_path)
    
    # Check that required features are present
    missing_cols = set(features_in) - set(df_new.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in incoming data: {{missing_cols}}")
    
    # 3. Apply the fitted pipeline (transform only, no refitting!)
    X_raw = df_new[features_in]
    X_transformed = pipeline.transform(X_raw)
    
    # 4. Convert to DataFrame with output feature names
    df_transformed = pd.DataFrame(X_transformed, columns=features_out)
    print(f"Transformed data successfully shape: {{df_transformed.shape}}")
    return df_transformed

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = transform_new_data(sys.argv[1])
        print(result.head())
    else:
        print("Usage: python run_inference.py <path_to_new_data.csv>")
'''
        script_path = self.output_dir / output_script_name
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_code)

        return str(script_path.resolve())
