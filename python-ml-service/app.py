import json
import hmac
import os
from pathlib import Path
import joblib
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import ARTIFACT_PATH, MAX_EMAIL_CHARS
from data.preprocess import normalize_text
from security.keyword_detector import detect_keywords
from security.url_analyzer import analyze_urls
from security.risk_engine import summarize_risk

app=Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256_000
CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "http://localhost:8080,http://localhost:5500").split(",")}})

def model():
    global _model
    if _model is None: _model=joblib.load(ARTIFACT_PATH)
    return _model
_model=None
_model_error = None

# Load the committed inference artifact as the web service starts so health checks
# reveal corrupt or missing artifacts before the first user submits an email.
try:
    model()
except Exception as exc:
    _model_error = exc
    app.logger.exception("The saved phishing model could not be loaded during startup.")

@app.before_request
def protect_internal_prediction_api():
    if request.endpoint not in {"predict", "metrics"}:
        return None
    expected = os.getenv("ML_SERVICE_TOKEN", "")
    if expected and not hmac.compare_digest(request.headers.get("X-Mailguard-Token", ""), expected):
        return jsonify({"error": "Unauthorized service request."}), 401

@app.errorhandler(413)
def too_large(_): return jsonify({"error":"Email exceeds the 50,000 character limit."}),413

@app.get("/health")
def health():
    available = _model is not None and _model_error is None
    return jsonify({"status": "ok" if available else "unavailable", "model_available": available}), 200 if available else 503

@app.post("/predict")
def predict():
    body=request.get_json(silent=True) or {}
    content=body.get("emailText",body.get("text", ""))
    if not isinstance(content,str) or not content.strip(): return jsonify({"error":"Email content is required."}),400
    if len(content)>MAX_EMAIL_CHARS: return jsonify({"error":"Email exceeds the 50,000 character limit."}),413
    try:
        content=normalize_text(content)
        estimator=model(); prediction=estimator.predict([content])[0]
        classifier=estimator.named_steps["classifier"]
        confidence=None
        if hasattr(classifier,"predict_proba"):
            confidence=float(estimator.predict_proba([content])[0][list(classifier.classes_).index(prediction)])
        elif hasattr(classifier,"decision_function"):
            import math
            raw=float(estimator.decision_function([content])[0]); confidence=1/(1+math.exp(-min(30,abs(raw))))
        classification="PHISHING" if prediction=="phishing" else "SAFE"
        keywords=detect_keywords(content); urls=analyze_urls(content); risk,reasons=summarize_risk(classification,keywords,urls)
        return jsonify({"classification":classification,"confidence":round(confidence,4) if confidence is not None else None,"confidenceType":"uncalibrated_model_probability" if hasattr(classifier,"predict_proba") else "decision_score_transform" if confidence is not None else "unavailable","riskLevel":risk,"keywords":keywords,"urls":urls,"reasons":reasons,"features":{"emailLength":len(content),"wordCount":len(content.split()),"urlCount":len(urls)}})
    except FileNotFoundError: return jsonify({"error":"Model is not trained. Run python -m models.train first."}),503
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return jsonify({"error":"Prediction service could not analyze this email."}),500

@app.get("/metrics")
def metrics():
    path=Path(__file__).parent/"reports"/"evaluation.json"
    if not path.exists(): return jsonify({"error":"Evaluation report is not available. Train the model first."}),503
    return jsonify(json.loads(path.read_text(encoding="utf-8")))

if __name__=="__main__": app.run(host="127.0.0.1",port=int(os.getenv("PORT",5000)),debug=False)
