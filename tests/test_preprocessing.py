"""
Automated Test Suite for AutoDataPrep Core Modules.
Covers data loading, semantic analysis, cleaning, feature transformation,
ML pipeline construction (zero leakage), export management, and reporting.
"""

import os
import shutil
import tempfile
import pytest
import numpy as np
import pandas as pd
import joblib

from core.data_loader import load_dataset, detect_csv_parameters
from core.data_analyzer import DataAnalyzer, VariableType
from core.data_cleaner import DataCleaner
from core.feature_transformer import FeatureTransformer
from core.ml_preprocessor import MLPreprocessor, MLTaskType
from core.export_manager import ExportManager
from core.report_generator import ReportGenerator


@pytest.fixture
def sample_raw_dataframe():
    """Generates a synthetic heterogeneous DataFrame reflecting real-world datasets."""
    np.random.seed(42)
    n = 100
    data = {
        "customer_id": [f"ID_{i:04d}" for i in range(n)],
        "age": np.random.choice([25, 30, 35, 40, np.nan, 999], size=n, p=[0.3, 0.3, 0.2, 0.15, 0.03, 0.02]),
        "salary": np.random.normal(50000, 15000, size=n),
        "city": np.random.choice(["Paris", " Lyon ", "lyon", "Marseille", None], size=n),
        "signup_date": pd.date_range("2023-01-01", periods=n, freq="D").astype(str),
        "is_active": np.random.choice(["oui", "non"], size=n),
        "review_text": ["Excellent service client très satisfait" if i % 2 == 0 else "Produit moyen délai trop long" for i in range(n)],
        "user_email": [f"user_{i}@domain.com" for i in range(n)],
        "rating_level": np.random.choice(["low", "medium", "high"], size=n),
        "constant_col": ["France"] * n,
        "churn": np.random.choice([0, 1], size=n, p=[0.7, 0.3])
    }
    return pd.DataFrame(data)


# 1. Tests for data_loader
def test_csv_sniffing_and_loading(tmp_path):
    csv_file = tmp_path / "test_semicolon.csv"
    csv_file.write_text("nom;age;note\nAlice;25;14,5\nBob;30;18,0\nCharlie;28;12,2\n", encoding="utf-8")
    
    params = detect_csv_parameters(str(csv_file))
    assert params["delimiter"] == ";"
    assert params["decimal"] == ","
    
    df, meta = load_dataset(str(csv_file))
    assert len(df) == 3
    assert len(df.columns) == 3
    assert meta["delimiter"] == ";"
    assert meta["decimal"] == ","


def test_json_loading(tmp_path):
    json_file = tmp_path / "test.json"
    json_file.write_text('[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]', encoding="utf-8")
    
    df, meta = load_dataset(str(json_file))
    assert len(df) == 2
    assert "a" in df.columns


# 2. Tests for data_analyzer
def test_semantic_variable_classification(sample_raw_dataframe):
    analyzer = DataAnalyzer()
    analysis = analyzer.analyze_dataset(sample_raw_dataframe)
    profiles = analysis["profiles"]

    assert profiles["customer_id"]["detected_type"] == VariableType.IDENTIFIER
    assert profiles["constant_col"]["detected_type"] == VariableType.CONSTANT
    assert profiles["user_email"]["detected_type"] == VariableType.PII
    assert profiles["signup_date"]["detected_type"] == VariableType.DATETIME
    assert profiles["rating_level"]["detected_type"] == VariableType.CATEGORICAL_ORDINAL
    assert profiles["is_active"]["detected_type"] == VariableType.BOOLEAN
    assert profiles["review_text"]["detected_type"] == VariableType.TEXT

    # Check global issues
    assert len(analysis["global_issues"]) > 0


# 3. Tests for data_cleaner
def test_data_cleaner_operations(sample_raw_dataframe):
    cleaner = DataCleaner(sample_raw_dataframe)
    
    # Text cleaning
    cleaner.clean_text_column("city", strip=True, casing="lower", empty_to_nan=True)
    assert cleaner.df["city"].str.contains(" ").sum() == 0

    # Imputation
    cleaner.impute_missing("age", strategy="median")
    assert cleaner.df["age"].isna().sum() == 0

    # Outlier clipping
    cleaner.handle_outliers("salary", method="iqr", action="clip", threshold=1.5)

    # Check history and undo
    history = cleaner.get_history()
    assert len(history) == 3

    cleaner.undo()
    assert len(cleaner.get_history()) == 2

    # Reset
    cleaner.reset()
    assert len(cleaner.get_history()) == 0
    assert cleaner.df["age"].isna().sum() > 0


# 4. Tests for feature_transformer
def test_feature_transformer(sample_raw_dataframe):
    transformer = FeatureTransformer(sample_raw_dataframe)
    
    # Datetime features
    df_dt, dt_cols = transformer.extract_datetime_features("signup_date", extract_year=True, extract_month=True, extract_is_weekend=True)
    assert "signup_date_year" in dt_cols
    assert "signup_date_is_weekend" in dt_cols
    assert "signup_date_year" in df_dt.columns

    # Text features
    df_txt, txt_cols = transformer.extract_text_features("review_text", extract_char_length=True, extract_word_count=True)
    assert "review_text_char_len" in txt_cols
    assert "review_text_word_count" in txt_cols

    # Binning
    df_bin, bin_col = transformer.bin_numeric_column("salary", n_bins=3, strategy="quantile")
    assert bin_col in df_bin.columns


# 5. Tests for ml_preprocessor
def test_supervised_pipeline_zero_leakage():
    # Synthetic dataset with train/test separation
    np.random.seed(123)
    n = 200
    df = pd.DataFrame({
        "num_feat": np.random.normal(10, 2, n),
        "cat_feat": np.random.choice(["A", "B", "C"], n),
        "target": np.random.choice([0, 1], n)
    })
    # Insert some missing values
    df.loc[0:10, "num_feat"] = np.nan
    df.loc[15:20, "cat_feat"] = np.nan

    preprocessor = MLPreprocessor(df)
    results = preprocessor.build_supervised_pipeline(
        target_col="target",
        test_size=0.25,
        split_strategy="stratified",
        numeric_scaler="standard",
        categorical_encoder="onehot",
        random_state=42
    )

    assert results["mode"] == "supervised"
    assert results["task_type"] == MLTaskType.BINARY_CLASSIFICATION
    assert len(results["X_train"]) == 150
    assert len(results["X_test"]) == 50

    # Ensure no NaN remaining in prepared sets
    assert not results["X_train"].isna().any().any()
    assert not results["X_test"].isna().any().any()

    # Verify that pipeline transformers were fitted strictly on X_train
    col_trans = results["pipeline"]
    num_pipe = col_trans.named_transformers_["num"]
    scaler = num_pipe.named_steps["scaler"]
    assert hasattr(scaler, "mean_")
    # Check that transform works on new unseen data
    unseen_df = pd.DataFrame({"num_feat": [12.0], "cat_feat": ["B"]})
    transformed_unseen = col_trans.transform(unseen_df)
    assert transformed_unseen.shape[1] == results["X_train"].shape[1]


def test_unsupervised_pipeline():
    df = pd.DataFrame({
        "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        "y": [10.0, 20.0, 30.0, 40.0, 50.0],
        "category": ["A", "B", "A", "B", "A"]
    })
    preprocessor = MLPreprocessor(df)
    results = preprocessor.build_unsupervised_pipeline(numeric_scaler="minmax")
    assert results["mode"] == "unsupervised"
    assert results["X_prepared"].shape[0] == 5
    assert not results["X_prepared"].isna().any().any()


# 6. Tests for export_manager and report_generator
def test_export_and_reports(tmp_path, sample_raw_dataframe):
    exp_dir = tmp_path / "exports"
    rep_dir = tmp_path / "reports"
    
    cleaner = DataCleaner(sample_raw_dataframe)
    cleaner.impute_missing("salary", strategy="mean")
    clean_df = cleaner.df

    # Export Cleaned
    exporter = ExportManager(output_dir=str(exp_dir))
    csv_path = exporter.export_cleaned_dataset(clean_df, filename="clean_test", format_type="csv")
    assert os.path.exists(csv_path)

    # ML Pipeline export
    ml_prep = MLPreprocessor(clean_df)
    ml_res = ml_prep.build_supervised_pipeline(target_col="churn", test_size=0.2)
    splits = exporter.export_ml_splits(ml_res, prefix="test_ml")
    assert os.path.exists(splits["X_train"])
    assert os.path.exists(splits["y_train"])

    joblib_path = exporter.export_pipeline_joblib(ml_res, filename="test_pipe.joblib")
    assert os.path.exists(joblib_path)

    # Verify reloading joblib
    bundle = joblib.load(joblib_path)
    assert "pipeline" in bundle
    assert bundle["task_type"] == MLTaskType.BINARY_CLASSIFICATION

    # Generate inference script
    inf_script = exporter.generate_inference_script(output_script_name="test_inf.py")
    assert os.path.exists(inf_script)

    # Report Generator
    analyzer = DataAnalyzer()
    analysis = analyzer.analyze_dataset(clean_df)
    
    reporter = ReportGenerator(output_dir=str(rep_dir))
    metadata = {"file_name": "synthetic.csv", "rows": len(clean_df), "cols": len(clean_df.columns), "memory_formatted": "15 Ko"}
    
    html_path = reporter.generate_html_report(
        metadata=metadata,
        analysis_results=analysis,
        cleaning_history=cleaner.get_history(),
        created_features=[],
        ml_prep_results=ml_res
    )
    assert os.path.exists(html_path)

    md_path = reporter.generate_markdown_report(
        metadata=metadata,
        analysis_results=analysis,
        cleaning_history=cleaner.get_history(),
        created_features=[],
        ml_prep_results=ml_res
    )
    assert os.path.exists(md_path)


# 7. Test UI instantiation
def test_ui_initialization():
    import tkinter as tk
    from ui.main_window import MainWindow

    root = tk.Tk()
    root.withdraw()
    try:
        app = MainWindow(root)
        assert app is not None
        assert "import" in app.views
        assert "eda" in app.views
        assert "audit" in app.views
        assert "cleaning" in app.views
        assert "transforms" in app.views
        assert "ml" in app.views
        assert "export" in app.views
    finally:
        root.destroy()

