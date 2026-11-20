# Mailguard phishing email detection

A local educational email inspection app. The browser calls the Java Spring Boot API; Java calls the Python Flask service for actual scikit-learn predictions and persists results to H2. The app never visits or opens a URL submitted in message text.

## What is included

- Python dataset loader that inspects and maps both original CSV datasets without modifying them.
- Four comparable classifiers (Multinomial Naive Bayes, Logistic Regression, Random Forest, and Linear SVM), TF-IDF text features, and message/URL indicators.
- Flask prediction, health, and evaluation APIs; keyword and URL analysis.
- Spring Boot validation, Flask integration, H2 history, dashboard statistics, and metrics endpoints.
- Responsive browser dashboard for analysis, history, model evaluation, and project information.

## Existing datasets

| File | Observed shape | Schema / label mapping |
|---|---:|---|
| `phishing_cleaned.csv` | 53,449 records | `subject`, `sender`, `receiver`, `body`, `urls`, `date`, `label`; label `1` → phishing, `0` → safe. Text uses subject, sender, body, and URL fields. |
| `spam.csv` | 5,572 records | `Category`, `Message`; `spam` → phishing-like, `ham` → safe. |

Observed label counts: `phishing_cleaned.csv` has 27,530 label-1 and 25,919 label-0 records. `spam.csv` has 747 spam and 4,825 ham records. These label names are normalized for the shared binary workflow; SMS spam is only a proxy for phishing, which can affect generalization. Original CSV files remain untouched. The loader reports columns, missing-cell totals, empty/invalid records, whole-row duplicates, usable labels, and per-file class counts whenever training runs. It concatenates the datasets, removes exact normalized text duplicates across sources, then uses a stratified 80/20 split to reduce duplicate leakage. `model_metadata.json` and `python-ml-service/reports/evaluation.json` capture the resulting counts and metrics.

## Requirements

- Python 3.10+ (3.12 recommended), pip
- Java 17+
- Internet access for the first Maven Wrapper launch and dependency install
- A browser

## Install and run (PowerShell)

From the project root:

```powershell
$python = "$env:LOCALAPPDATA\Python\bin\python.exe"
& $python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r python-ml-service\requirements.txt
& .\.venv\Scripts\python.exe python-ml-service\models\train.py
```

The script compares the four classifiers on one held-out stratified test split and selects by macro F1, then phishing recall. It writes the normalized, deduplicated rows to `python-ml-service/data/processed/combined_emails.csv` without altering either source CSV, saves the fitted pipeline to `python-ml-service/models/saved/phishing_model.joblib`, metadata to `python-ml-service/models/saved/model_metadata.json`, and evaluation JSON/PNG charts to `python-ml-service/reports/`. Train once before starting the services.

Actual held-out results from the current run (11,709 test records):

| Model | Accuracy | Phishing precision | Phishing recall | Phishing F1 | Macro F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Multinomial Naive Bayes | 65.51% | 76.20% | 41.04% | 53.35% | 63.00% | 0.6546 |
| Logistic Regression | 81.04% | 83.63% | 75.28% | 79.23% | 80.90% | 0.8481 |
| Random Forest (selected) | 97.29% | 99.35% | 94.99% | 97.12% | 97.28% | 0.9974 |
| Linear SVM | 64.93% | 59.14% | 87.43% | 70.55% | 63.61% | 0.6652 |

The Linear SVM emitted a convergence warning at the configured iteration limit, so its scores are a limited baseline. The selected Random Forest did not emit that warning. These random held-out scores should be interpreted cautiously: the data combines email and short-message sources, and the short-message spam labels are only phishing-like proxies.

Start Flask in one terminal:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "python-ml-service"
& .\.venv\Scripts\python.exe python-ml-service\app.py
```

Start Spring Boot in another terminal:

```powershell
cd java-backend
.\mvnw.cmd spring-boot:run
```

Serve the frontend in a third terminal from the project root:

```powershell
& .\.venv\Scripts\python.exe -m http.server 5500 --directory frontend
```

Open <http://localhost:5500>. Services default to Python `127.0.0.1:5000`, Java `localhost:8080`, and frontend `localhost:5500`. Set `ML_SERVICE_URL`, `PORT`, `DB_URL`, `DB_USER`, `DB_PASSWORD`, or `CORS_ORIGINS` to override defaults. The file-backed H2 database is created at `java-backend/data/phishing`.

## API

Frontend-facing Java endpoints:

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/analyze` | Accepts `{ "emailText": "..." }`, returns model result and stores history. Maximum length 50,000 characters. |
| GET | `/api/history` | Newest detections first. |
| GET | `/api/stats` | Total, phishing, and safe detection counts. |
| GET | `/api/metrics` | Training report from Python. |
| GET | `/api/health` | Java and Flask availability. |

Flask service endpoints (internal to the browser-facing architecture): `GET /health`, `POST /predict` with `{ "emailText": "..." }`, and `GET /metrics`. The prediction includes `classification`, confidence and its type, risk level, keyword groups, extracted URLs, visible indicators, reasons, and basic message features. Linear SVM confidence is explicitly a transformed decision score, not a calibrated probability.

## Tests

Run Python checks from the project root:

```powershell
$env:PYTHONPATH = "python-ml-service"
.\.venv\Scripts\python.exe -m pytest -q python-ml-service\tests
```

Run Java checks:

```powershell
cd java-backend
.\mvnw.cmd test
```

The Python suite covers keyword rules, IP/shortener and malformed URLs, empty and oversized requests, Flask health, and prediction using the saved model. Java tests cover request validation, H2 history persistence, and Java service mapping of a Python prediction response. Frontend scripts were checked with `node --check`; the running static server returns the app at port 5500.

## Model and interpretation notes

TF-IDF word unigrams/bigrams and deterministic numeric signals are fit inside each model pipeline. Naive Bayes, logistic regression, random forest, and linear SVM are evaluated using accuracy, phishing precision/recall/F1, macro F1, confusion matrix, and ROC-AUC when decision scores are available. The selected classifier is based on macro F1, with phishing recall as tie-break. Displayed model confidence is uncalibrated. URL checks describe formatting (for example, an IP host or a known shortener) and do not determine reputation. Keyword rules and model explanations report visible indicators without inventing threat intelligence.

## Troubleshooting

- **No model / 503 from Flask:** activate the venv, install `python-ml-service\requirements.txt`, then run `python python-ml-service\models\train.py`.
- **Java reports ML service unavailable:** start Flask and confirm <http://127.0.0.1:5000/health>.
- **Frontend cannot reach Java:** run Spring Boot and open the site from `http://localhost:5500` or `http://127.0.0.1:5500` (the configured CORS origins).
- **Python is installed elsewhere:** set `$python` to its `python.exe` path before the venv creation step.
- H2 data is local and append-only for this app; stop Java before manually removing its database files.

## Layout

`python-ml-service/` contains data handling, training, security analysis, Flask API, and reports. `java-backend/` contains the Spring Boot API and H2 persistence. `frontend/` contains the responsive UI. `docs/` contains architecture, dataset, and endpoint notes. The original dataset files are at the repository root.

## Dataset distribution note

This repository includes the two original CSV files as supplied by the project owner. The provided project files do not document their upstream source or redistribution license; verify those terms before redistributing the repository. The phishing CSV includes sender and receiver fields with email-like values. The generated `python-ml-service/data/processed/combined_emails.csv`, local H2 files, and Python/Java build outputs are not published.

## Deploy to Render Free

The root `render.yaml` defines three free resources: a static frontend, a Flask/Gunicorn ML API, and a Dockerized Spring Boot API. It pins the Python service to the dependency versions used to serialize the checked-in Random Forest model. The model file is included so deployment does not retrain or modify either CSV.

Deploy from the existing GitHub repository by selecting **New → Blueprint** in Render and choosing `render.yaml`. All dynamic services in the Blueprint explicitly use the `free` plan; the frontend is a free static site. Do not attach a paid disk or database. The Java-to-Flask token is generated by Render and referenced from the API service; it is not stored in the repository. The frontend build writes its API base from `JAVA_API_URL`; local builds default to `http://localhost:8080/api`.

The Blueprint sets these runtime values:

| Variable | Service | Purpose |
|---|---|---|
| `JAVA_API_URL` | Frontend build | Render URL for the Java API; the build adds `/api`. |
| `ML_SERVICE_URL` | Java | Render URL for Flask. |
| `ML_SERVICE_TOKEN` | Java and Flask | Render-generated shared token for Java-to-Flask prediction and metrics calls. |
| `CORS_ORIGINS` | Java and Flask | The deployed frontend URL. |
| `ML_TIMEOUT_MS` | Java | 120-second timeout to allow for a sleeping Flask service to start. |
| `DB_URL` | Java | In-memory H2 database on Render. |
| `H2_CONSOLE_ENABLED` | Java | Disabled in the public deployment. |
| `PORT` | Web services | Supplied by Render; servers bind to `0.0.0.0`. |
| `PYTHON_VERSION` | Flask | Pinned to the model's current Python minor release. |
| `SPRING_PROFILES_ACTIVE` | Java | Render profile marker. |

Render Free web services have 512 MB RAM each and share 750 instance-hours per workspace each month. They spin down after 15 idle minutes; the first request can take about a minute to warm a service. If both backend services ran continuously, they would use the shared allowance in about 15.6 days. Static sites are free and do not use web-service instance-hours. See [Render's free plan limits](https://render.com/docs/free).

H2 uses ephemeral in-memory storage on Render. Detection history is available while the Java instance remains running and is lost when it restarts, spins down, or redeploys. A persistent disk or durable database would require a different service plan or storage arrangement and is intentionally not configured.

The live frontend, Java API, and Flask API URLs will be recorded here after the Blueprint deployment is created and verified.
