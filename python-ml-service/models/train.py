"""Train/evaluate four models using both supplied CSV files."""
import json
import sys
import shutil
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score, classification_report, ConfusionMatrixDisplay, RocCurveDisplay
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.svm import LinearSVC
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DATASETS, ARTIFACT_DIR, ARTIFACT_PATH
from data.dataset_loader import load_datasets
from data.feature_extraction import TextSignals

def pipeline(model):
    return Pipeline([("features", FeatureUnion([("tfidf", TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1,2), max_features=60_000, min_df=2, sublinear_tf=True)), ("signals", TextSignals())])), ("classifier", model)])

def score_for_roc(model, X):
    clf=model.named_steps["classifier"]
    if hasattr(clf,"predict_proba"): return model.predict_proba(X)[:, list(clf.classes_).index("phishing")]
    if hasattr(clf,"decision_function"):
        scores=model.decision_function(X)
        return scores if list(clf.classes_)[-1] == "phishing" else -scores
    return None

def train():
    print("Loading and validating the two supplied CSV files…", flush=True)
    data, datasets, duplicate_count = load_datasets(DATASETS)
    print(f"Loaded {len(data)} unique text records; preparing stratified split…", flush=True)
    processed_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "combined_emails.csv"
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(processed_path, index=False, encoding="utf-8")
    X_train, X_test, y_train, y_test = train_test_split(data.text, data.label, test_size=0.2, random_state=42, stratify=data.label)
    models={"Multinomial Naive Bayes":MultinomialNB(alpha=0.35), "Logistic Regression":LogisticRegression(max_iter=300, class_weight="balanced", solver="liblinear", tol=1e-3), "Random Forest":RandomForestClassifier(n_estimators=60, max_depth=30, min_samples_leaf=2, class_weight="balanced_subsample", n_jobs=4, random_state=42), "Linear SVM":LinearSVC(C=1.0, class_weight="balanced", max_iter=500, tol=1e-2, random_state=42)}
    reports={}; fitted={}; roc_data={}
    for name, estimator in models.items():
        print(f"Training {name}…", flush=True)
        model=pipeline(estimator); model.fit(X_train, y_train); pred=model.predict(X_test)
        metrics={"accuracy":accuracy_score(y_test,pred), "precision":precision_score(y_test,pred,pos_label="phishing",zero_division=0), "recall":recall_score(y_test,pred,pos_label="phishing",zero_division=0), "f1":f1_score(y_test,pred,pos_label="phishing",zero_division=0), "macro_f1":f1_score(y_test,pred,average="macro",zero_division=0), "confusion_matrix":confusion_matrix(y_test,pred,labels=["safe","phishing"]).tolist(), "classification_report":classification_report(y_test,pred,output_dict=True,zero_division=0)}
        scores=score_for_roc(model,X_test)
        if scores is not None:
            metrics["roc_auc"]=roc_auc_score((y_test=="phishing").astype(int),scores)
            roc_data[name]=scores
        reports[name]=metrics; fitted[name]=model
        print(f"{name}: F1={metrics['f1']:.4f}, recall={metrics['recall']:.4f}, AUC={metrics.get('roc_auc',float('nan')):.4f}",flush=True)
    best_name=max(reports, key=lambda k:(reports[k]["macro_f1"], reports[k]["recall"]))
    ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)
    joblib.dump(fitted[best_name],ARTIFACT_PATH)
    metadata={"best_model":best_name,"selected_by":"macro F1, then phishing recall","label_order":["safe","phishing"],"train_rows":len(X_train),"test_rows":len(X_test),"total_unique_rows":len(data),"duplicates_removed":duplicate_count,"dataset_report":datasets,"metrics":reports}
    (ARTIFACT_DIR/"model_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    report_dir=Path(__file__).resolve().parents[1]/"reports"; report_dir.mkdir(exist_ok=True)
    (report_dir/"evaluation.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    fig,axes=plt.subplots(1,len(models),figsize=(4*len(models),4))
    for ax,(name,metrics) in zip(axes, reports.items()):
        ConfusionMatrixDisplay(np.array(metrics["confusion_matrix"]),display_labels=["Safe","Phishing"]).plot(ax=ax,colorbar=False); ax.set_title(name)
    fig.tight_layout(); fig.savefig(report_dir/"confusion_matrices.png",dpi=150); plt.close(fig)
    if roc_data:
        fig,ax=plt.subplots(figsize=(7,6))
        for name,scores in roc_data.items(): RocCurveDisplay.from_predictions((y_test=="phishing").astype(int),scores,name=name,ax=ax)
        fig.tight_layout(); fig.savefig(report_dir/"roc_curves.png",dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,4)); data.label.value_counts().reindex(["safe","phishing"]).plot.bar(ax=ax,color=["#21b68a","#f25f5c"]); ax.set_title("Combined class distribution"); ax.set_ylabel("Emails"); fig.tight_layout(); fig.savefig(report_dir/"class_distribution.png",dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4)); ax.bar(list(reports),[v["f1"] for v in reports.values()],color="#345ef0"); ax.set_ylabel("Phishing F1"); ax.tick_params(axis="x",rotation=18); fig.tight_layout(); fig.savefig(report_dir/"model_comparison.png",dpi=150); plt.close(fig)
    asset_dir=Path(__file__).resolve().parents[2]/"frontend"/"assets"; asset_dir.mkdir(parents=True,exist_ok=True)
    for name in ("roc_curves.png","class_distribution.png"):
        if (report_dir/name).exists(): shutil.copy2(report_dir/name,asset_dir/name)
    print(f"Best model: {best_name}; saved to {ARTIFACT_PATH}",flush=True)
    return metadata

if __name__=="__main__": train()
