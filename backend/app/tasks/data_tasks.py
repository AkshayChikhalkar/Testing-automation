"""
Celery tasks for data processing
"""

from typing import Dict, Any, List
from celery import current_task
import pandas as pd
import numpy as np
import structlog

from app.core.celery import celery_app

logger = structlog.get_logger()


@celery_app.task(name="process_test_data")
def process_test_data_task(
    test_run_id: int,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any]
):
    """
    Process and analyze test data
    
    Args:
        test_run_id: ID of the test run
        input_data: Input data from the test
        output_data: Output data from the test
    """
    try:
        logger.info("Starting data processing", test_run_id=test_run_id)
        
        # Process input data
        processed_input = _process_data_dict(input_data, "input")
        
        # Process output data
        processed_output = _process_data_dict(output_data, "output")
        
        # Calculate statistics
        statistics = _calculate_statistics(processed_input, processed_output)
        
        # Generate analysis results
        analysis_results = {
            "test_run_id": test_run_id,
            "processed_input": processed_input,
            "processed_output": processed_output,
            "statistics": statistics,
            "data_quality": _assess_data_quality(processed_output)
        }
        
        logger.info("Data processing completed", test_run_id=test_run_id)
        
        return {
            "status": "success",
            "test_run_id": test_run_id,
            "analysis_results": analysis_results
        }
        
    except Exception as e:
        logger.error("Data processing failed", test_run_id=test_run_id, error=str(e))
        return {
            "status": "error",
            "test_run_id": test_run_id,
            "error": str(e)
        }


@celery_app.task(name="export_test_data")
def export_test_data_task(
    test_run_id: int,
    data: Dict[str, Any],
    export_format: str = "csv",
    file_path: str = None
):
    """
    Export test data to various formats
    
    Args:
        test_run_id: ID of the test run
        data: Data to export
        export_format: Export format (csv, excel, json)
        file_path: Output file path
    """
    try:
        logger.info("Starting data export", test_run_id=test_run_id, format=export_format)
        
        if export_format == "csv":
            result = _export_to_csv(data, file_path)
        elif export_format == "excel":
            result = _export_to_excel(data, file_path)
        elif export_format == "json":
            result = _export_to_json(data, file_path)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        logger.info("Data export completed", test_run_id=test_run_id)
        
        return {
            "status": "success",
            "test_run_id": test_run_id,
            "export_format": export_format,
            "file_path": result["file_path"],
            "file_size": result["file_size"]
        }
        
    except Exception as e:
        logger.error("Data export failed", test_run_id=test_run_id, error=str(e))
        return {
            "status": "error",
            "test_run_id": test_run_id,
            "error": str(e)
        }


@celery_app.task(name="import_data_file")
def import_data_file_task(
    file_path: str,
    file_type: str,
    metadata: Dict[str, Any] = None
):
    """
    Import data from various file formats
    
    Args:
        file_path: Path to the data file
        file_type: Type of file (csv, excel, mat, json)
        metadata: Additional metadata
    """
    try:
        logger.info("Starting data import", file_path=file_path, file_type=file_type)
        
        if file_type == "csv":
            data = _import_from_csv(file_path)
        elif file_type == "excel":
            data = _import_from_excel(file_path)
        elif file_type == "mat":
            data = _import_from_mat(file_path)
        elif file_type == "json":
            data = _import_from_json(file_path)
        else:
            raise ValueError(f"Unsupported import format: {file_type}")
        
        # Process imported data
        processed_data = _process_imported_data(data, metadata)
        
        logger.info("Data import completed", file_path=file_path)
        
        return {
            "status": "success",
            "file_path": file_path,
            "file_type": file_type,
            "data": processed_data,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error("Data import failed", file_path=file_path, error=str(e))
        return {
            "status": "error",
            "file_path": file_path,
            "error": str(e)
        }


def _process_data_dict(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """Process a dictionary of data"""
    processed = {}
    
    for key, value in data.items():
        if isinstance(value, (list, tuple)):
            # Convert to numpy array for analysis
            arr = np.array(value)
            processed[key] = {
                "values": arr.tolist(),
                "type": "array",
                "shape": arr.shape,
                "dtype": str(arr.dtype),
                "statistics": {
                    "mean": float(np.mean(arr)) if arr.size > 0 else None,
                    "std": float(np.std(arr)) if arr.size > 0 else None,
                    "min": float(np.min(arr)) if arr.size > 0 else None,
                    "max": float(np.max(arr)) if arr.size > 0 else None
                }
            }
        elif isinstance(value, (int, float)):
            processed[key] = {
                "value": value,
                "type": "scalar"
            }
        else:
            processed[key] = {
                "value": value,
                "type": "other"
            }
    
    return processed


def _calculate_statistics(input_data: Dict[str, Any], output_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate statistics from input and output data"""
    statistics = {
        "input_variables": len(input_data),
        "output_variables": len(output_data),
        "data_quality_metrics": {}
    }
    
    # Calculate data quality metrics
    for data_type, data in [("input", input_data), ("output", output_data)]:
        for key, value in data.items():
            if value.get("type") == "array":
                stats = value.get("statistics", {})
                statistics["data_quality_metrics"][f"{data_type}_{key}"] = {
                    "mean": stats.get("mean"),
                    "std": stats.get("std"),
                    "range": stats.get("max", 0) - stats.get("min", 0) if stats.get("max") is not None else None
                }
    
    return statistics


def _assess_data_quality(output_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the quality of output data"""
    quality_metrics = {
        "completeness": 0.0,
        "consistency": 0.0,
        "validity": 0.0
    }
    
    total_variables = len(output_data)
    if total_variables == 0:
        return quality_metrics
    
    # Check completeness (non-null values)
    complete_variables = sum(1 for v in output_data.values() if v.get("value") is not None)
    quality_metrics["completeness"] = complete_variables / total_variables
    
    # Check consistency (data types)
    consistent_variables = sum(1 for v in output_data.values() if v.get("type") in ["scalar", "array"])
    quality_metrics["consistency"] = consistent_variables / total_variables
    
    # Check validity (reasonable values)
    valid_variables = 0
    for v in output_data.values():
        if v.get("type") == "scalar":
            val = v.get("value")
            if isinstance(val, (int, float)) and not (np.isnan(val) if isinstance(val, float) else False):
                valid_variables += 1
        elif v.get("type") == "array":
            stats = v.get("statistics", {})
            if stats.get("mean") is not None and not np.isnan(stats["mean"]):
                valid_variables += 1
    
    quality_metrics["validity"] = valid_variables / total_variables
    
    return quality_metrics


def _export_to_csv(data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Export data to CSV format"""
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    
    return {
        "file_path": file_path,
        "file_size": len(df.to_csv().encode('utf-8'))
    }


def _export_to_excel(data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Export data to Excel format"""
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    
    return {
        "file_path": file_path,
        "file_size": len(df.to_excel().encode('utf-8'))
    }


def _export_to_json(data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Export data to JSON format"""
    import json
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return {
        "file_path": file_path,
        "file_size": len(json.dumps(data).encode('utf-8'))
    }


def _import_from_csv(file_path: str) -> Dict[str, Any]:
    """Import data from CSV file"""
    df = pd.read_csv(file_path)
    return df.to_dict('list')


def _import_from_excel(file_path: str) -> Dict[str, Any]:
    """Import data from Excel file"""
    df = pd.read_excel(file_path)
    return df.to_dict('list')


def _import_from_mat(file_path: str) -> Dict[str, Any]:
    """Import data from MATLAB .mat file"""
    from scipy.io import loadmat
    mat_data = loadmat(file_path)
    
    # Convert MATLAB data to Python format
    data = {}
    for key, value in mat_data.items():
        if not key.startswith('__'):  # Skip metadata
            data[key] = value.tolist() if hasattr(value, 'tolist') else value
    
    return data


def _import_from_json(file_path: str) -> Dict[str, Any]:
    """Import data from JSON file"""
    import json
    
    with open(file_path, 'r') as f:
        return json.load(f)


def _process_imported_data(data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Process imported data"""
    processed = {
        "data": data,
        "metadata": metadata or {},
        "import_timestamp": pd.Timestamp.now().isoformat(),
        "data_summary": {
            "variables": len(data),
            "total_values": sum(len(v) if isinstance(v, list) else 1 for v in data.values())
        }
    }
    
    return processed
