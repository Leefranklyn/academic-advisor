from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "Programming",
    "Theory",
    "AI_Data",
    "Systems_Hardware",
    "Networks_Cloud_Security",
    "Software_Apps",
    "Professional",
]
Band = Literal["At Risk", "Average", "Strong"]


class ResultIn(BaseModel):
    course_code: str = Field(examples=["COS 201"])
    score: float = Field(ge=0, le=100)


class AdviseRequest(BaseModel):
    jamb_score: int = Field(ge=100, le=400, examples=[230])
    study_hours: float = Field(ge=0, le=60, description="Study hours per week", examples=[12])
    attendance: float = Field(
        ge=0, le=1, description="Attendance as a fraction, 0 to 1", examples=[0.85]
    )
    results: list[ResultIn] = Field(min_length=1, description="Completed courses and scores")


class CourseAdvice(BaseModel):
    course_code: str
    title: str
    units: int
    type: str
    category: str
    predicted_band: Band
    probabilities: dict[str, float]
    prerequisite_issues: list[str]
    watch_points: list[str]
    advice: str
    recommended: bool


class AdviseResponse(BaseModel):
    summary: dict
    courses: list[CourseAdvice]
    notes: list[str]


class PredictRequest(BaseModel):
    """Raw model features, for testing the pickle directly."""

    jamb_score: int = Field(ge=100, le=400)
    level: int = Field(ge=100, le=400)
    semester: int = Field(ge=1, le=2)
    units: int = Field(ge=1, le=6)
    is_elective: int = Field(ge=0, le=1)
    category: Category
    study_hours: float = Field(ge=0, le=60)
    attendance: float = Field(ge=0, le=1)
    prior_cgpa: float = Field(ge=0, le=5)
    prior_semester_gpa: float = Field(ge=0, le=5)
    prior_avg_score: float = Field(ge=0, le=100)
    courses_failed_so_far: int = Field(ge=0)
    courses_taken_so_far: int = Field(ge=0)
    category_avg_prior: float = Field(ge=0, le=100)
    has_category_history: int = Field(ge=0, le=1)
    prereq_avg_score: float = Field(ge=0, le=100)
    has_prereqs: int = Field(ge=0, le=1)


class PredictResponse(BaseModel):
    predicted_band: Band
    probabilities: dict[str, float]
