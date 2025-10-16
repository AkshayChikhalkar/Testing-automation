"""
Celery tasks for report generation
"""

from typing import Dict, Any, Optional
import structlog
from datetime import datetime
import os

from app.core.celery import celery_app

logger = structlog.get_logger()


@celery_app.task(name="generate_test_report")
def generate_test_report_task(
    test_run_id: int,
    report_format: str = "pdf",
    template: Optional[str] = None
):
    """
    Generate a test report for a completed test run
    
    Args:
        test_run_id: ID of the test run
        report_format: Report format (pdf, html, excel)
        template: Optional custom template
    """
    try:
        logger.info("Starting test report generation", test_run_id=test_run_id, format=report_format)
        
        # Get test run data (this would typically come from database)
        test_run_data = _get_test_run_data(test_run_id)
        
        if not test_run_data:
            raise ValueError(f"Test run {test_run_id} not found")
        
        # Generate report based on format
        if report_format == "pdf":
            report_path = _generate_pdf_report(test_run_data, template)
        elif report_format == "html":
            report_path = _generate_html_report(test_run_data, template)
        elif report_format == "excel":
            report_path = _generate_excel_report(test_run_data, template)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")
        
        logger.info("Test report generation completed", test_run_id=test_run_id)
        
        return {
            "status": "success",
            "test_run_id": test_run_id,
            "report_format": report_format,
            "report_path": report_path,
            "file_size": os.path.getsize(report_path) if os.path.exists(report_path) else 0
        }
        
    except Exception as e:
        logger.error("Test report generation failed", test_run_id=test_run_id, error=str(e))
        return {
            "status": "error",
            "test_run_id": test_run_id,
            "error": str(e)
        }


@celery_app.task(name="generate_batch_report")
def generate_batch_report_task(
    test_run_ids: list,
    report_format: str = "pdf",
    template: Optional[str] = None
):
    """
    Generate a batch report for multiple test runs
    
    Args:
        test_run_ids: List of test run IDs
        report_format: Report format
        template: Optional custom template
    """
    try:
        logger.info("Starting batch report generation", count=len(test_run_ids), format=report_format)
        
        # Get all test run data
        test_runs_data = []
        for test_run_id in test_run_ids:
            data = _get_test_run_data(test_run_id)
            if data:
                test_runs_data.append(data)
        
        if not test_runs_data:
            raise ValueError("No valid test runs found")
        
        # Generate batch report
        if report_format == "pdf":
            report_path = _generate_batch_pdf_report(test_runs_data, template)
        elif report_format == "html":
            report_path = _generate_batch_html_report(test_runs_data, template)
        elif report_format == "excel":
            report_path = _generate_batch_excel_report(test_runs_data, template)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")
        
        logger.info("Batch report generation completed", count=len(test_runs_data))
        
        return {
            "status": "success",
            "test_run_ids": test_run_ids,
            "report_format": report_format,
            "report_path": report_path,
            "file_size": os.path.getsize(report_path) if os.path.exists(report_path) else 0
        }
        
    except Exception as e:
        logger.error("Batch report generation failed", error=str(e))
        return {
            "status": "error",
            "test_run_ids": test_run_ids,
            "error": str(e)
        }


@celery_app.task(name="generate_analytics_report")
def generate_analytics_report_task(
    start_date: str,
    end_date: str,
    report_format: str = "pdf",
    metrics: Optional[list] = None
):
    """
    Generate an analytics report for a date range
    
    Args:
        start_date: Start date for analytics
        end_date: End date for analytics
        report_format: Report format
        metrics: List of metrics to include
    """
    try:
        logger.info("Starting analytics report generation", start_date=start_date, end_date=end_date)
        
        # Get analytics data
        analytics_data = _get_analytics_data(start_date, end_date, metrics)
        
        # Generate analytics report
        if report_format == "pdf":
            report_path = _generate_analytics_pdf_report(analytics_data, start_date, end_date)
        elif report_format == "html":
            report_path = _generate_analytics_html_report(analytics_data, start_date, end_date)
        elif report_format == "excel":
            report_path = _generate_analytics_excel_report(analytics_data, start_date, end_date)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")
        
        logger.info("Analytics report generation completed")
        
        return {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "report_format": report_format,
            "report_path": report_path,
            "file_size": os.path.getsize(report_path) if os.path.exists(report_path) else 0
        }
        
    except Exception as e:
        logger.error("Analytics report generation failed", error=str(e))
        return {
            "status": "error",
            "start_date": start_date,
            "end_date": end_date,
            "error": str(e)
        }


def _get_test_run_data(test_run_id: int) -> Optional[Dict[str, Any]]:
    """Get test run data from database"""
    # This would typically query the database
    # For now, return mock data
    return {
        "id": test_run_id,
        "name": f"Test Run {test_run_id}",
        "model_name": "Sample Model",
        "status": "completed",
        "execution_time": 120.5,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "input_data": {"param1": 10, "param2": 20},
        "output_data": {"result1": 30, "result2": 40},
        "results": {"success": True, "performance": "good"}
    }


def _generate_pdf_report(test_run_data: Dict[str, Any], template: Optional[str]) -> str:
    """Generate PDF report"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        # Create PDF file
        report_path = f"./reports/test_run_{test_run_data['id']}_report.pdf"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        doc = SimpleDocTemplate(report_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title = Paragraph(f"Test Report - {test_run_data['name']}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add test run details
        details = f"""
        <b>Test Run ID:</b> {test_run_data['id']}<br/>
        <b>Model:</b> {test_run_data['model_name']}<br/>
        <b>Status:</b> {test_run_data['status']}<br/>
        <b>Execution Time:</b> {test_run_data['execution_time']} seconds<br/>
        <b>Start Time:</b> {test_run_data['start_time']}<br/>
        <b>End Time:</b> {test_run_data['end_time']}<br/>
        """
        story.append(Paragraph(details, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Add results
        results = f"""
        <b>Results:</b><br/>
        {test_run_data.get('results', {})}
        """
        story.append(Paragraph(results, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return report_path
        
    except ImportError:
        logger.warning("reportlab not available, creating simple text report")
        return _generate_text_report(test_run_data)


def _generate_html_report(test_run_data: Dict[str, Any], template: Optional[str]) -> str:
    """Generate HTML report"""
    report_path = f"./reports/test_run_{test_run_data['id']}_report.html"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Report - {test_run_data['name']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            .details {{ background-color: #f5f5f5; padding: 20px; margin: 20px 0; }}
            .results {{ background-color: #e8f5e8; padding: 20px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>Test Report - {test_run_data['name']}</h1>
        
        <div class="details">
            <h2>Test Details</h2>
            <p><strong>Test Run ID:</strong> {test_run_data['id']}</p>
            <p><strong>Model:</strong> {test_run_data['model_name']}</p>
            <p><strong>Status:</strong> {test_run_data['status']}</p>
            <p><strong>Execution Time:</strong> {test_run_data['execution_time']} seconds</p>
            <p><strong>Start Time:</strong> {test_run_data['start_time']}</p>
            <p><strong>End Time:</strong> {test_run_data['end_time']}</p>
        </div>
        
        <div class="results">
            <h2>Results</h2>
            <pre>{test_run_data.get('results', {})}</pre>
        </div>
    </body>
    </html>
    """
    
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    return report_path


def _generate_excel_report(test_run_data: Dict[str, Any], template: Optional[str]) -> str:
    """Generate Excel report"""
    try:
        import pandas as pd
        
        report_path = f"./reports/test_run_{test_run_data['id']}_report.xlsx"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Field': ['Test Run ID', 'Name', 'Model', 'Status', 'Execution Time', 'Start Time', 'End Time'],
                'Value': [
                    test_run_data['id'],
                    test_run_data['name'],
                    test_run_data['model_name'],
                    test_run_data['status'],
                    test_run_data['execution_time'],
                    test_run_data['start_time'],
                    test_run_data['end_time']
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Input data sheet
            if test_run_data.get('input_data'):
                input_df = pd.DataFrame([test_run_data['input_data']])
                input_df.to_excel(writer, sheet_name='Input Data', index=False)
            
            # Output data sheet
            if test_run_data.get('output_data'):
                output_df = pd.DataFrame([test_run_data['output_data']])
                output_df.to_excel(writer, sheet_name='Output Data', index=False)
        
        return report_path
        
    except ImportError:
        logger.warning("pandas/openpyxl not available, creating CSV report")
        return _generate_csv_report(test_run_data)


def _generate_text_report(test_run_data: Dict[str, Any]) -> str:
    """Generate simple text report"""
    report_path = f"./reports/test_run_{test_run_data['id']}_report.txt"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    content = f"""
Test Report - {test_run_data['name']}
{'=' * 50}

Test Run ID: {test_run_data['id']}
Model: {test_run_data['model_name']}
Status: {test_run_data['status']}
Execution Time: {test_run_data['execution_time']} seconds
Start Time: {test_run_data['start_time']}
End Time: {test_run_data['end_time']}

Results:
{test_run_data.get('results', {})}
"""
    
    with open(report_path, 'w') as f:
        f.write(content)
    
    return report_path


def _generate_csv_report(test_run_data: Dict[str, Any]) -> str:
    """Generate CSV report"""
    report_path = f"./reports/test_run_{test_run_data['id']}_report.csv"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    import csv
    
    with open(report_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Field', 'Value'])
        writer.writerow(['Test Run ID', test_run_data['id']])
        writer.writerow(['Name', test_run_data['name']])
        writer.writerow(['Model', test_run_data['model_name']])
        writer.writerow(['Status', test_run_data['status']])
        writer.writerow(['Execution Time', test_run_data['execution_time']])
        writer.writerow(['Start Time', test_run_data['start_time']])
        writer.writerow(['End Time', test_run_data['end_time']])
    
    return report_path


def _get_analytics_data(start_date: str, end_date: str, metrics: Optional[list]) -> Dict[str, Any]:
    """Get analytics data for date range"""
    # This would typically query the database for analytics
    return {
        "date_range": {"start": start_date, "end": end_date},
        "total_tests": 150,
        "successful_tests": 140,
        "failed_tests": 10,
        "average_execution_time": 120.5,
        "models_tested": 25,
        "metrics": metrics or ["execution_time", "success_rate", "model_performance"]
    }


def _generate_batch_pdf_report(test_runs_data: list, template: Optional[str]) -> str:
    """Generate batch PDF report"""
    # Implementation for batch PDF report
    return "./reports/batch_report.pdf"


def _generate_batch_html_report(test_runs_data: list, template: Optional[str]) -> str:
    """Generate batch HTML report"""
    # Implementation for batch HTML report
    return "./reports/batch_report.html"


def _generate_batch_excel_report(test_runs_data: list, template: Optional[str]) -> str:
    """Generate batch Excel report"""
    # Implementation for batch Excel report
    return "./reports/batch_report.xlsx"


def _generate_analytics_pdf_report(analytics_data: Dict[str, Any], start_date: str, end_date: str) -> str:
    """Generate analytics PDF report"""
    # Implementation for analytics PDF report
    return "./reports/analytics_report.pdf"


def _generate_analytics_html_report(analytics_data: Dict[str, Any], start_date: str, end_date: str) -> str:
    """Generate analytics HTML report"""
    # Implementation for analytics HTML report
    return "./reports/analytics_report.html"


def _generate_analytics_excel_report(analytics_data: Dict[str, Any], start_date: str, end_date: str) -> str:
    """Generate analytics Excel report"""
    # Implementation for analytics Excel report
    return "./reports/analytics_report.xlsx"
