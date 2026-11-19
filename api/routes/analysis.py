"""
Module: api/routes/analysis.py
Description: API endpoints for data analysis operations.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import pandas as pd

from core.data_analyzer import DataAnalyzer
from api.models.analysis import AnalysisResults, ColumnProfile, ComparisonRequest
from api.session import session_store

router = APIRouter()


def get_session_data(session_id: str):
    """Get session data or raise 404."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a dataset first.")
    return session_store[session_id]


@router.post("/run", response_model=AnalysisResults)
async def run_analysis(session_id: str):
    """
    Run complete semantic analysis on the dataset.
    """
    session_data = get_session_data(session_id)
    df = session_data["df"]
    
    try:
        analyzer = DataAnalyzer()
        results = analyzer.analyze_dataset(df)
        
        # Store results in session
        session_data["analysis_results"] = results
        
        return AnalysisResults(**results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running analysis: {str(e)}")


@router.get("/results", response_model=AnalysisResults)
async def get_analysis_results(session_id: str):
    """
    Get previously computed analysis results.
    """
    session_data = get_session_data(session_id)
    results = session_data.get("analysis_results")
    
    if results is None:
        raise HTTPException(status_code=404, detail="No analysis results found. Please run analysis first.")
    
    return AnalysisResults(**results)


@router.get("/profile/{column_name}", response_model=ColumnProfile)
async def get_column_profile(column_name: str, session_id: str):
    """
    Get detailed profile for a specific column.
    """
    session_data = get_session_data(session_id)
    results = session_data.get("analysis_results")
    
    if results is None:
        raise HTTPException(status_code=404, detail="No analysis results found. Please run analysis first.")
    
    profiles = results.get("profiles", {})
    
    if column_name not in profiles:
        raise HTTPException(status_code=404, detail=f"Column '{column_name}' not found in analysis results.")
    
    return ColumnProfile(**profiles[column_name])


@router.get("/correlations")
async def get_correlations(session_id: str):
    """
    Get correlation matrix for numeric columns.
    """
    session_data = get_session_data(session_id)
    results = session_data.get("analysis_results")
    
    if results is None:
        raise HTTPException(status_code=404, detail="No analysis results found. Please run analysis first.")
    
    return {"correlations": results.get("correlations", {})}


@router.get("/summary")
async def get_analysis_summary(session_id: str):
    """
    Get analysis summary only.
    """
    session_data = get_session_data(session_id)
    results = session_data.get("analysis_results")
    
    if results is None:
        raise HTTPException(status_code=404, detail="No analysis results found. Please run analysis first.")
    
    return {"summary": results.get("summary", {})}


@router.get("/correlation-heatmap")
async def get_correlation_heatmap(session_id: str):
    """
    Get correlation matrix data formatted for Plotly heatmap visualization.
    """
    session_data = get_session_data(session_id)
    results = session_data.get("analysis_results")
    
    if results is None:
        raise HTTPException(status_code=404, detail="No analysis results found. Please run analysis first.")
    
    correlations = results.get("correlations", {})
    
    if not correlations:
        return {
            "z": [],
            "x": [],
            "y": [],
            "message": "No numeric columns found for correlation analysis"
        }
    
    # Extract column names and correlation matrix
    columns = list(correlations.keys())
    z_matrix = []
    
    for col_y in columns:
        row = []
        for col_x in columns:
            # Get correlation value (handle self-correlation)
            if col_x == col_y:
                row.append(1.0)
            else:
                val = correlations.get(col_x, {}).get(col_y, 0.0)
                row.append(val)
        z_matrix.append(row)
    
    return {
        "z": z_matrix,
        "x": columns,
        "y": columns,
        "message": f"Correlation matrix for {len(columns)} numeric columns"
    }


@router.post("/compare")
async def compare_before_after(request: ComparisonRequest, session_id: str):
    """
    Compare original dataset with current (cleaned) dataset.
    Returns statistics for the entire dataset or a specific column.
    """
    session_data = get_session_data(session_id)
    df_current = session_data["df"]
    metadata = session_data["metadata"]
    
    # Get original dataset from session or reload from file
    df_original = session_data.get("initial_df")
    if df_original is None:
        from core.data_loader import load_dataset
        file_path = session_data["file_path"]
        df_original, _ = load_dataset(file_path)
    
    try:
        if request.column:
            # Compare specific column
            if request.column not in df_current.columns:
                raise HTTPException(status_code=400, detail=f"Column '{request.column}' not found")
            
            col_original = df_original[request.column]
            col_current = df_current[request.column]
            
            # Calculate statistics
            original_stats = {
                "missing_count": int(col_original.isna().sum()),
                "missing_pct": round(col_original.isna().sum() / len(col_original) * 100, 2),
                "unique_count": int(col_original.nunique()),
                "dtype": str(col_original.dtype)
            }
            
            current_stats = {
                "missing_count": int(col_current.isna().sum()),
                "missing_pct": round(col_current.isna().sum() / len(col_current) * 100, 2),
                "unique_count": int(col_current.nunique()),
                "dtype": str(col_current.dtype)
            }
            
            # Add numeric stats if applicable
            if pd.api.types.is_numeric_dtype(col_original):
                original_stats.update({
                    "mean": round(float(col_original.mean()), 4),
                    "std": round(float(col_original.std()), 4),
                    "min": round(float(col_original.min()), 4),
                    "max": round(float(col_original.max()), 4)
                })
                current_stats.update({
                    "mean": round(float(col_current.mean()), 4),
                    "std": round(float(col_current.std()), 4),
                    "min": round(float(col_current.min()), 4),
                    "max": round(float(col_current.max()), 4)
                })
            
            return {
                "column": request.column,
                "original": original_stats,
                "current": current_stats,
                "changes": {
                    "rows_changed": len(df_original) - len(df_current),
                    "missing_change": current_stats["missing_count"] - original_stats["missing_count"],
                    "unique_change": current_stats["unique_count"] - original_stats["unique_count"]
                }
            }
        else:
            # Compare entire dataset
            original_summary = {
                "rows": len(df_original),
                "cols": len(df_original.columns),
                "total_missing": int(df_original.isna().sum().sum()),
                "duplicate_rows": int(df_original.duplicated().sum())
            }
            
            current_summary = {
                "rows": len(df_current),
                "cols": len(df_current.columns),
                "total_missing": int(df_current.isna().sum().sum()),
                "duplicate_rows": int(df_current.duplicated().sum())
            }
            
            # Get cleaning history
            cleaning_history = session_data.get("cleaning_history", [])
            
            return {
                "original": original_summary,
                "current": current_summary,
                "changes": {
                    "rows_removed": original_summary["rows"] - current_summary["rows"],
                    "cols_removed": original_summary["cols"] - current_summary["cols"],
                    "missing_resolved": original_summary["total_missing"] - current_summary["total_missing"],
                    "duplicates_removed": original_summary["duplicate_rows"] - current_summary["duplicate_rows"]
                },
                "operations_applied": len(cleaning_history),
                "operations": cleaning_history
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")
