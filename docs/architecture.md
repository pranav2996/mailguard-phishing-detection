# Architecture

```text
Browser (frontend on :5500)
       │ /api requests
       ▼
Spring Boot (:8080) ─── H2 local history
       │ REST /predict and /metrics
       ▼
Flask (:5000) ─── scikit-learn fitted pipeline
```

Only Java is exposed as the frontend's application API. Spring Boot validates a 50,000 character request, calls Flask with a bounded timeout, stores the structured response and a short preview, and returns the result. Python loads a joblib pipeline on first prediction, extracts visible phrase and URL indicators, and returns a classification with an explicitly labeled confidence type. URLs are parsed locally; no network requests are made to them.

The training workflow loads the two existing CSV schemas through explicit schema detection and label mapping. Normalized exact text duplicates are removed before a stratified train/test split. All learned transforms live in each scikit-learn pipeline and fit only on the train split. Reports include source-specific data quality counts and held-out metrics.
