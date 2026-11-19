"""
Module: api/routes/dataset.py
Description: API endpoints for dataset operations (upload, preview, metadata).
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import numpy as np

from core.data_loader import load_dataset, detect_csv_parameters
from core.data_cleaner import DataCleaner
from core.feature_transformer import FeatureTransformer
from core.ml_preprocessor import MLPreprocessor
from api.models.dataset import DatasetMetadata, DatasetPreviewRequest, DatasetPreviewResponse, CSVParameters, TargetSelectionRequest
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


def get_session_data(session_id: str):
    """Get session data or raise 404."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a dataset first.")
    return session_store[session_id]


def get_cleaner(session_data: dict):
    """Reconstruct DataCleaner from session DataFrame."""
    from core.data_cleaner import DataCleaner
    df = session_data["df"]
    cleaner = DataCleaner(df)
    # Apply cleaning history if exists
    for op in session_data.get("cleaning_history", []):
        # Note: We would need to replay operations here
        pass
    return cleaner


def get_transformer(session_data: dict):
    """Reconstruct FeatureTransformer from session DataFrame."""
    from core.feature_transformer import FeatureTransformer
    df = session_data["df"]
    return FeatureTransformer(df)


router = APIRouter()

# Temporary upload directory
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=DatasetMetadata)
async def upload_dataset(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    delimiter: Optional[str] = Form(None),
    encoding: Optional[str] = Form(None),
    decimal: Optional[str] = Form(None)
):
    """
    Upload and load a dataset.
    Supports CSV, Excel, JSON, Parquet.
    """
    try:
        # Save uploaded file temporarily
        file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Load dataset with parameters
        load_params = {}
        if delimiter:
            load_params["delimiter"] = delimiter
        if encoding:
            load_params["encoding"] = encoding
        if decimal:
            load_params["decimal"] = decimal
        
        df, metadata = load_dataset(str(file_path), **load_params)
        
        cleaner = DataCleaner(df)
        session_store[session_id] = {
            "file_path": str(file_path),
            "metadata": metadata,
            "df": df,
            "initial_df": df.copy(),
            "cleaner": cleaner,
            "analysis_results": None,
            "ml_prep_results": None,
            "cleaning_history": cleaner.history,
            "created_features": []
        }
        
        return DatasetMetadata(**metadata)
    
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=400, detail=f"Error loading dataset: {str(e)}")


@router.get("/metadata", response_model=DatasetMetadata)
async def get_metadata(session_id: str):
    """Get metadata of the loaded dataset."""
    session_data = get_session_data(session_id)
    df = session_data.get("df")
    meta = session_data.get("metadata", {}).copy()
    if df is not None:
        meta["total_rows"] = len(df)
        meta["total_columns"] = len(df.columns)
        meta["columns"] = list(df.columns)
        meta["dtypes"] = {col: str(dtype) for col, dtype in df.dtypes.items()}
        session_data["metadata"] = meta
    return DatasetMetadata(**meta)


@router.post("/preview", response_model=DatasetPreviewResponse)
async def get_preview(request: DatasetPreviewRequest, session_id: str):
    """Get paginated preview of the dataset."""
    session_data = get_session_data(session_id)
    df = session_data["df"]
    
    total_rows = len(df)
    total_pages = (total_rows - 1) // request.page_size + 1
    
    start = request.page * request.page_size
    end = min(start + request.page_size, total_rows)
    
    # Convert DataFrame to list of dicts for JSON serialization
    preview_data = df.iloc[start:end].fillna("<NA>").to_dict(orient="records")
    columns = list(df.columns)
    
    return DatasetPreviewResponse(
        data=preview_data,
        columns=columns,
        total_rows=total_rows,
        page=request.page,
        page_size=request.page_size,
        total_pages=total_pages
    )


@router.delete("/delete")
async def delete_dataset(session_id: str):
    """Delete the dataset from session and clean up files."""
    if session_id in session_store:
        session_data = session_store[session_id]
        file_path = session_data.get("file_path")
        
        # Clean up temporary file
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()
        
        del session_store[session_id]
    
    return {"message": "Dataset deleted successfully"}


@router.post("/reload")
async def reload_dataset(
    session_id: str,
    delimiter: Optional[str] = Form(None),
    encoding: Optional[str] = Form(None),
    decimal: Optional[str] = Form(None)
):
    """
    Reload dataset with different CSV parameters.
    """
    session_data = get_session_data(session_id)
    file_path = session_data["file_path"]
    
    try:
        load_params = {}
        if delimiter:
            load_params["delimiter"] = delimiter
        if encoding:
            load_params["encoding"] = encoding
        if decimal:
            load_params["decimal"] = decimal
        
        df, metadata = load_dataset(file_path, **load_params)
        
        cleaner = DataCleaner(df)
        session_store[session_id] = {
            "file_path": file_path,
            "metadata": metadata,
            "df": df,
            "initial_df": df.copy(),
            "cleaner": cleaner,
            "analysis_results": None,
            "ml_prep_results": None,
            "cleaning_history": cleaner.history,
            "created_features": []
        }
        
        return DatasetMetadata(**metadata)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reloading dataset: {str(e)}")


@router.post("/select-target")
async def select_target_variable(request: TargetSelectionRequest, session_id: str):
    """
    Select target variable and learning mode for ML preparation.
    """
    session_data = get_session_data(session_id)
    
    # Get df from session - it might be stored directly or in cleaner
    if "df" in session_data:
        df = session_data["df"]
    elif "cleaner" in session_data and hasattr(session_data["cleaner"], "df"):
        df = session_data["cleaner"].df
    else:
        raise HTTPException(status_code=400, detail="No dataset found in session. Please upload a dataset first.")
    
    if request.target_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{request.target_column}' not found in dataset")
    
    try:
        # Store target selection in session
        session_data["target_column"] = request.target_column
        session_data["learning_mode"] = request.learning_mode
        
        # If supervised, infer task type
        if request.learning_mode == "supervised":
            preprocessor = MLPreprocessor(df)
            task_type, imbalance_info = preprocessor.infer_task_type(df[request.target_column])
            
            return {
                "message": f"Target variable '{request.target_column}' selected successfully",
                "target_column": request.target_column,
                "learning_mode": request.learning_mode,
                "task_type": task_type,
                "imbalance_info": convert_numpy_types(imbalance_info)
            }
        else:
            return {
                "message": f"Unsupervised mode selected",
                "target_column": None,
                "learning_mode": request.learning_mode,
                "task_type": "Apprentissage Non Supervisé",
                "imbalance_info": None
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting target: {str(e)}")
