"""
Maduk Business Intelligence - AI Recommendation Pipeline Route
File: backend/routes/ai_recommendation_pipeline_route.py

Production-ready FastAPI endpoint routing binary business dataset uploads 
from Streamlit frontend views to the BusinessIntelligencePipeline orchestrator.
"""

import os
import shutil
import base64
import tempfile
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse

# Import the core BusinessIntelligencePipeline orchestrator
from backend.services.ai_recommendation_pipeline.pipeline import BusinessIntelligencePipeline

logger = logging.getLogger("MadukBI.AIRecommendationRoute")

router = APIRouter(
    prefix="/api/v1/recommendations",
    tags=["AI Business Recommendations"]
)


def execute_bi_pipeline(
    data_file_path: str,
    company_name: str,
    work_dir: str
) -> Dict[str, Any]:
    """
    Instantiates the BusinessIntelligencePipeline orchestrator and executes
    the end-to-end 12-stage analysis within a clean working directory workspace.
    """
    orchestrator = BusinessIntelligencePipeline(base_dir=work_dir)
    pdf_filename = f"{company_name.lower().replace(' ', '_')}_executive_report.pdf"
    
    result = orchestrator.run(
        input_data=data_file_path,
        output_pdf_filename=pdf_filename,
        company_name=company_name
    )

    if not isinstance(result, dict):
        raise ValueError("Pipeline execution failed to return a valid dictionary payload.")

    return result


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_business_dataset(
    file: UploadFile = File(...),
    company_name: Optional[str] = Form("Enterprise Client"),
    industry: Optional[str] = Form("General Business")
) -> JSONResponse:
    """
    Receives uploaded business datasets (.csv, .xlsx, .xls), executes the 12-stage pipeline 
    orchestration engine, cleans up temporary assets, and returns structured analytical results 
    along with Base64-encoded PDF report bytes.

    Args:
        file: Binary uploaded tabular dataset file stream.
        company_name: Name of the enterprise client for report branding.
        industry: Sector taxonomy context.

    Returns:
        JSONResponse payload with status, health score, dashboard metrics, 
        insights, recommendations, and Base64 encoded PDF report data.
    """
    # 1. Validate File Extension Format
    allowed_extensions = ('.csv', '.xlsx', '.xls')
    filename = file.filename or "uploaded_dataset.csv"

    if not filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Please upload a dataset with extensions: {', '.join(allowed_extensions)}"
        )

    # 2. Prepare Isolated Temporary Execution Workspace
    temp_dir = tempfile.mkdtemp(prefix="maduk_bi_run_")
    uploaded_file_path = os.path.join(temp_dir, filename)

    try:
        # Save streamed upload to local temp path
        with open(uploaded_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Received dataset upload '{filename}' for company '{company_name}'. Executing pipeline...")

        # 3. Run Pipeline Orchestration Engine
        pipeline_output: Dict[str, Any] = execute_bi_pipeline(
            data_file_path=uploaded_file_path,
            company_name=company_name,
            work_dir=temp_dir
        )

        # 4. Encode Output PDF to Base64 String for Transport
        pdf_path = pipeline_output.get("pdf_report_path")
        pdf_base64_str = ""

        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                pdf_base64_str = base64.b64encode(pdf_bytes).decode("utf-8")

        # Extract health values safely regardless of dict/object structure
        health_data = pipeline_output.get("health_assessment") or pipeline_output.get("health") or {}
        health_score = health_data.get("health_score") if isinstance(health_data, dict) else getattr(health_data, "health_score", 0.0)
        health_status = health_data.get("status") if isinstance(health_data, dict) else getattr(health_data, "status", "Healthy")

        # 5. Construct Structured Response Payload
        response_payload = {
            "status": "success",
            "company_name": company_name,
            "industry": industry,
            "data_quality_score": pipeline_output.get("profile", {}).get("data_quality_score", 100.0) if isinstance(pipeline_output.get("profile"), dict) else 100.0,
            "business_health": {
                "health_score": health_score,
                "status": health_status
            },
            "dashboard_metrics": pipeline_output.get("dashboard_metrics", pipeline_output.get("dashboard", {})),
            "recommendations": pipeline_output.get("recommendations", []),
            "insights": pipeline_output.get("insights", []),
            "anomalies": pipeline_output.get("anomalies", []),
            "narrative_summary": pipeline_output.get("summary_narrative", ""),
            "pdf_report_base64": pdf_base64_str,
            "pdf_filename": f"{company_name.lower().replace(' ', '_')}_executive_report.pdf"
        }

        logger.info("Pipeline execution completed successfully. Returning payload to UI.")
        return JSONResponse(status_code=status.HTTP_200_OK, content=response_payload)

    except ValueError as ve:
        logger.error(f"Validation failure during processing: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data Processing Error: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"Pipeline execution failure: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline Orchestration Error: {str(e)}"
        )

    finally:
        # Resource Cleanup
        file.file.close()
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as err:
                logger.warning(f"Failed to remove temp dir '{temp_dir}': {str(err)}")
