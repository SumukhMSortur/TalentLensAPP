"""
TalentLens AI — FastAPI Backend Server

Provides REST endpoints for:
  - Video upload
  - Athlete vs User comparison processing
  - Serving processed/annotated videos
  - Retrieving analysis results
"""

import hashlib
import logging
import os
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# Ensure project root is on the import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.features.feature_extractor import FeatureExtractor
from src.pose.pose_extractor import PoseExtractor
from src.scoring.score_calculator import ScoreCalculator
from src.analytics.model_performance import ModelPerformanceAnalyzer
from src.comparison.comparison_service import (
    compare_sequences,
    process_video,
    render_comparison_annotations,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("talentlens")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "web_demo"
UPLOAD_DIR = OUTPUT_ROOT / "uploads"
PROCESSED_DIR = OUTPUT_ROOT / "processed"
RENDER_VERSION = "v3_web"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Shared service instances (created once)
# ---------------------------------------------------------------------------
pose_extractor = PoseExtractor(debug=False, model_complexity=1)
feature_extractor = FeatureExtractor()
scorer = ScoreCalculator()
model_analyzer = ModelPerformanceAnalyzer()

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="TalentLens AI",
    description="AI-powered Action Quality Assessment API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# Serve output videos as static files
app.mount("/videos", StaticFiles(directory=str(OUTPUT_ROOT)), name="videos")


@app.get("/")
async def root():
    return RedirectResponse(url="/app/")


# ---------------------------------------------------------------------------
# In-memory result store (keyed by job_id)
# ---------------------------------------------------------------------------
results_store: dict = {}


def _save_upload(upload_bytes: bytes, prefix: str, original_name: str) -> Path:
    """Persist uploaded bytes to disk with a content-based filename."""
    suffix = Path(original_name).suffix or ".mp4"
    digest = hashlib.md5(upload_bytes).hexdigest()[:12]
    out_path = UPLOAD_DIR / f"{prefix}_{digest}{suffix}"
    if not out_path.exists():
        out_path.write_bytes(upload_bytes)
    return out_path


def _make_video_url(absolute_path: str) -> str:
    """Convert absolute path to a relative URL the frontend can fetch."""
    try:
        rel = Path(absolute_path).relative_to(OUTPUT_ROOT)
        return f"/videos/{rel.as_posix()}"
    except ValueError:
        # File is outside OUTPUT_ROOT — copy it there
        dest = PROCESSED_DIR / Path(absolute_path).name
        if not dest.exists():
            import shutil
            shutil.copy2(absolute_path, dest)
        rel = dest.relative_to(OUTPUT_ROOT)
        return f"/videos/{rel.as_posix()}"


def _serialise_comparison(comparison: dict) -> dict:
    """Make the comparison dict JSON-safe (numpy → python)."""
    import numpy as np

    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        return obj

    out = {}
    for key, value in comparison.items():
        if key == "frame_feedback":
            # Drop heavy per-frame data from REST response (kept on server)
            out["frame_feedback_count"] = len(value) if value else 0
            continue
        out[key] = convert(value)
    return out


def _serialise_result(result: dict) -> dict:
    """Build a JSON-safe summary from a process_video result dict."""
    import numpy as np
    return {
        "role": result["role"],
        "action": result["action"],
        "exercise_type": result["exercise_type"],
        "rep_count": int(result["rep_count"]),
        "score_details": result["score_details"],
        "prediction": {
            "predicted_label": result["prediction"]["predicted_label"],
            "confidence": float(result["prediction"]["confidence"]),
            "probabilities": {
                k: float(v)
                for k, v in result["prediction"]["probabilities"].items()
            },
        },
        "original_video_url": _make_video_url(result["video_path"]),
        "annotated_video_url": _make_video_url(result["annotated_video_path"]),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/actions")
async def list_actions():
    """Return available exercise categories from the dataset."""
    video_root = PROJECT_ROOT / "dataset" / "videos"
    if not video_root.exists():
        return {"actions": ["squat", "push-up", "pull Up"]}
    actions = [item.name for item in sorted(video_root.iterdir()) if item.is_dir()]
    return {"actions": actions if actions else ["squat", "push-up", "pull Up"]}


@app.post("/api/compare")
async def compare_videos(
    athlete_video: UploadFile = File(...),
    user_video: UploadFile = File(...),
    action: str = Form("squat"),
):
    """
    Upload two videos (athlete + user), run the full comparison pipeline,
    and return a job_id to retrieve results.
    """
    try:
        athlete_bytes = await athlete_video.read()
        user_bytes = await user_video.read()

        athlete_path = _save_upload(athlete_bytes, "athlete", athlete_video.filename)
        user_path = _save_upload(user_bytes, "user", user_video.filename)

        logger.info(f"Processing athlete video: {athlete_path}")
        athlete_result = process_video(
            video_path=str(athlete_path),
            action_name=action,
            role_name="Athlete",
            output_root=PROCESSED_DIR / RENDER_VERSION,
            pose_extractor=pose_extractor,
            feature_extractor=feature_extractor,
            scorer=scorer,
            model_analyzer=model_analyzer,
        )

        logger.info(f"Processing user video: {user_path}")
        user_result = process_video(
            video_path=str(user_path),
            action_name=action,
            role_name="User",
            output_root=PROCESSED_DIR / RENDER_VERSION,
            pose_extractor=pose_extractor,
            feature_extractor=feature_extractor,
            scorer=scorer,
            model_analyzer=model_analyzer,
        )

        logger.info("Comparing sequences...")
        comparison = compare_sequences(
            athlete_result["angle_sequence"],
            user_result["angle_sequence"],
        )

        # Render comparison overlay on user video
        compared_user_video = (
            PROCESSED_DIR / RENDER_VERSION
            / f"user_comparison_{Path(str(user_path)).stem}_{RENDER_VERSION}.mp4"
        )
        render_comparison_annotations(
            processed_video=user_result,
            comparison_result=comparison,
            output_path=compared_user_video,
            pose_extractor=pose_extractor,
        )
        user_result["comparison_video_path"] = str(compared_user_video)
        athlete_result["comparison_video_path"] = athlete_result["annotated_video_path"]

        # Also copy original uploads into output so they can be served
        import shutil
        athlete_upload_serve = PROCESSED_DIR / f"athlete_original_{athlete_path.name}"
        user_upload_serve = PROCESSED_DIR / f"user_original_{user_path.name}"
        if not athlete_upload_serve.exists():
            shutil.copy2(str(athlete_path), str(athlete_upload_serve))
        if not user_upload_serve.exists():
            shutil.copy2(str(user_path), str(user_upload_serve))

        job_id = uuid.uuid4().hex[:12]
        results_store[job_id] = {
            "athlete": athlete_result,
            "user": user_result,
            "comparison": comparison,
        }

        # Build JSON-safe response
        response = {
            "job_id": job_id,
            "athlete": _serialise_result(athlete_result),
            "user": _serialise_result(user_result),
            "athlete_comparison_video_url": _make_video_url(
                athlete_result["comparison_video_path"]
            ),
            "user_comparison_video_url": _make_video_url(
                user_result["comparison_video_path"]
            ),
            "athlete_original_video_url": _make_video_url(str(athlete_upload_serve)),
            "user_original_video_url": _make_video_url(str(user_upload_serve)),
            "comparison": _serialise_comparison(comparison),
        }

        logger.info(f"Comparison job {job_id} completed successfully.")
        return JSONResponse(content=response)

    except Exception as exc:
        logger.exception("Comparison failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Retrieve cached results for a completed job."""
    payload = results_store.get(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    athlete_result = payload["athlete"]
    user_result = payload["user"]
    comparison = payload["comparison"]

    return JSONResponse(content={
        "job_id": job_id,
        "athlete": _serialise_result(athlete_result),
        "user": _serialise_result(user_result),
        "comparison": _serialise_comparison(comparison),
    })


@app.get("/api/model-metrics")
async def get_model_metrics():
    """Return model performance metrics (or baseline fallback)."""
    metrics = model_analyzer.load_metrics()
    return JSONResponse(content={
        "source": metrics.get("source", "unknown"),
        "accuracy": metrics.get("accuracy"),
        "loss": metrics.get("loss"),
    })


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
