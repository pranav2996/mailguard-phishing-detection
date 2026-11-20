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

This repository includes the two original CSV files as supplied by the project owner. No upstream source or redistribution license is documented in the repository, and no `LICENSE` file is present. A local scan of `phishing_cleaned.csv` found 47,141 email-address matches in sender, 55,241 in receiver, and 38,134 in body (some messages repeat addresses); matches include public and organizational domains. Treat the data as potentially personal information and confirm source permissions and applicable privacy requirements before further redistribution. The project owner explicitly approved publishing the original CSVs for this repository. The generated `python-ml-service/data/processed/combined_emails.csv`, local H2 files, and Python/Java build outputs are not published.

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

### Live deployment

| Component | Public URL | Health check |
|---|---|---|
| Frontend | <https://mailguard-frontend-sfk7.onrender.com> | Open the homepage; static sites do not expose a separate health API. |
| Java API | <https://mailguard-api-q3o6.onrender.com> | <https://mailguard-api-q3o6.onrender.com/actuator/health> (Spring Actuator) and <https://mailguard-api-q3o6.onrender.com/api/health> (application and ML connectivity). |
| Python Flask API | <https://mailguard-ml.onrender.com> | <https://mailguard-ml.onrender.com/health> |

The frontend build sets its Java API base URL from the Render service URL. The browser calls Java; Java calls Flask and forwards the shared service token. The Flask prediction route is intended for Java-to-Flask calls, not direct browser use. The public service URLs were read from the deployed Render service dashboard for commit `c56e51e`.

To try the deployed app, open the frontend and use **Analyze email**. Submit one clearly suspicious sample (for example, an urgent account-verification message containing a fabricated URL such as `https://secure-bank-login.example.com/verify`) and one ordinary legitimate sample (for example, a meeting update with no request for credentials or payment). Review the classification, confidence, risk, URL and keyword indicators, and explanation. Open **Detection history** to confirm both analyses were saved, **Overview** to see updated counts, and **Performance** to inspect the model report. Predictions are model output and are not guaranteed ground truth; use fictional test messages and do not paste confidential email.

The deployed Java endpoints include `GET /api/health`, `POST /api/analyze` with `{"emailText":"..."}`, `GET /api/history`, `GET /api/stats`, and `GET /api/metrics`. A successful `/api/health` response reports Java status and Flask health; `/actuator/health` reports Spring service health. The Flask health endpoint is `GET /health`.

Live smoke test on 2026-11-20: two fictional messages submitted to the public Java `POST /api/analyze` endpoint returned saved record IDs and actual model results. The urgent credential-verification sample returned `PHISHING`, 0.5919 confidence, `HIGH` risk, one extracted URL, and credential-request/urgency indicators. The routine project-meeting sample returned `SAFE`, 0.6014 confidence, `LOW` risk, and no URL or keyword indicators. Confidence is uncalibrated model output. Automated GET checks for health, history, metrics, and the static homepage received Cloudflare challenge pages (HTTP 403) in the verification environment, so those GET responses and the interactive browser pages were not verified in that run.

H2 uses ephemeral in-memory storage on Render. Detection history is available while the Java instance remains running and is lost when it restarts, spins down, or redeploys. A persistent disk or durable database is not configured.

Render Free web services use 512 MB RAM and share 750 instance-hours per workspace per calendar month. A service idles down after 15 minutes without inbound traffic; the next request may wait about a minute for it to start. Free services can restart and have ephemeral filesystems, and usage limits can suspend them. Static sites are free and do not consume web-service instance-hours. See [Render's current Free plan limits](https://render.com/docs/free).
