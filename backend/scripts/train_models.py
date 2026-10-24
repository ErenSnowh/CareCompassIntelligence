"""Train and evaluate lightweight triage models (care type + urgency).

Usage:
  python backend/scripts/train_models.py
  python backend/scripts/train_models.py --extra-data path/to/public.jsonl

The script uses scikit-learn TF-IDF (word + char n-grams) + LogisticRegression,
which is lightweight, fast, and robust for Hinglish transliteration.
It optionally merges additional public JSONL datasets in the same schema.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "triage_dataset.jsonl"
MODEL_DIR = ROOT / "backend" / "models"


def load_examples(paths):
    texts, care, urgency = [], [], []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                req = rec.get("request", {})
                resp = rec.get("response", {})
                text = req.get("user_input", "")
                ct = resp.get("care_type")
                ur = resp.get("urgency")
                if text and ct and ur:
                    texts.append(text)
                    care.append(ct)
                    urgency.append(ur)
    return texts, care, urgency


def build_pipeline():
    union = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 3), min_df=1, sublinear_tf=True)),
        ("char", TfidfVectorizer(ngram_range=(2, 5), analyzer="char_wb", min_df=1, sublinear_tf=True)),
    ])
    return Pipeline([
        ("features", union),
        ("clf", LogisticRegression(C=10.0, max_iter=3000, class_weight="balanced")),
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extra-data", nargs="*", default=[])
    args = parser.parse_args()

    paths = [DATASET] + [Path(p) for p in args.extra_data]
    texts, care_labels, urg_labels = load_examples(paths)
    print(f"Loaded {len(texts)} examples from {len(paths)} file(s).")

    X_train, X_test, ycare_train, ycare_test, yurg_train, yurg_test = train_test_split(
        texts, care_labels, urg_labels, test_size=0.2, random_state=42, stratify=care_labels
    )

    care_pipe = build_pipeline()
    urg_pipe = build_pipeline()

    # Cross-validation on training set
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    care_cv = cross_val_score(care_pipe, X_train, ycare_train, cv=cv, scoring="f1_macro")
    urg_cv = cross_val_score(urg_pipe, X_train, yurg_train, cv=cv, scoring="f1_macro")
    print(f"Care CV Macro-F1: {care_cv.mean():.4f} (+/- {care_cv.std():.4f})")
    print(f"Urgency CV Macro-F1: {urg_cv.mean():.4f} (+/- {urg_cv.std():.4f})")

    care_pipe.fit(X_train, ycare_train)
    urg_pipe.fit(X_train, yurg_train)

    care_pred = care_pipe.predict(X_test)
    urg_pred = urg_pipe.predict(X_test)
    print("Care accuracy:", accuracy_score(ycare_test, care_pred))
    print("Care Macro-F1:", f1_score(ycare_test, care_pred, average="macro"))
    print(classification_report(ycare_test, care_pred))
    print("Urgency accuracy:", accuracy_score(yurg_test, urg_pred))
    print("Urgency Macro-F1:", f1_score(yurg_test, urg_pred, average="macro"))
    print(classification_report(yurg_test, urg_pred))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(care_pipe, MODEL_DIR / "care_model.joblib")
    joblib.dump(urg_pipe, MODEL_DIR / "urgency_model.joblib")
    print(f"Saved models to {MODEL_DIR}")


if __name__ == "__main__":
    main()