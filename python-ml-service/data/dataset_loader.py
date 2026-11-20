"""Load the two original datasets without modifying them."""
from pathlib import Path
import re
import pandas as pd
from data.preprocess import normalize_text

def normalize_label(value):
    value = str(value).strip().lower()
    if value in {"1", "spam", "phishing", "phish", "malicious", "fraud", "1.0"}:
        return "phishing"
    if value in {"0", "ham", "safe", "legitimate", "legit", "benign", "0.0"}:
        return "safe"
    return None

def load_datasets(paths):
    frames, report = [], []
    for path in map(Path, paths):
        if not path.exists():
            report.append({"file": path.name, "status": "missing", "rows": 0})
            continue
        df = pd.read_csv(path, encoding="utf-8", encoding_errors="replace", low_memory=False)
        cols = {str(c).strip().lower(): c for c in df.columns}
        if "label" in cols and "body" in cols:
            text_cols = [cols[c] for c in ("subject", "sender", "body", "urls") if c in cols]
            raw_labels = df[cols["label"]]
        elif "category" in cols and "message" in cols:
            text_cols, raw_labels = [cols["message"]], df[cols["category"]]
        else:
            report.append({"file": path.name, "status": "unsupported schema", "columns": list(df.columns), "rows": len(df)})
            continue
        text = df[text_cols].fillna("").astype(str).agg(" ".join, axis=1).map(normalize_text)
        labels = raw_labels.map(normalize_label)
        valid = text.ne("") & labels.notna()
        clean = pd.DataFrame({"text": text[valid], "label": labels[valid], "source": path.name})
        report.append({"file": path.name, "status": "loaded", "columns": list(df.columns), "rows": len(df), "usable": len(clean), "missing_cells": int(df.isna().sum().sum()), "duplicates": int(df.duplicated().sum()), "label_counts": labels[valid].value_counts().to_dict()})
        frames.append(clean)
    if not frames:
        raise ValueError("No supported labeled datasets were found.")
    data = pd.concat(frames, ignore_index=True)
    before = len(data)
    data["normalized"] = data.text.str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    data = data.drop_duplicates("normalized").drop(columns="normalized").reset_index(drop=True)
    return data, report, before - len(data)
