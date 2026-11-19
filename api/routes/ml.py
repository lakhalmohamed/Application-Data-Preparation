"""
Module: api/routes/ml.py
Description: API endpoints for Machine Learning preparation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import numpy as np

from core.ml_preprocessor import MLPreprocessor
from api.session import session_store


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

router = APIRouter()


class SupervisedMLRequest(BaseModel):
    """Request for supervised ML pipeline."""
    target_col: str
    feature_cols: Optional[List[str]] = None
    test_size: float = 0.2
    split_strategy: str = "stratified"  # stratified, random, chronological
    temporal_col: Optional[str] = None
    numeric_scaler: str = "standard"  # standard, minmax, robust, none
    categorical_encoder: str = "onehot"  # onehot, ordinal, none
    random_state: int = 42


class UnsupervisedMLRequest(BaseModel):
    """Request for unsupervised ML pipeline."""
    feature_cols: Optional[List[str]] = None
    numeric_scaler: str = "standard"
    categorical_encoder: str = "onehot"


def get_session_data(session_id: str):
    """Get session data or raise 404."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a dataset first.")
    return session_store[session_id]


@router.post("/supervised")
async def build_supervised_pipeline(request: SupervisedMLRequest, session_id: str):
    """
    Build and fit a supervised ML pipeline with zero data leakage.
    """
    session_data = get_session_data(session_id)
    
    # Get df from session - it might be stored directly or in cleaner
    if "df" in session_data:
        df = session_data["df"]
    elif "cleaner" in session_data and hasattr(session_data["cleaner"], "df"):
        df = session_data["cleaner"].df
    else:
        raise HTTPException(status_code=400, detail="No dataset found in session. Please upload a dataset first.")
    
    try:
        preprocessor = MLPreprocessor(df)
        results = preprocessor.build_supervised_pipeline(
            target_col=request.target_col,
            feature_cols=request.feature_cols,
            test_size=request.test_size,
            split_strategy=request.split_strategy,
            temporal_col=request.temporal_col,
            numeric_scaler=request.numeric_scaler,
            categorical_encoder=request.categorical_encoder,
            random_state=request.random_state
        )
        
        # Store results in session (convert non-serializable objects)
        session_data["ml_prep_results"] = {
            "mode": results["mode"],
            "task_type": results["task_type"],
            "target_col": results["target_col"],
            "dropped_target_na": convert_numpy_types(results["dropped_target_na"]),
            "imbalance_info": convert_numpy_types(results["imbalance_info"]),
            "leakage_warnings": convert_numpy_types(results["leakage_warnings"]),
            "split_strategy": results["split_strategy"],
            "test_size": results["test_size"],
            "random_state": results["random_state"],
            "numeric_scaler": results["numeric_scaler"],
            "categorical_encoder": results["categorical_encoder"],
            # Don't store pipeline and label_encoder in session (non-serializable)
            # They will be reconstructed when needed for export
            "feature_names_in": results["feature_names_in"],
            "feature_names_out": results["feature_names_out"],
            "X_train_shape": results["X_train"].shape,
            "X_test_shape": results["X_test"].shape,
            "y_train": results["y_train"].tolist(),
            "y_test": results["y_test"].tolist(),
            "recommended_models": results["recommended_models"]
        }
        
        return {
            "message": "Supervised ML pipeline built successfully",
            "task_type": results["task_type"],
            "X_train_shape": results["X_train"].shape,
            "X_test_shape": results["X_test"].shape,
            "feature_names_out": results["feature_names_out"],
            "leakage_warnings": convert_numpy_types(results["leakage_warnings"]),
            "imbalance_info": convert_numpy_types(results["imbalance_info"]),
            "recommended_models": results["recommended_models"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ML pipeline error: {str(e)}")


@router.post("/unsupervised")
async def build_unsupervised_pipeline(request: UnsupervisedMLRequest, session_id: str):
    """
    Build and fit an unsupervised ML pipeline.
    """
    session_data = get_session_data(session_id)
    
    # Get df from session - it might be stored directly or in cleaner
    if "df" in session_data:
        df = session_data["df"]
    elif "cleaner" in session_data and hasattr(session_data["cleaner"], "df"):
        df = session_data["cleaner"].df
    else:
        raise HTTPException(status_code=400, detail="No dataset found in session. Please upload a dataset first.")
    
    try:
        preprocessor = MLPreprocessor(df)
        results = preprocessor.build_unsupervised_pipeline(
            feature_cols=request.feature_cols,
            numeric_scaler=request.numeric_scaler,
            categorical_encoder=request.categorical_encoder
        )
        
        # Store results in session (convert non-serializable objects)
        session_data["ml_prep_results"] = {
            "mode": results["mode"],
            "task_type": results["task_type"],
            "numeric_scaler": results["numeric_scaler"],
            "categorical_encoder": results["categorical_encoder"],
            # Don't store pipeline in session (non-serializable)
            # It will be reconstructed when needed for export
            "feature_names_in": results["feature_names_in"],
            "feature_names_out": results["feature_names_out"],
            "X_prepared_shape": results["X_prepared"].shape,
            "recommended_models": results["recommended_models"]
        }
        
        return {
            "message": "Unsupervised ML pipeline built successfully",
            "X_prepared_shape": results["X_prepared"].shape,
            "feature_names_out": results["feature_names_out"],
            "recommended_models": results["recommended_models"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unsupervised pipeline error: {str(e)}")


@router.get("/results")
async def get_ml_results(session_id: str):
    """
    Get ML preparation results.
    """
    session_data = get_session_data(session_id)
    results = session_data.get("ml_prep_results")
    
    if results is None:
        raise HTTPException(status_code=404, detail="No ML results found. Please build a pipeline first.")
    
    # Return serializable data only
    return {
        "mode": results.get("mode"),
        "task_type": results.get("task_type"),
        "target_col": results.get("target_col"),
        "imbalance_info": results.get("imbalance_info"),
        "leakage_warnings": results.get("leakage_warnings"),
        "split_strategy": results.get("split_strategy"),
        "test_size": results.get("test_size"),
        "numeric_scaler": results.get("numeric_scaler"),
        "categorical_encoder": results.get("categorical_encoder"),
        "feature_names_in": results.get("feature_names_in"),
        "feature_names_out": results.get("feature_names_out"),
        "X_train_shape": results.get("X_train_shape"),
        "X_test_shape": results.get("X_test_shape"),
        "X_prepared_shape": results.get("X_prepared_shape"),
        "recommended_models": results.get("recommended_models")
    }
