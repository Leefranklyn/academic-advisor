"""
Advisor logic.

The ML model only predicts a grade band for one student in one course.
Everything else here is ordinary code: turning a student's results into the
model's features, checking prerequisites, applying rules and writing advice.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = Path(os.getenv("MODEL_PATH", BASE_DIR / "models" / "advisor_model.pkl"))
META_PATH = Path(os.getenv("META_PATH", BASE_DIR / "models" / "model_metadata.json"))
DATA_DIR = BASE_DIR / "data"

# Must match scripts/generate_dataset.py
GRADE_SCALE = [(70, "A", 5), (60, "B", 4), (50, "C", 3), (45, "D", 2), (40, "E", 1), (0, "F", 0)]
FAIL_MARK = 40
MAX_UNITS = 24
LOW_ATTENDANCE = 0.75
LOW_STUDY_HOURS = 8
WEAK_SCORE = 50

LEVEL_NAMES = {1: "first", 2: "second"}


# ---------------------------------------------------------------- loading
@lru_cache(maxsize=1)
def get_courses() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "courses.csv").fillna({"prerequisites": ""})
    df.index = df["course_code"]
    df.index.name = None  # avoid index/column name ambiguity in sort_values
    return df


@lru_cache(maxsize=1)
def get_model():
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def get_metadata() -> dict:
    with open(META_PATH) as f:
        return json.load(f)


def semester_label(sem_index: int) -> str:
    level = (sem_index - 1) // 2 + 1
    sem = (sem_index - 1) % 2 + 1
    return f"{level * 100} level, {LEVEL_NAMES[sem]} semester"


# ---------------------------------------------------------------- helpers
def points_for(score: float) -> int:
    for cutoff, _, pts in GRADE_SCALE:
        if score >= cutoff:
            return pts
    return 0


def letter_for(score: float) -> str:
    for cutoff, letter, _ in GRADE_SCALE:
        if score >= cutoff:
            return letter
    return "F"


def gpa(rows: list[dict]) -> float:
    units = sum(r["units"] for r in rows)
    return sum(r["units"] * r["points"] for r in rows) / units


def build_history(results: list[dict]) -> list[dict]:
    """Attach catalog info to the results a student entered (last entry wins on duplicates)."""
    courses = get_courses()
    unknown = [r["course_code"] for r in results if r["course_code"] not in courses.index]
    if unknown:
        raise ValueError(f"Unknown course code(s): {', '.join(unknown)}")

    latest = {r["course_code"]: float(r["score"]) for r in results}
    history = []
    for code, score in latest.items():
        c = courses.loc[code]
        history.append(
            {
                "course_code": code,
                "title": c["title"],
                "score": score,
                "sem_index": int(c["sem_index"]),
                "units": int(c["units"]),
                "category": c["category"],
                "points": points_for(score),
            }
        )
    return history


def course_features(
    course, history: list[dict], jamb: int, hours: float, attendance: float
) -> dict:
    """Features for one upcoming course, computed only from results before it."""
    scores = [h["score"] for h in history]
    prior_avg = float(np.mean(scores))
    last_sem = max(h["sem_index"] for h in history)
    last_sem_rows = [h for h in history if h["sem_index"] == last_sem]

    same_cat = [h["score"] for h in history if h["category"] == course["category"]]
    prereqs = [p for p in str(course["prerequisites"]).split(",") if p]
    by_code = {h["course_code"]: h["score"] for h in history}
    prereq_scores = [by_code[p] for p in prereqs if p in by_code]

    return {
        "jamb_score": jamb,
        "level": int(course["level"]),
        "semester": int(course["semester"]),
        "units": int(course["units"]),
        "is_elective": int(course["type"] == "elective"),
        "category": course["category"],
        "study_hours": hours,
        "attendance": attendance,
        "prior_cgpa": round(gpa(history), 2),
        "prior_semester_gpa": round(gpa(last_sem_rows), 2),
        "prior_avg_score": round(prior_avg, 2),
        "courses_failed_so_far": int(sum(s < FAIL_MARK for s in scores)),
        "courses_taken_so_far": len(history),
        "category_avg_prior": round(float(np.mean(same_cat)) if same_cat else prior_avg, 2),
        "has_category_history": int(bool(same_cat)),
        "prereq_avg_score": round(float(np.mean(prereq_scores)) if prereq_scores else prior_avg, 2),
        "has_prereqs": int(bool(prereq_scores)),
    }


def predict_rows(rows: list[dict]) -> list[dict]:
    """Run the pickled pipeline on a list of feature dicts."""
    model = get_model()
    features = get_metadata()["features"]
    X = pd.DataFrame(rows)[features]
    probs = model.predict_proba(X)
    out = []
    for p in probs:
        dist = {cls: round(float(v), 4) for cls, v in zip(model.classes_, p)}
        out.append({"band": max(dist, key=dist.get), "probabilities": dist})
    return out


# ---------------------------------------------------------------- rules
def prerequisite_issues(course, history: list[dict]) -> list[str]:
    by_code = {h["course_code"]: h["score"] for h in history}
    courses = get_courses()
    issues = []
    for p in [p for p in str(course["prerequisites"]).split(",") if p]:
        name = f"{p} ({courses.loc[p, 'title']})"
        if p not in by_code:
            issues.append(f"Prerequisite {name} is not on your record.")
        elif by_code[p] < FAIL_MARK:
            issues.append(f"You failed {name}. Clear that carryover first.")
        elif by_code[p] < WEAK_SCORE:
            issues.append(f"Weak result in {name}: {by_code[p]:.0f}. Revise it before this course.")
    return issues


def watch_points(feat: dict) -> list[str]:
    pts = []
    if feat["attendance"] < LOW_ATTENDANCE:
        pts.append(f"Attendance is {feat['attendance']:.0%}. Aim for at least 75%.")
    if feat["study_hours"] < LOW_STUDY_HOURS:
        pts.append(f"Study time is {feat['study_hours']:.0f} hours a week. Try to reach 8 or more.")
    if feat["has_category_history"] and feat["category_avg_prior"] < WEAK_SCORE:
        pts.append(
            f"Your average in {feat['category'].replace('_', ' ')} courses is "
            f"{feat['category_avg_prior']:.0f}, which is below 50."
        )
    if feat["prior_cgpa"] < 2.0:
        pts.append(f"Your CGPA is {feat['prior_cgpa']:.2f}. Consider a lighter elective load.")
    return pts


def advice_text(band: str, has_flags: bool) -> str:
    if band == "At Risk":
        return (
            "High risk. Start early, attend every class and see the lecturer or a "
            "course adviser before the first test."
            if has_flags
            else "High risk based on your overall record. Start early and get support "
            "from the lecturer or a course adviser."
        )
    if band == "Average":
        return "Manageable. A bit more consistent study should move this to a strong result."
    return "Good fit for your current record."


# ---------------------------------------------------------------- main entry
def advise(jamb: int, hours: float, attendance: float, results: list[dict]) -> dict:
    history = build_history(results)
    last_sem = max(h["sem_index"] for h in history)
    next_sem = last_sem + 1

    summary = {
        "cgpa": round(gpa(history), 2),
        "courses_on_record": len(history),
        "courses_failed": int(sum(h["score"] < FAIL_MARK for h in history)),
        "last_semester": semester_label(last_sem),
        "next_semester": semester_label(next_sem) if next_sem <= 8 else None,
    }
    if next_sem > 8:
        return {
            "summary": summary,
            "courses": [],
            "notes": ["You have completed the final semester on the curriculum."],
        }

    courses = get_courses()
    offered = courses[courses["sem_index"] == next_sem]
    feats = [course_features(c, history, jamb, hours, attendance) for _, c in offered.iterrows()]
    preds = predict_rows(feats)

    items = []
    for (_, c), feat, pred in zip(offered.iterrows(), feats, preds):
        issues = prerequisite_issues(c, history)
        flags = watch_points(feat)
        items.append(
            {
                "course_code": c["course_code"],
                "title": c["title"],
                "units": int(c["units"]),
                "type": c["type"],
                "category": c["category"],
                "predicted_band": pred["band"],
                "probabilities": pred["probabilities"],
                "prerequisite_issues": issues,
                "watch_points": flags,
                "advice": advice_text(pred["band"], bool(issues or flags)),
                "recommended": c["type"] == "core",
            }
        )

    # Electives: rank by P(Strong) - P(At Risk), recommend the best one unless it is high risk.
    electives = sorted(
        (i for i in items if i["type"] == "elective"),
        key=lambda i: i["probabilities"]["Strong"] - i["probabilities"]["At Risk"],
        reverse=True,
    )
    notes = []
    if electives:
        best = electives[0]
        if best["predicted_band"] != "At Risk" and not best["prerequisite_issues"]:
            best["recommended"] = True
            notes.append(f"Suggested elective: {best['course_code']} {best['title']}.")
        else:
            notes.append("No elective is recommended this semester. Focus on the core courses.")

    total_units = sum(i["units"] for i in items if i["recommended"])
    summary["recommended_units"] = total_units
    if total_units > MAX_UNITS:
        notes.append(f"Recommended load is {total_units} units, above the {MAX_UNITS}-unit limit.")

    at_risk = [
        i["course_code"] for i in items if i["predicted_band"] == "At Risk" and i["type"] == "core"
    ]
    if at_risk:
        notes.append("Core courses to prioritise: " + ", ".join(at_risk) + ".")

    items.sort(key=lambda i: (i["type"] != "core", -(i["probabilities"]["At Risk"])))
    return {"summary": summary, "courses": items, "notes": notes}


# ---------------------------------------------------------------- demo data
@lru_cache(maxsize=1)
def _demo_tables():
    students = pd.read_csv(DATA_DIR / "students.csv")
    results = pd.read_csv(DATA_DIR / "results.csv")
    sems = pd.read_csv(DATA_DIR / "student_semesters.csv")
    return students, results, sems


def sample_student(seed: int | None = None) -> dict:
    """A random synthetic student with at least two completed semesters (for demos)."""
    students, results, sems = _demo_tables()
    pool = students[(students["completed_semesters"] >= 2) & (students["completed_semesters"] <= 7)]
    row = pool.sample(1, random_state=seed).iloc[0]
    sid = row["student_id"]
    r = results[results["student_id"] == sid]
    s = sems[sems["student_id"] == sid]
    return {
        "student_id": sid,
        "jamb_score": int(row["jamb_score"]),
        "study_hours": round(float(s["study_hours"].iloc[-1]), 1),
        "attendance": round(float(s["attendance"].iloc[-1]), 3),
        "results": [
            {"course_code": c, "score": int(sc)} for c, sc in zip(r["course_code"], r["score"])
        ],
    }
