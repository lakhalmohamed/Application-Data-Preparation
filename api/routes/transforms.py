"""
Module: api/routes/transforms.py
Description: API endpoints for feature engineering and transformations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from api.session import session_store
from core.data_cleaner import CleaningOperation

router = APIRouter()


class DateTimeExtractionRequest(BaseModel):
    """Request for datetime feature extraction."""
    column: str
    extract_year: bool = True
    extract_month: bool = True
    extract_day: bool = True
    extract_dayofweek: bool = True
    extract_hour: bool = False
    extract_is_weekend: bool = True
    extract_quarter: bool = True
    reference_date: Optional[str] = None


class NumericInteractionRequest(BaseModel):
    """Request for numeric interaction features."""
    col_a: str
    col_b: str
    operation: str  # ratio, multiply, sum, diff
    output_name: Optional[str] = None


class BinningRequest(BaseModel):
    """Request for binning/discretization."""
    column: str
    n_bins: int = 5
    strategy: str = "quantile"  # quantile, uniform
    output_name: Optional[str] = None


class TextFeaturesRequest(BaseModel):
    """Request for text feature extraction."""
    column: str
    extract_char_length: bool = True
    extract_word_count: bool = True
    vectorize_method: Optional[str] = None  # tfidf, bow, None
    max_features: int = 50


def get_session_data(session_id: str):
    """Get session data or raise 404."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a dataset first.")
    return session_store[session_id]


def sync_session_after_transform(
    session_data: dict,
    df,
    transformer,
    op_type: str,
    col: str,
    strategy: str,
    details: str,
    params: dict
):
    """Synchronize DataFrame, metadata, created_features, and cleaning history."""
    session_data["df"] = df
    
    if "created_features" not in session_data or not isinstance(session_data["created_features"], list):
        session_data["created_features"] = []
    if hasattr(transformer, "created_features") and transformer.created_features:
        session_data["created_features"].extend(transformer.created_features)
    
    if "metadata" in session_data and isinstance(session_data["metadata"], dict):
        session_data["metadata"]["columns"] = list(df.columns)
        session_data["metadata"]["total_columns"] = len(df.columns)
        session_data["metadata"]["total_rows"] = len(df)
        
    cleaner = session_data.get("cleaner")
    if cleaner is not None:
        cleaner.df = df
        op = CleaningOperation(
            op_type=op_type,
            column=col,
            strategy=strategy,
            details=details,
            params=params
        )
        cleaner._save_state(op)
        session_data["cleaning_history"] = cleaner.history


@router.post("/datetime")
async def extract_datetime_features(request: DateTimeExtractionRequest, session_id: str):
    """
    Extract temporal features from a datetime column.
    """
    session_data = get_session_data(session_id)
    from core.feature_transformer import FeatureTransformer
    transformer = FeatureTransformer(session_data["df"])
    
    try:
        df, new_cols = transformer.extract_datetime_features(
            column=request.column,
            extract_year=request.extract_year,
            extract_month=request.extract_month,
            extract_day=request.extract_day,
            extract_dayofweek=request.extract_dayofweek,
            extract_hour=request.extract_hour,
            extract_is_weekend=request.extract_is_weekend,
            extract_quarter=request.extract_quarter,
            reference_date=request.reference_date
        )
        
        sync_session_after_transform(
            session_data=session_data,
            df=df,
            transformer=transformer,
            op_type="Ingénierie Temporelle",
            col=request.column,
            strategy="Décomposition temporelle",
            details=f"Création de {len(new_cols)} variables temporelles : {', '.join(new_cols)}",
            params={"created_columns": new_cols}
        )
        
        return {
            "message": f"{len(new_cols)} caractéristiques temporelles extraites de '{request.column}'",
            "new_columns": new_cols,
            "columns": list(df.columns)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'extraction temporelle : {str(e)}")


@router.post("/numeric-interaction")
async def create_numeric_interaction(request: NumericInteractionRequest, session_id: str):
    """
    Create interaction features between two numeric columns.
    """
    session_data = get_session_data(session_id)
    from core.feature_transformer import FeatureTransformer
    transformer = FeatureTransformer(session_data["df"])
    
    try:
        df, new_col = transformer.create_numeric_interaction(
            col_a=request.col_a,
            col_b=request.col_b,
            operation=request.operation,
            output_name=request.output_name
        )
        
        sync_session_after_transform(
            session_data=session_data,
            df=df,
            transformer=transformer,
            op_type="Interaction Numérique",
            col=f"{request.col_a} & {request.col_b}",
            strategy=request.operation,
            details=f"Nouvelle variable créée : '{new_col}'",
            params={"output_column": new_col, "operation": request.operation}
        )
        
        return {
            "message": f"Caractéristique d'interaction '{new_col}' créée",
            "new_column": new_col,
            "columns": list(df.columns)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur interaction numérique : {str(e)}")


@router.post("/binning")
async def bin_numeric_column(request: BinningRequest, session_id: str):
    """
    Discretize a continuous numeric column into bins.
    """
    session_data = get_session_data(session_id)
    from core.feature_transformer import FeatureTransformer
    transformer = FeatureTransformer(session_data["df"])
    
    try:
        df, new_col = transformer.bin_numeric_column(
            column=request.column,
            n_bins=request.n_bins,
            strategy=request.strategy,
            output_name=request.output_name
        )
        
        sync_session_after_transform(
            session_data=session_data,
            df=df,
            transformer=transformer,
            op_type="Discrétisation (Binning)",
            col=request.column,
            strategy=f"{request.strategy} ({request.n_bins} classes)",
            details=f"Variable discrétisée créée : '{new_col}'",
            params={"output_column": new_col, "n_bins": request.n_bins}
        )
        
        return {
            "message": f"Colonne '{request.column}' discrétisée en {request.n_bins} tranches dans '{new_col}'",
            "new_column": new_col,
            "columns": list(df.columns)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur binning : {str(e)}")


@router.post("/text-features")
async def extract_text_features(request: TextFeaturesRequest, session_id: str):
    """
    Extract features from a text column.
    """
    session_data = get_session_data(session_id)
    from core.feature_transformer import FeatureTransformer
    transformer = FeatureTransformer(session_data["df"])
    
    try:
        df, new_cols = transformer.extract_text_features(
            column=request.column,
            extract_char_length=request.extract_char_length,
            extract_word_count=request.extract_word_count,
            vectorize_method=request.vectorize_method,
            max_features=request.max_features
        )
        
        sync_session_after_transform(
            session_data=session_data,
            df=df,
            transformer=transformer,
            op_type="Ingénierie Textuelle",
            col=request.column,
            strategy="Statistiques textuelles",
            details=f"Création de {len(new_cols)} caractéristiques textuelles : {', '.join(new_cols)}",
            params={"created_columns": new_cols}
        )
        
        return {
            "message": f"{len(new_cols)} caractéristiques textuelles extraites de '{request.column}'",
            "new_columns": new_cols,
            "columns": list(df.columns)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur extraction texte : {str(e)}")


@router.get("/log")
async def get_features_log(session_id: str):
    """
    Get the log of created features.
    """
    session_data = get_session_data(session_id)
    log = session_data.get("created_features", [])
    return {"features_log": log}
