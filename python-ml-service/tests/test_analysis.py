import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from security.keyword_detector import detect_keywords
from security.url_analyzer import analyze_urls
from security.risk_engine import summarize_risk
import app as flask_app

def test_keyword_categories():
    found = detect_keywords("Urgent: verify your account password. Wire transfer needed.")
    assert {"urgent", "credential_request", "financial_request"}.issubset(found)

def test_url_analysis_does_not_open_links():
    found = analyze_urls("Visit http://192.0.2.10/reset and https://bit.ly/x")
    assert len(found) == 2
    assert "IP address used as host" in found[0]["indicators"]
    assert "URL shortener domain" in found[1]["indicators"]

def test_malformed_url_is_reported_safely():
    found = analyze_urls("Open http://[bad-host")
    assert found and "Malformed URL" in found[0]["indicators"]

def test_risk_reasons_are_evidence_based():
    level, reasons = summarize_risk("SAFE", {"urgent": ["act now"]}, [])
    assert level == "MEDIUM"
    assert any("act now" in reason for reason in reasons)

def test_predict_rejects_empty_content():
    response = flask_app.app.test_client().post("/predict", json={"emailText": " "})
    assert response.status_code == 400

def test_predict_rejects_oversized_content():
    response = flask_app.app.test_client().post("/predict", json={"emailText": "x" * 50001})
    assert response.status_code == 413

def test_health_endpoint():
    response = flask_app.app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

def test_predict_with_saved_model():
    if not flask_app.ARTIFACT_PATH.exists():
        import pytest
        pytest.skip("Train the model before running the saved-model API check")
    flask_app._model = None
    response = flask_app.app.test_client().post("/predict", json={"emailText":"Urgent: verify your account at http://192.0.2.10/login"})
    assert response.status_code == 200
    result=response.get_json()
    assert result["classification"] in {"PHISHING","SAFE"}
    assert result["urls"][0]["host"] == "192.0.2.10"
