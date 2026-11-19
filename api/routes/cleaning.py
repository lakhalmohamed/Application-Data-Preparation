"""
Module: api/routes/cleaning.py
Description: API endpoints for data cleaning operations.
"""

from fastapi import APIRouter, HTTPException
from api.models.cleaning import (
    ImputationRequest, OutlierRequest, TextCleaningRequest,
    DuplicateRemovalRequest, ColumnDropRequest, CleaningHistoryResponse
)
from api.session import session_store

router = APIRouter()


def get_session_data(session_id: str):
    """Get session data or raise 404."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a dataset first.")
    return session_store[session_id]


def get_cleaner(session_data: dict):
    """Retrieve existing DataCleaner from session or initialize one."""
    if "cleaner" not in session_data or session_data["cleaner"] is None:
        from core.data_cleaner import DataCleaner
        session_data["cleaner"] = DataCleaner(session_data["df"])
    return session_data["cleaner"]


def sync_session_after_cleaning(session_data: dict, cleaner):
    """Keep session dataframe, history, and metadata synchronized."""
    session_data["df"] = cleaner.df
    session_data["cleaning_history"] = cleaner.history
    session_data["cleaner"] = cleaner
    if "metadata" in session_data and isinstance(session_data["metadata"], dict):
        session_data["metadata"]["columns"] = list(cleaner.df.columns)
        session_data["metadata"]["total_columns"] = len(cleaner.df.columns)
        session_data["metadata"]["total_rows"] = len(cleaner.df)
    if "transformer" in session_data and session_data["transformer"] is not None:
        try:
            session_data["transformer"] = type(session_data["transformer"])(cleaner.df)
        except Exception:
            pass


@router.post("/impute")
async def impute_missing(request: ImputationRequest, session_id: str):
    """
    Impute missing values in a column.
    Strategies: mean, median, mode, constant, drop_rows, forward_fill, backward_fill, knn
    """
    session_data = get_session_data(session_id)
    cleaner = get_cleaner(session_data)
    
    try:
        cleaner.impute_missing(
            column=request.column,
            strategy=request.strategy,
            fill_value=request.fill_value,
            knn_neighbors=request.knn_neighbors
        )
        sync_session_after_cleaning(session_data, cleaner)
        return {"message": f"Imputation completed for column '{request.column}'"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Imputation error: {str(e)}")


@router.post("/outliers")
async def handle_outliers(request: OutlierRequest, session_id: str):
    """
    Treat outliers in a numeric column.
    Methods: iqr, zscore
    Actions: clip, nan, drop
    """
    session_data = get_session_data(session_id)
    cleaner = get_cleaner(session_data)
    
    try:
        df, count = cleaner.handle_outliers(
            column=request.column,
            method=request.method,
            action=request.action,
            threshold=request.threshold
        )
        sync_session_after_cleaning(session_data, cleaner)
        return {"message": f"Treated {count} outliers in column '{request.column}'"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Outlier treatment error: {str(e)}")


@router.post("/text")
async def clean_text(request: TextCleaningRequest, session_id: str):
    """
    Clean text column (strip, normalize case, handle empty strings).
    """
    session_data = get_session_data(session_id)
    cleaner = get_cleaner(session_data)
    
    try:
        cleaner.clean_text_column(
            column=request.column,
            strip=request.strip,
            casing=request.casing,
            empty_to_nan=request.empty_to_nan
        )
        sync_session_after_cleaning(session_data, cleaner)
        return {"message": f"Text cleaning completed for column '{request.column}'"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Text cleaning error: {str(e)}")


@router.post("/duplicates")
async def remove_duplicates(request: DuplicateRemovalRequest, session_id: str):
    """
    Remove duplicate rows.
    """
    session_data = get_session_data(session_id)
    cleaner = get_cleaner(session_data)
    
    try:
        df, count = cleaner.remove_duplicates(
            subset=request.subset,
            keep=request.keep
        )
        sync_session_after_cleaning(session_data, cleaner)
        return {"message": f"Removed {count} duplicate rows"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Duplicate removal error: {str(e)}")


@router.post("/drop-columns")
async def drop_columns(request: ColumnDropRequest, session_id: str):
    """
    Drop specified columns from the dataset.
    """
    session_data = get_session_data(session_id)
    cleaner = get_cleaner(session_data)
    
    try:
        cleaner.drop_columns(request.columns)
        sync_session_after_cleaning(session_data, cleaner)
        return {"message": f"Dropped columns: {', '.join(request.columns)}"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Column drop error: {str(e)}")


@router.post("/undo")
async def undo_last_operation(session_id: str):
    """
    Undo the last cleaning operation.
    """
    session_data = get_session_data(session_id)
    cleaner = get_cleaner(session_data)
    
    try:
        result = cleaner.undo()
        if result is None:
            return {"message": "Nothing to undo"}
        
        sync_session_after_cleaning(session_data, cleaner)
        return {"message": "Last operation undone successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Undo error: {str(e)}")


@router.post("/reset")
async def reset_dataset(session_id: str):
    """
    Reset dataset to its original state (undo all operations).
    """
    session_data = get_session_data(session_id)
    cleaner = get_cleaner(session_data)
    
    try:
        result = cleaner.reset()
        sync_session_after_cleaning(session_data, cleaner)
        session_data["created_features"] = []
        return {"message": "Dataset reset successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset error: {str(e)}")


@router.get("/history", response_model=CleaningHistoryResponse)
async def get_cleaning_history(session_id: str):
    """
    Get the history of cleaning operations.
    """
    session_data = get_session_data(session_id)
    cleaner = get_cleaner(session_data)
    history = cleaner.history
    df = session_data["df"]
    
    history_dicts = []
    for op in history:
        if hasattr(op, 'to_dict'):
            history_dicts.append(op.to_dict())
        elif hasattr(op, 'model_dump'):
            history_dicts.append(op.model_dump())
        elif hasattr(op, 'dict'):
            history_dicts.append(op.dict())
        elif isinstance(op, dict):
            history_dicts.append(op)
        else:
            history_dicts.append({
                "timestamp": str(getattr(op, 'timestamp', '')),
                "operation": str(getattr(op, 'op_type', getattr(op, 'operation', 'Opération'))),
                "column": str(getattr(op, 'column', '[Global]')),
                "strategy": str(getattr(op, 'strategy', '')),
                "details": str(getattr(op, 'details', '')),
                "params": getattr(op, 'params', {}) or {}
            })
    
    return CleaningHistoryResponse(
        history=history_dicts,
        current_rows=len(df),
        current_cols=len(df.columns)
    )
