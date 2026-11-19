"""
Module: core/data_loader.py
Description: Robust dataset loading with format auto-detection, CSV parameter sniffing,
             and metadata extraction.
"""

import os
import csv
import json
import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd


SUPPORTED_EXTENSIONS = {
    ".csv": "CSV",
    ".tsv": "TSV",
    ".txt": "Texte délimité",
    ".xlsx": "Excel (XLSX)",
    ".xls": "Excel (XLS)",
    ".json": "JSON",
    ".parquet": "Apache Parquet"
}

ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
DELIMITERS_TO_TRY = [",", ";", "\t", "|"]


def detect_csv_parameters(file_path: str, sample_bytes: int = 65536) -> Dict[str, str]:
    """
    Detects the encoding, delimiter, and decimal separator of a CSV/text file.
    
    Args:
        file_path: Path to the target file.
        sample_bytes: Number of bytes to sample for sniffing.
        
    Returns:
        Dictionary with detected 'encoding', 'delimiter', and 'decimal'.
    """
    detected_encoding = "utf-8"
    raw_sample = b""
    
    # 1. Detect Encoding
    for enc in ENCODINGS_TO_TRY:
        try:
            with open(file_path, "rb") as f:
                raw_sample = f.read(sample_bytes)
            raw_sample.decode(enc)
            detected_encoding = enc
            break
        except (UnicodeDecodeError, Exception):
            continue

    text_sample = raw_sample.decode(detected_encoding, errors="replace")
    
    # 2. Detect Delimiter using csv.Sniffer with fallback
    detected_delimiter = ","
    try:
        sample_lines = "\n".join([line for line in text_sample.splitlines()[:25] if line.strip()])
        if sample_lines:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample_lines, delimiters=";,|\t,")
            detected_delimiter = dialect.delimiter
    except Exception:
        # Fallback: Count frequency of candidate delimiters in the first non-empty lines
        lines = [line for line in text_sample.splitlines()[:10] if line.strip()]
        if lines:
            counts = {d: sum(line.count(d) for line in lines) for d in DELIMITERS_TO_TRY}
            best_delim = max(counts, key=counts.get)
            if counts[best_delim] > 0:
                detected_delimiter = best_delim

    # 3. Detect Decimal separator (e.g. French CSVs often use ';' delimiter with ',' decimal)
    detected_decimal = "."
    if detected_delimiter in [";", "\t", "|"]:
        comma_num_matches = 0
        point_num_matches = 0
        tokens = re.split(r'[\r\n' + re.escape(detected_delimiter) + r']', text_sample)
        for token in tokens:
            clean = token.strip(" \t\n\r\"'")
            if not clean or clean.startswith(",") or clean.endswith(",") or clean.startswith(".") or clean.endswith("."):
                continue
            if "," in clean and clean.replace(",", "", 1).replace("-", "", 1).isdigit():
                comma_num_matches += 1
            elif "." in clean and clean.replace(".", "", 1).replace("-", "", 1).isdigit():
                point_num_matches += 1
        if comma_num_matches > point_num_matches:
            detected_decimal = ","

    return {
        "encoding": detected_encoding,
        "delimiter": detected_delimiter,
        "decimal": detected_decimal
    }


def format_bytes(size: int) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    for unit in ['o', 'Ko', 'Mo', 'Go']:
        if abs(size) < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} To"


def load_dataset(
    file_path: str,
    encoding: Optional[str] = None,
    delimiter: Optional[str] = None,
    decimal: Optional[str] = None,
    sheet_name: Optional[Any] = 0,
    header: Optional[int] = 0,
    **kwargs
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Loads a dataset from CSV, TSV, Excel, JSON, or Parquet file.
    
    Args:
        file_path: Path to dataset.
        encoding: File encoding (auto-detected if None for CSV).
        delimiter: CSV separator (auto-detected if None for CSV).
        decimal: Decimal point character (auto-detected if None for CSV).
        sheet_name: Sheet name or index for Excel files.
        header: Row number to use as column names.
        kwargs: Additional arguments passed to pandas readers.
        
    Returns:
        A tuple of (DataFrame, metadata_dict).
        
    Raises:
        FileNotFoundError: If the file path does not exist.
        ValueError: If file format is unsupported or parsing fails.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Format de fichier non pris en charge : {ext}. "
            f"Formats acceptés : {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    file_size = path.stat().st_size
    detected_params = {}

    if ext in [".csv", ".tsv", ".txt"]:
        detected_params = detect_csv_parameters(str(path))
        enc = encoding or detected_params["encoding"]
        sep = delimiter or (detected_params["delimiter"] if ext == ".csv" else ("\t" if ext == ".tsv" else detected_params["delimiter"]))
        dec = decimal or detected_params["decimal"]

        try:
            df = pd.read_csv(
                path,
                sep=sep,
                encoding=enc,
                decimal=dec,
                header=header,
                on_bad_lines="warn",
                low_memory=False,
                **kwargs
            )
        except Exception as e:
            try:
                df = pd.read_csv(
                    path,
                    sep=sep,
                    encoding="latin-1",
                    decimal=dec,
                    header=header,
                    engine="python",
                    **kwargs
                )
                enc = "latin-1"
            except Exception as e2:
                raise ValueError(f"Impossible de lire le fichier CSV : {e}. Tentative de secours échouée : {e2}")

        effective_encoding = enc
        effective_delimiter = sep
        effective_decimal = dec

    elif ext in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(path, sheet_name=sheet_name, header=header, **kwargs)
        except ImportError:
            raise ValueError("Le package 'openpyxl' (pour .xlsx) ou 'xlrd' (pour .xls) est requis.")
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier Excel : {e}")
        effective_encoding = "N/A (Binaire)"
        effective_delimiter = "N/A"
        effective_decimal = "."

    elif ext == ".json":
        try:
            df = pd.read_json(path, **kwargs)
        except Exception:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    df = pd.json_normalize(data)
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                            df = pd.json_normalize(v)
                            break
                    else:
                        df = pd.DataFrame([data])
                else:
                    raise ValueError("Structure JSON non tabulaire.")
            except Exception as e2:
                raise ValueError(f"Erreur lors de la lecture du fichier JSON : {e2}")
        effective_encoding = "utf-8"
        effective_delimiter = "N/A"
        effective_decimal = "."

    elif ext == ".parquet":
        try:
            df = pd.read_parquet(path, **kwargs)
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier Parquet : {e}")
        effective_encoding = "N/A"
        effective_delimiter = "N/A"
        effective_decimal = "."

    else:
        raise ValueError(f"Format non supporté : {ext}")

    df.columns = [str(col) for col in df.columns]

    memory_bytes = int(df.memory_usage(deep=True).sum()) if not df.empty else 0
    total_missing = int(df.isna().sum().sum())
    total_cells = df.size if df.size > 0 else 1
    missing_pct = round((total_missing / total_cells) * 100, 2)
    duplicate_rows = int(df.duplicated().sum())

    metadata = {
        "file_name": path.name,
        "file_path": str(path.resolve()),
        "file_size_bytes": file_size,
        "file_size_formatted": format_bytes(file_size),
        "format": SUPPORTED_EXTENSIONS.get(ext, ext.upper()),
        "extension": ext,
        "encoding": effective_encoding,
        "delimiter": effective_delimiter,
        "decimal": effective_decimal,
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "memory_bytes": memory_bytes,
        "memory_formatted": format_bytes(memory_bytes),
        "total_missing": total_missing,
        "missing_pct": missing_pct,
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": round((duplicate_rows / len(df) * 100), 2) if len(df) > 0 else 0.0
    }

    return df, metadata


def get_preview(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Returns the first n rows as preview."""
    return df.head(n).copy()