"""
Module: api/routes/export.py
Description: API endpoints for export operations.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from core.export_manager import ExportManager
from core.report_generator import ReportGenerator
from api.session import session_store

router = APIRouter()


class ExportCleanedRequest(BaseModel):
    """Request for exporting cleaned dataset."""
    filename: str = "dataset_cleaned"
    format_type: str = "csv"  # csv, excel


class ExportMLSplitsRequest(BaseModel):
    """Request for exporting ML splits."""
    prefix: str = "ml_data"
    format_type: str = "csv"
    split_name: Optional[str] = None


class ExportPipelineRequest(BaseModel):
    """Request for exporting pipeline."""
    filename: str = "fitted_pipeline.joblib"


class GenerateReportRequest(BaseModel):
    """Request for generating report."""
    filename: str = "rapport_preparation"
    format_type: str = "html"  # html, markdown


def get_session_data(session_id: str):
    """Get session data or raise 404."""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a dataset first.")
    return session_store[session_id]


@router.post("/cleaned")
async def export_cleaned_dataset(request: ExportCleanedRequest, session_id: str):
    """
    Export the cleaned dataset to CSV or Excel.
    """
    session_data = get_session_data(session_id)
    df = session_data["df"]
    
    try:
        export_manager = ExportManager(output_dir="exports")
        path = export_manager.export_cleaned_dataset(
            df=df,
            filename=request.filename,
            format_type=request.format_type
        )
        
        # Return file for download
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Exported file not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type='application/octet-stream'
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@router.post("/splits")
async def export_ml_splits(request: ExportMLSplitsRequest, session_id: str):
    """
    Export ML train/test splits.
    """
    session_data = get_session_data(session_id)
    ml_results = session_data.get("ml_prep_results")
    
    if ml_results is None:
        raise HTTPException(status_code=404, detail="No ML results found. Please build a pipeline first.")
    
    try:
        # Reconstruct ML results with actual DataFrames
        from core.ml_preprocessor import MLPreprocessor
        df = session_data["df"]
        preprocessor = MLPreprocessor(df)
        
        # Rebuild pipeline to get actual DataFrames
        if ml_results["mode"] == "supervised":
            full_results = preprocessor.build_supervised_pipeline(
                target_col=ml_results["target_col"],
                feature_cols=ml_results["feature_names_in"],
                test_size=ml_results["test_size"],
                split_strategy=ml_results["split_strategy"],
                numeric_scaler=ml_results["numeric_scaler"],
                categorical_encoder=ml_results["categorical_encoder"],
                random_state=ml_results["random_state"]
            )
        else:
            full_results = preprocessor.build_unsupervised_pipeline(
                feature_cols=ml_results["feature_names_in"],
                numeric_scaler=ml_results["numeric_scaler"],
                categorical_encoder=ml_results["categorical_encoder"]
            )
        
        export_manager = ExportManager(output_dir="exports")
        paths = export_manager.export_ml_splits(
            ml_prep_results=full_results,
            prefix=request.prefix,
            format_type=request.format_type
        )
        
        # Handle dict or list returned by export_ml_splits
        import zipfile
        if isinstance(paths, dict):
            if request.split_name and request.split_name in paths:
                file_path = Path(paths[request.split_name])
            elif "excel_splits" in paths:
                file_path = Path(paths["excel_splits"])
            elif len(paths) == 1:
                file_path = Path(list(paths.values())[0])
            else:
                zip_path = Path("exports") / f"{request.prefix}_splits.zip"
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for key, fpath in paths.items():
                        p = Path(fpath)
                        if p.exists():
                            zf.write(p, arcname=p.name)
                file_path = zip_path
        elif isinstance(paths, list):
            file_path = Path(paths[0])
        else:
            file_path = Path(paths)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Exported file not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type='application/octet-stream',
            headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export splits error: {str(e)}")


@router.post("/pipeline")
async def export_pipeline(request: ExportPipelineRequest, session_id: str):
    """
    Export the fitted ML pipeline as joblib file.
    """
    session_data = get_session_data(session_id)
    ml_results = session_data.get("ml_prep_results")
    
    if ml_results is None:
        raise HTTPException(status_code=404, detail="No ML results found. Please build a pipeline first.")
    
    try:
        # Reconstruct ML results with actual pipeline
        from core.ml_preprocessor import MLPreprocessor
        df = session_data["df"]
        preprocessor = MLPreprocessor(df)
        
        if ml_results["mode"] == "supervised":
            full_results = preprocessor.build_supervised_pipeline(
                target_col=ml_results["target_col"],
                feature_cols=ml_results["feature_names_in"],
                test_size=ml_results["test_size"],
                split_strategy=ml_results["split_strategy"],
                numeric_scaler=ml_results["numeric_scaler"],
                categorical_encoder=ml_results["categorical_encoder"],
                random_state=ml_results["random_state"]
            )
        else:
            full_results = preprocessor.build_unsupervised_pipeline(
                feature_cols=ml_results["feature_names_in"],
                numeric_scaler=ml_results["numeric_scaler"],
                categorical_encoder=ml_results["categorical_encoder"]
            )
        
        export_manager = ExportManager(output_dir="exports")
        path = export_manager.export_pipeline_joblib(
            ml_prep_results=full_results,
            filename=request.filename
        )
        
        # Return file for download
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Exported file not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type='application/octet-stream',
            headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export pipeline error: {str(e)}")


@router.post("/inference-script")
async def generate_inference_script(
    pipeline_joblib_name: str = "fitted_pipeline.joblib",
    output_script_name: str = "run_inference.py",
    session_id: str = ""
):
    """
    Generate standalone inference script.
    """
    try:
        export_manager = ExportManager(output_dir="exports")
        path = export_manager.generate_inference_script(
            pipeline_joblib_name=pipeline_joblib_name,
            output_script_name=output_script_name
        )
        
        # Return file for download
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Generated script not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type='text/plain',
            headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generate script error: {str(e)}")


@router.post("/report")
async def generate_report(request: GenerateReportRequest, session_id: str):
    """
    Generate HTML, Markdown, Word, or Excel report with detailed explanations.
    """
    session_data = get_session_data(session_id)
    metadata = session_data["metadata"]
    analysis_results = session_data.get("analysis_results")
    ml_results = session_data.get("ml_prep_results")
    
    if analysis_results is None:
        from core.data_analyzer import DataAnalyzer
        analyzer = DataAnalyzer()
        analysis_results = analyzer.analyze_dataset(session_data["df"])
        session_data["analysis_results"] = analysis_results
    
    try:
        report_generator = ReportGenerator(output_dir="reports")
        
        # Get cleaning history and created features from session normalized as dicts
        raw_history = session_data.get("cleaning_history", [])
        if hasattr(session_data.get("cleaner"), "history"):
            raw_history = session_data["cleaner"].history
        cleaning_history = [op.to_dict() if hasattr(op, "to_dict") else op for op in raw_history]
        created_features = session_data.get("created_features", [])
        
        # Ensure analysis_results has required structure
        if "profiles" not in analysis_results:
            analysis_results["profiles"] = {}
        if "global_issues" not in analysis_results:
            analysis_results["global_issues"] = []
        if "summary" not in analysis_results:
            analysis_results["summary"] = {}
        
        if request.format_type == "html":
            path = report_generator.generate_html_report(
                metadata=metadata,
                analysis_results=analysis_results,
                cleaning_history=cleaning_history,
                created_features=created_features,
                ml_prep_results=ml_results,
                filename=request.filename + ".html"
            )
            media_type = 'text/html'
        elif request.format_type == "word" or request.format_type == "docx":
            path = report_generator.generate_word_report(
                metadata=metadata,
                analysis_results=analysis_results,
                cleaning_history=cleaning_history,
                created_features=created_features,
                ml_prep_results=ml_results,
                filename=request.filename + ".docx"
            )
            media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif request.format_type == "excel" or request.format_type == "xlsx":
            path = report_generator.generate_excel_report(
                metadata=metadata,
                analysis_results=analysis_results,
                cleaning_history=cleaning_history,
                created_features=created_features,
                ml_prep_results=ml_results,
                filename=request.filename + ".xlsx"
            )
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            path = report_generator.generate_markdown_report(
                metadata=metadata,
                analysis_results=analysis_results,
                cleaning_history=cleaning_history,
                created_features=created_features,
                ml_prep_results=ml_results,
                filename=request.filename + ".md"
            )
            media_type = 'text/markdown'
        
        # Return file for download
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Generated report not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
        )
    
    except Exception as e:
        import traceback
        error_detail = f"Report generation error: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)
