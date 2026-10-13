# Academic Advisor System

A web app that predicts how a student will perform in next semester's Computer Science
courses (At Risk, Average or Strong) and gives advice on prerequisites, study habits and
elective choice.

- **Model:** scikit-learn pipeline trained on Google Colab, saved as `models/advisor_model.pkl`
- **Backend:** FastAPI (`app/`)
- **Frontend:** single page in `app/static/index.html`
- **Data:** synthetic, generated from the 2026/2027 CS course allocation (`scripts/generate_dataset.py`)

## Project layout

```
app/            FastAPI app, advisor logic, schemas, web page
data/           courses.csv (curriculum) and the generated dataset tables
models/         advisor_model.pkl and model_metadata.json
notebooks/      train_model.ipynb (run on Colab)
scripts/        generate_dataset.py
tests/          pytest suite for the API and the advisor rules
```

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 for the app and http://127.0.0.1:8000/docs for the API docs.

## Test

```bash
pytest
```

## Retrain the model

1. Regenerate data if needed: `python scripts/generate_dataset.py --students 1000 --seed 42 --out data`
2. Open `notebooks/train_model.ipynb` in Google Colab and run all cells.
3. Download `advisor_model.pkl` and `model_metadata.json` into `models/`.
4. Set `scikit-learn==<version printed by the notebook>` in `requirements.txt`.

## How it works

1. The student enters a JAMB score, study hours, attendance and the results they already have.
2. The app works out their CGPA, last semester's GPA, category averages and prerequisite scores.
3. For each course offered next semester it asks the model for At Risk / Average / Strong probabilities.
4. Plain rules add prerequisite checks, watch points, a load check and an elective suggestion.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | model name, classes, metrics |
| GET | `/api/courses` | the course catalog |
| GET | `/api/sample` | a random synthetic student for demos |
| POST | `/api/advise` | advice for next semester |
| POST | `/api/predict` | raw model features in, predicted band out |
