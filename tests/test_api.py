import pytest
from fastapi.testclient import TestClient

from app import advisor
from app.main import app

client = TestClient(app)

PROFILE = {"jamb_score": 230, "study_hours": 12, "attendance": 0.85}


def advise(results, **overrides):
    return client.post("/api/advise", json={**PROFILE, **overrides, "results": results})


def test_health_reports_model():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["classes"] == ["At Risk", "Average", "Strong"]


def test_courses_catalog_is_complete():
    r = client.get("/api/courses")
    assert r.status_code == 200
    assert len(r.json()) == 51


def test_index_page_is_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Academic Advisor" in r.text


def test_advise_with_sample_student():
    s = client.get("/api/sample?seed=3").json()
    r = advise(
        s["results"],
        jamb_score=s["jamb_score"],
        study_hours=s["study_hours"],
        attendance=s["attendance"],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["courses"], "expected courses for the next semester"
    for c in body["courses"]:
        assert c["predicted_band"] in ("At Risk", "Average", "Strong")
        assert sum(c["probabilities"].values()) == pytest.approx(1.0, abs=1e-2)


def test_next_semester_follows_last_result():
    r = advise([{"course_code": "COS 102", "score": 65}])  # 100 level, second semester
    body = r.json()
    assert body["summary"]["next_semester"] == "200 level, first semester"
    codes = {c["course_code"] for c in body["courses"]}
    assert {"COS 201", "CSC 203", "IFT 211"} <= codes


def test_missing_prerequisite_is_flagged():
    r = advise([{"course_code": "COS 102", "score": 65}])
    hci = next(c for c in r.json()["courses"] if c["course_code"] == "VUA-CSC 207")
    assert any("VUA-CSC 104" in i for i in hci["prerequisite_issues"])


def test_failed_prerequisite_is_flagged_as_carryover():
    r = advise([{"course_code": "COS 102", "score": 30}])
    prog = next(c for c in r.json()["courses"] if c["course_code"] == "COS 201")
    assert any("carryover" in i for i in prog["prerequisite_issues"])


def test_strong_record_beats_weak_record():
    strong = [{"course_code": c, "score": 85} for c in ("COS 101", "VUA-CSC 107", "VUA-CSC 105")]
    weak = [{"course_code": c, "score": 38} for c in ("COS 101", "VUA-CSC 107", "VUA-CSC 105")]
    s = next(
        c
        for c in advise(strong, study_hours=15, attendance=0.95).json()["courses"]
        if c["course_code"] == "COS 102"
    )
    w = next(
        c
        for c in advise(weak, study_hours=3, attendance=0.5).json()["courses"]
        if c["course_code"] == "COS 102"
    )
    assert s["probabilities"]["Strong"] > w["probabilities"]["Strong"]
    assert s["probabilities"]["At Risk"] < w["probabilities"]["At Risk"]


def test_final_semester_has_no_next_courses():
    r = advise([{"course_code": "CSC 498", "score": 70}])
    assert r.status_code == 200
    assert r.json()["courses"] == []


def test_unknown_course_code_is_rejected():
    r = advise([{"course_code": "XYZ 999", "score": 60}])
    assert r.status_code == 422


def test_empty_results_are_rejected():
    assert advise([]).status_code == 422


def test_out_of_range_inputs_are_rejected():
    ok = [{"course_code": "COS 101", "score": 60}]
    assert advise(ok, attendance=1.4).status_code == 422
    assert advise(ok, jamb_score=900).status_code == 422
    assert advise([{"course_code": "COS 101", "score": 140}]).status_code == 422


def test_raw_predict_endpoint():
    payload = {
        "jamb_score": 230,
        "level": 300,
        "semester": 1,
        "units": 3,
        "is_elective": 0,
        "category": "Programming",
        "study_hours": 12,
        "attendance": 0.85,
        "prior_cgpa": 3.5,
        "prior_semester_gpa": 3.6,
        "prior_avg_score": 66,
        "courses_failed_so_far": 0,
        "courses_taken_so_far": 20,
        "category_avg_prior": 68,
        "has_category_history": 1,
        "prereq_avg_score": 70,
        "has_prereqs": 1,
    }
    r = client.post("/api/predict", json=payload)
    assert r.status_code == 200
    assert r.json()["predicted_band"] in ("At Risk", "Average", "Strong")


def test_feature_builder_matches_model_features():
    history = advisor.build_history([{"course_code": "COS 101", "score": 60}])
    course = advisor.get_courses().loc["COS 102"]
    feats = advisor.course_features(course, history, 230, 10, 0.8)
    assert set(feats) == set(advisor.get_metadata()["features"])


def test_grade_helpers():
    assert advisor.points_for(70) == 5
    assert advisor.points_for(49) == 2
    assert advisor.points_for(39) == 0
    assert advisor.letter_for(61) == "B"
