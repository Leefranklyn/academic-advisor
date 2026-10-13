from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import advisor
from .schemas import AdviseRequest, AdviseResponse, PredictRequest, PredictResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Academic Advisor System",
    description="Predicts how a student will perform in next semester's courses and gives advice.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    meta = advisor.get_metadata()
    return {
        "status": "ok",
        "model": meta["model"],
        "classes": meta["classes"],
        "metrics": meta["metrics"],
        "sklearn_version": meta["sklearn_version"],
    }


@app.get("/api/courses")
def courses():
    df = advisor.get_courses()
    cols = ["course_code", "title", "level", "semester", "units", "type", "category", "sem_index"]
    return df[cols].sort_values(["sem_index", "type", "course_code"]).to_dict(orient="records")


@app.get("/api/sample")
def sample(seed: int | None = None):
    """A random synthetic student, handy for demos and testing."""
    return advisor.sample_student(seed)


@app.post("/api/advise", response_model=AdviseResponse)
def advise(req: AdviseRequest):
    try:
        return advisor.advise(
            req.jamb_score, req.study_hours, req.attendance, [r.model_dump() for r in req.results]
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    out = advisor.predict_rows([req.model_dump()])[0]
    return {"predicted_band": out["band"], "probabilities": out["probabilities"]}
