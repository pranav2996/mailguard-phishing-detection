"""Stable, serializable engineered message feature transformer."""
import re
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin

class TextSignals(BaseEstimator, TransformerMixin):
    """Compact numeric message and URL indicators, shared by training and inference."""
    url_re = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
    patterns = [r"urgent|immediately|act now|expires today", r"password|verify your account|login credentials|security code", r"wire transfer|bank account|credit card|payment details", r"account suspended|you have won|legal action"]
    def fit(self, X, y=None): return self
    def transform(self, X):
        rows=[]
        for raw in X:
            t=str(raw); low=t.lower(); urls=self.url_re.findall(t)
            rows.append([len(t), len(t.split()), len(urls), sum(map(len,urls)), sum(bool(re.search(p,low)) for p in self.patterns), sum(c in t for c in "@#$%!?=:/"), int("http://" in low), int("https://" in low), sum(bool(re.search(r"https?://\d{1,3}(?:\.\d{1,3}){3}",u,re.I)) for u in urls), sum(len(u)>100 for u in urls)])
        return csr_matrix(np.asarray(rows, dtype=np.float32))
