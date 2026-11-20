# API reference

All frontend calls go to Spring Boot at `http://localhost:8080/api`.

## `POST /analyze`

Request: `{"emailText":"Subject: ...\\n\\nMessage body ..."}`. The value must be nonblank and no longer than 50,000 characters. The response contains `id`, `createdAt`, `classification` (`PHISHING` or `SAFE`), `confidence`, `confidenceType`, `riskLevel`, `keywords`, `urls`, `reasons`, and `features`. A service outage returns a JSON `error` message.

## Read endpoints

- `GET /history`: newest first; stored result fields plus a short `preview`.
- `GET /stats`: `total`, `phishing`, and `safe` history counts.
- `GET /metrics`: best model name, dataset inspection, split counts, and per-model held-out metrics.
- `GET /health`: Java status and nested Flask status.

Flask runs separately and offers `GET /health`, `POST /predict`, and `GET /metrics` for backend-to-backend integration.
