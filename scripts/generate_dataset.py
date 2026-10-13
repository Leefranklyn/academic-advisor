"""
Synthetic academic dataset for the Academic Advisor System.

Curriculum source: Department of Computer Science, course allocation 2026/2027
(100 to 400 level, both semesters, including electives).

ASSUMED (not in the allocation sheet, edit if you know the real values):
  - prerequisites
  - course difficulty (1 to 5)
  - course category
  - grading scale (Nigerian 5-point scale, see GRADE_SCALE)

Run:
    python generate_dataset.py --students 1000 --seed 42 --out data
"""
import argparse
import os

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# 1. COURSE CATALOG
# (code, title, level, semester, units, type, category, difficulty, prerequisites)
# ----------------------------------------------------------------------------
C = [
    # 100 level, first semester
    ("COS 101", "Introduction to Computing Sciences", 100, 1, 3, "core", "Theory", 2, ""),
    ("VUA-CSC 107", "Systems Analysis and Design", 100, 1, 2, "core", "Software_Apps", 2, ""),
    ("VUA-CSC 105", "Cloud Computing Fundamentals", 100, 1, 2, "core", "Networks_Cloud_Security", 2, ""),
    ("VUA-CSC 103", "Introduction to Information Systems", 100, 1, 2, "elective", "Software_Apps", 1, ""),
    # 100 level, second semester
    ("COS 102", "Problem Solving", 100, 2, 2, "core", "Programming", 3, ""),
    ("VUA-CSC 104", "Introduction to Web Development", 100, 2, 2, "core", "Software_Apps", 2, "COS 101"),
    ("VUA-CSC 106", "AI Project Development and Prototyping", 100, 2, 2, "core", "AI_Data", 2, "COS 101"),
    ("VUA-CSC 114", "Foundations of Artificial Intelligence", 100, 2, 2, "core", "AI_Data", 3, "COS 101"),
    ("VUA-CSC 110", "Image Processing and Computer Vision", 100, 2, 2, "elective", "AI_Data", 3, "COS 101"),
    # 200 level, first semester
    ("COS 201", "Computer Programming I", 200, 1, 3, "core", "Programming", 3, "COS 102"),
    ("VUA-CSC 209", "System Modelling and Simulation", 200, 1, 2, "core", "Theory", 3, "COS 101"),
    ("CSC 203", "Discrete Structures", 200, 1, 2, "core", "Theory", 4, ""),
    ("VUA-CSC 207", "Human Computer Interaction II", 200, 1, 2, "core", "Software_Apps", 2, "VUA-CSC 104"),
    ("CYB 201", "Introduction to Cybersecurity and Strategy", 200, 1, 2, "core", "Networks_Cloud_Security", 3, "COS 101"),
    ("SEN 201", "Introduction to Software Engineering", 200, 1, 2, "core", "Software_Apps", 3, "VUA-CSC 107"),
    ("IFT 211", "Digital Logic Design", 200, 1, 2, "core", "Systems_Hardware", 4, "COS 101"),
    ("VUA-CSC 205", "Natural Language Processing", 200, 1, 2, "elective", "AI_Data", 3, "VUA-CSC 114"),
    # 200 level, second semester
    ("IFT 212", "Computer Architecture and Organization", 200, 2, 2, "core", "Systems_Hardware", 4, "IFT 211"),
    ("COS 202", "Computer Programming II", 200, 2, 3, "core", "Programming", 4, "COS 201"),
    ("VUA-CSC 214", "Embedded Systems", 200, 2, 3, "core", "Systems_Hardware", 4, "IFT 211"),
    ("VUA-CSC 222", "Data Science and Big Data", 200, 2, 2, "core", "AI_Data", 3, "COS 201"),
    ("CSC 299", "SIWES I", 200, 2, 3, "core", "Professional", 1, "COS 201"),
    ("VUA-CSC 208", "Data Mining", 200, 2, 2, "elective", "AI_Data", 3, "VUA-CSC 114"),
    # 300 level, first semester
    ("CSC 301", "Data Structures", 300, 1, 3, "core", "Programming", 5, "COS 202,CSC 203"),
    ("CSC 309", "Artificial Intelligence", 300, 1, 2, "core", "AI_Data", 4, "VUA-CSC 114,CSC 203"),
    ("ICT 305", "Data Communication System and Network", 300, 1, 3, "core", "Networks_Cloud_Security", 3, "IFT 212"),
    ("VUA-CSC 317", "Mobile Application Development", 300, 1, 2, "core", "Software_Apps", 3, "COS 202"),
    ("VUA-CSC 303", "Artificial Intelligence Tools and Frameworks", 300, 1, 3, "core", "AI_Data", 3, "VUA-CSC 114,COS 202"),
    ("VUA-CSC 319", "Games Application Development", 300, 1, 3, "elective", "Software_Apps", 3, "COS 202"),
    # 300 level, second semester
    ("DTS 304", "Data Management I", 300, 2, 3, "core", "AI_Data", 3, "VUA-CSC 222"),
    ("CSC 308", "Operating Systems", 300, 2, 3, "core", "Systems_Hardware", 5, "IFT 212,COS 202"),
    ("CSC 322", "Computer Science Innovation and New Technologies", 300, 2, 2, "core", "Professional", 2, ""),
    ("VUA-CSC 314", "Introduction to Robotics Design", 300, 2, 3, "core", "Systems_Hardware", 3, "VUA-CSC 214"),
    ("CSC 399", "SIWES II", 300, 2, 3, "core", "Professional", 1, "CSC 299"),
    ("VUA-CSC 302", "Object Oriented Programming", 300, 2, 2, "elective", "Programming", 3, "COS 202"),
    # 400 level, first semester
    ("COS 409", "Research Methodology and Technical Report Writing", 400, 1, 2, "core", "Professional", 2, ""),
    ("CSC 401", "Algorithms and Analysis of Complexity", 400, 1, 2, "core", "Theory", 5, "CSC 301,CSC 203"),
    ("INS 401", "Project Management", 400, 1, 2, "core", "Professional", 2, ""),
    ("VUA-CSC 439", "Robotics and Control Systems", 400, 1, 3, "core", "Systems_Hardware", 4, "VUA-CSC 314"),
    ("VUA-CSC 423", "Computer Networks and Communication", 400, 1, 3, "core", "Networks_Cloud_Security", 3, "ICT 305"),
    ("VUA-CSC 405", "Software Testing and Quality Assurance", 400, 1, 2, "core", "Software_Apps", 3, "SEN 201"),
    ("CSC 497", "Final Year Project I", 400, 1, 3, "core", "Professional", 3, "CSC 399"),
    ("VUA-CSC 481", "Intelligent Systems", 400, 1, 2, "elective", "AI_Data", 4, "CSC 309"),
    # 400 level, second semester
    ("CSC 498", "Final Year Project II", 400, 2, 3, "core", "Professional", 3, "CSC 497"),
    ("CSC 402", "Ethics and Legal Issues in Computer Science", 400, 2, 2, "core", "Professional", 2, ""),
    ("VUA-CSC 404", "Advanced Cloud Computing", 400, 2, 2, "core", "Networks_Cloud_Security", 4, "VUA-CSC 105"),
    ("VUA-CSC 406", "Machine Learning", 400, 2, 2, "core", "AI_Data", 5, "VUA-CSC 303,VUA-CSC 222"),
    ("VUA-CSC 432", "Computer Graphics and Visualization", 400, 2, 2, "core", "Software_Apps", 4, "COS 202"),
    ("VUA-CSC 408", "Enterprise Architecture Design", 400, 2, 2, "core", "Software_Apps", 3, "SEN 201"),
    ("VUA-CSC 412", "Internet of Things", 400, 2, 2, "core", "Systems_Hardware", 3, "VUA-CSC 214"),
    ("VUA-CSC 416", "Advanced Modelling and Prototyping", 400, 2, 2, "elective", "Theory", 3, "VUA-CSC 209"),
]
COLS = ["course_code", "title", "level", "semester", "units", "type",
        "category", "difficulty", "prerequisites"]
courses = pd.DataFrame(C, columns=COLS)
courses["sem_index"] = (courses["level"] // 100 - 1) * 2 + courses["semester"]  # 1..8
courses["prerequisites_assumed"] = True

# Which hidden aptitudes drive each course category
APTITUDES = ["programming", "theory", "ai_data", "systems", "applied"]
CATEGORY_WEIGHTS = {
    "Programming":             {"programming": .70, "theory": .20, "applied": .10},
    "Theory":                  {"theory": .70, "programming": .20, "applied": .10},
    "AI_Data":                 {"ai_data": .50, "theory": .25, "programming": .25},
    "Systems_Hardware":        {"systems": .70, "theory": .20, "programming": .10},
    "Networks_Cloud_Security": {"systems": .50, "applied": .30, "programming": .20},
    "Software_Apps":           {"programming": .40, "applied": .40, "theory": .20},
    "Professional":            {"applied": .60, "programming": .20, "theory": .20},
}

# Assumed grading scale (Nigerian 5-point). Change to your official scale.
GRADE_SCALE = [(70, "A", 5), (60, "B", 4), (50, "C", 3), (45, "D", 2), (40, "E", 1), (0, "F", 0)]


def to_grade(score):
    for cutoff, letter, points in GRADE_SCALE:
        if score >= cutoff:
            return letter, points


def to_band(score):
    if score < 50:
        return "At Risk"
    if score < 65:
        return "Average"
    return "Strong"


def build(n_students, seed):
    rng = np.random.default_rng(seed)
    by_code = courses.set_index("course_code")

    # sanity: every prerequisite must be scheduled in an earlier semester
    for _, r in courses.iterrows():
        for p in filter(None, r["prerequisites"].split(",")):
            assert by_code.loc[p, "sem_index"] < r["sem_index"], (r["course_code"], p)

    students, sems, results = [], [], []

    for i in range(1, n_students + 1):
        sid = f"S{i:04d}"
        g = rng.normal()                       # general ability
        conscientious = rng.normal()           # drives study habits
        apt = {a: float(np.clip(0.55 + 0.09 * g + 0.13 * rng.normal(), 0.15, 0.97)) for a in APTITUDES}
        jamb = int(np.clip(round(215 + 30 * g + 15 * rng.normal()), 160, 330))
        base_hours = float(np.clip(10 + 4 * conscientious + 2 * rng.normal(), 2, 30))
        base_att = float(np.clip(0.78 + 0.08 * conscientious + 0.05 * rng.normal(), 0.45, 1.0))
        completed = int(rng.integers(1, 9))    # semesters completed, 1..8

        students.append({"student_id": sid, "jamb_score": jamb,
                         "completed_semesters": completed,
                         "current_level": min(400, (completed // 2 + 1) * 100) if completed < 8 else 400})

        done = {}  # course_code -> score
        for s in range(1, completed + 1):
            hours = float(np.clip(base_hours + rng.normal(0, 1.5), 1, 35))
            att = float(np.clip(base_att + rng.normal(0, 0.04), 0.4, 1.0))
            shock = rng.normal(0, 3)

            offered = courses[courses["sem_index"] == s]
            take = []
            for _, c in offered.iterrows():
                if c["type"] == "core":
                    take.append(c)
                else:
                    w = CATEGORY_WEIGHTS[c["category"]]
                    interest = sum(w[k] * apt[k] for k in w)
                    if rng.random() < np.clip(0.2 + 0.7 * interest, 0, 0.9):
                        take.append(c)

            sem_rows = []
            for c in take:
                w = CATEGORY_WEIGHTS[c["category"]]
                ability = sum(w[k] * apt[k] for k in w)
                prereqs = [p for p in c["prerequisites"].split(",") if p]
                prereq_effect = 0.0
                if prereqs:
                    prereq_avg = np.mean([done[p] for p in prereqs])
                    prereq_effect = 0.20 * (prereq_avg - 58)
                score = (26 + 62 * ability
                         + 0.55 * (hours - 10)
                         + 28 * (att - 0.78)
                         - 4 * (c["difficulty"] - 3)
                         + prereq_effect + shock + rng.normal(0, 6.5))
                score = int(np.clip(round(score), 0, 100))
                letter, pts = to_grade(score)
                sem_rows.append((c, score, letter, pts, hours, att))

            # features available BEFORE this semester (what an advisor would know)
            prior_codes = list(done.keys())
            prior_scores = [done[k] for k in prior_codes]
            prior_units = [by_code.loc[k, "units"] for k in prior_codes]
            prior_pts = [to_grade(done[k])[1] for k in prior_codes]
            if prior_codes:
                prior_cgpa = float(np.dot(prior_pts, prior_units) / sum(prior_units))
                prior_avg = float(np.mean(prior_scores))
                n_failed = int(sum(1 for v in prior_scores if v < 40))
            else:
                prior_cgpa = prior_avg = np.nan
                n_failed = 0
            results_sem_gpa = None
            if sems and sems[-1]["student_id"] == sid:
                results_sem_gpa = sems[-1]["semester_gpa"]

            for c, score, letter, pts, h, a in sem_rows:
                results.append({"student_id": sid, "course_code": c["course_code"],
                                "sem_index": s, "score": score, "grade": letter,
                                "grade_points": pts, "grade_band": to_band(score),
                                "study_hours": round(h, 1), "attendance": round(a, 3),
                                "prior_cgpa": prior_cgpa, "prior_avg_score": prior_avg,
                                "prior_semester_gpa": results_sem_gpa if results_sem_gpa is not None else np.nan,
                                "courses_failed_so_far": n_failed,
                                "courses_taken_so_far": len(prior_codes)})
            tot_u = sum(c["units"] for c, *_ in sem_rows)
            sem_gpa = sum(c["units"] * p for c, _, _, p, *_ in sem_rows) / tot_u
            sems.append({"student_id": sid, "sem_index": s,
                         "study_hours": round(hours, 1), "attendance": round(att, 3),
                         "units_taken": tot_u, "semester_gpa": round(sem_gpa, 2)})
            for c, score, *_ in sem_rows:
                done[c["course_code"]] = score

    students = pd.DataFrame(students)
    sems = pd.DataFrame(sems)
    results = pd.DataFrame(results)
    return students, sems, results


def model_ready(students, results):
    """One row per (student, course), features known BEFORE the course is taken."""
    cat = courses.set_index("course_code")
    r = results.merge(courses[["course_code", "level", "semester", "units", "type", "category", "prerequisites"]],
                      on="course_code")
    r = r.merge(students[["student_id", "jamb_score"]], on="student_id")
    r = r[r["sem_index"] > 1].copy()  # first semester has no history

    # category history and prerequisite performance, computed from earlier results only
    score_lookup = {(a, b): c for a, b, c in zip(results.student_id, results.course_code, results.score)}
    by_student = results.groupby("student_id")

    cat_avg, has_cat, pre_avg, has_pre = [], [], [], []
    hist = {sid: g[["course_code", "sem_index", "score"]].values.tolist() for sid, g in by_student}
    for sid, code, s, cg, prereqs, pavg in zip(r.student_id, r.course_code, r.sem_index,
                                               r.category, r.prerequisites, r.prior_avg_score):
        same = [sc for cc, si, sc in hist[sid] if si < s and cat.loc[cc, "category"] == cg]
        cat_avg.append(np.mean(same) if same else pavg)
        has_cat.append(int(bool(same)))
        pl = [score_lookup[(sid, p)] for p in prereqs.split(",") if p and (sid, p) in score_lookup]
        pre_avg.append(np.mean(pl) if pl else pavg)
        has_pre.append(int(bool(pl)))
    r["category_avg_prior"] = np.round(cat_avg, 2)
    r["has_category_history"] = has_cat
    r["prereq_avg_score"] = np.round(pre_avg, 2)
    r["has_prereqs"] = has_pre
    r["is_elective"] = (r["type"] == "elective").astype(int)
    r["prior_semester_gpa"] = r["prior_semester_gpa"].fillna(r["prior_cgpa"])
    r["prior_cgpa"] = r["prior_cgpa"].round(2)
    r["prior_avg_score"] = r["prior_avg_score"].round(2)
    r["prior_semester_gpa"] = r["prior_semester_gpa"].round(2)

    cols = ["student_id", "course_code", "jamb_score", "level", "semester", "units", "is_elective",
            "category", "study_hours", "attendance", "prior_cgpa", "prior_semester_gpa",
            "prior_avg_score", "courses_failed_so_far", "courses_taken_so_far",
            "category_avg_prior", "has_category_history", "prereq_avg_score", "has_prereqs",
            "score", "grade", "grade_band"]
    return r[cols].reset_index(drop=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--students", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    students, sems, results = build(args.students, args.seed)
    mr = model_ready(students, results)

    out_results = results[["student_id", "course_code", "sem_index", "score", "grade", "grade_points"]]
    courses.to_csv(f"{args.out}/courses.csv", index=False)
    students.to_csv(f"{args.out}/students.csv", index=False)
    sems.to_csv(f"{args.out}/student_semesters.csv", index=False)
    out_results.to_csv(f"{args.out}/results.csv", index=False)
    mr.to_csv(f"{args.out}/model_ready.csv", index=False)

    print(f"courses: {len(courses)}  students: {len(students)}  results: {len(results)}  model_ready: {len(mr)}")
    print(mr["grade_band"].value_counts(normalize=True).round(3).to_string())
    print(mr["grade"].value_counts(normalize=True).sort_index().round(3).to_string())
