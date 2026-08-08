from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import json
import logging

from backend.services.data_intelligence_pipeline.pipeline import run_pipeline_stream

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# 🚀 STREAMING PIPELINE ENDPOINT (PRODUCTION)
# ============================================
@router.post("/run-pipeline-stream")
async def run_pipeline(file: UploadFile = File(...)):
    """
    Streams Decision Intelligence Pipeline output as JSON lines.

    Response format:
    {
        "log": str,
        "progress": int,
        "done": bool (optional),
        "data": dict (final output only)
    }
    """

    try:
        # ----------------------------------------
        # 🔥 STREAM GENERATOR
        # ----------------------------------------
        def event_stream():
            try:
                # IMPORTANT FIX: reset file pointer (prevents empty reads)
                file.file.seek(0)

                for step in run_pipeline_stream(file.file):

                    # Ensure safe JSON serialization
                    try:
                        yield json.dumps(step, default=str) + "\n"
                    except Exception as ser_err:
                        logger.warning(f"Serialization error: {ser_err}")

                        yield json.dumps({
                            "log": "⚠️ Serialization issue in pipeline output",
                            "progress": 99,
                            "done": False,
                            "data": {}
                        }) + "\n"

            except Exception as e:
                logger.exception(f"[STREAM ERROR] {str(e)}")

                yield json.dumps({
                    "log": f"❌ Pipeline crashed: {str(e)}",
                    "progress": 100,
                    "done": True,
                    "data": {}
                }) + "\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/plain"
        )

    except Exception as e:
        logger.exception(f"[ROUTE ERROR] {str(e)}")

        return StreamingResponse(
            iter([json.dumps({
                "log": f"❌ Request failed: {str(e)}",
                "progress": 100,
                "done": True,
                "data": {}
            }) + "\n"]),
            media_type="text/plain"
        )