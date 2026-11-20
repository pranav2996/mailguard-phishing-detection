from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATASETS = [ROOT / "phishing_cleaned.csv", ROOT / "spam.csv"]
ARTIFACT_DIR = Path(os.getenv("MODEL_DIR", Path(__file__).parent / "models" / "saved"))
ARTIFACT_PATH = ARTIFACT_DIR / "phishing_model.joblib"
MAX_EMAIL_CHARS = 50_000
