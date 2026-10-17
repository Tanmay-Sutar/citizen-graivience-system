"""
train_model.py - Train the ML models for the Citizen Grievance System.

Trains TWO scikit-learn models:
  (a) TF-IDF + Logistic Regression -> category (Water / Road / Electricity)
  (b) TF-IDF + Logistic Regression -> priority (High / Medium / Low)

Reads data from data/grievance_dataset.csv (columns: complaint, category, priority).
Reports accuracy, precision, recall, F1, and confusion matrices for both models.
Saves everything with joblib to app/ml_models/:
  - category_model.joblib   (LogisticRegression)
  - priority_model.joblib   (LogisticRegression)
  - category_vectorizer.joblib  (TfidfVectorizer)
  - priority_vectorizer.joblib  (TfidfVectorizer)
  - label_encoders.joblib   (category and priority label lists)

To retrain with your own data, replace data/grievance_dataset.csv (keep the same
column names) and run: python train_model.py
"""
import os
import re
import sys
import csv
import joblib
import numpy as np

# NLTK stopwords (gracefully fall back to a built-in list if NLTK data is missing)
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    try:
        STOPWORDS = set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords")
        STOPWORDS = set(stopwords.words("english"))

    try:
        lemmatizer = WordNetLemmatizer()
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
    except LookupError:
        lemmatizer = None
except Exception:
    STOPWORDS = set("""a an the and or but if then of to in on at for with by from as is are was were
    be been being have has had do does did will would shall should may might can could this that these
    those it its i you he she we they me him her us them my your his our their what which who whom
    not no so such only own same than too very just about above after again against all am any because
    before between both during each few more most other some into through under until up down out off
    over here there when where why how all any both each few more most other some""".split())
    lemmatizer = None

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "data", "grievance_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "app", "ml_models")


def preprocess(text: str) -> str:
    """Lowercase, remove punctuation & stopwords, optional lemmatization."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)  # keep letters, digits, spaces
    tokens = [t for t in text.split() if t and t not in STOPWORDS]
    if lemmatizer is not None:
        tokens = [lemmatizer.lemmatize(t) for t in tokens]
    return " ".join(tokens)


def load_dataset():
    complaints, categories, priorities = [], [], []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            complaints.append(preprocess(row["complaint"].strip()))
            categories.append(row["category"].strip())
            priorities.append(row["priority"].strip())
    return complaints, categories, priorities


def train_and_evaluate(X, y, label_name):
    """Train a TF-IDF + Logistic Regression model, print metrics, return model + vectorizer."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)

    print("\n" + "=" * 60)
    print(f"  {label_name.upper()} MODEL EVALUATION")
    print("=" * 60)
    print(f"  Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"  Precision: {precision_score(y_test, y_pred, average='weighted', zero_division=0):.4f}")
    print(f"  Recall   : {recall_score(y_test, y_pred, average='weighted', zero_division=0):.4f}")
    print(f"  F1-score : {f1_score(y_test, y_pred, average='weighted', zero_division=0):.4f}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred, labels=sorted(set(y)))
    labels = sorted(set(y))
    print(f"    {'':>12} " + " ".join(f"{l[:8]:>10}" for l in labels))
    for i, row in enumerate(cm):
        print(f"    {labels[i][:12]:>12} " + " ".join(f"{v:>10}" for v in row))

    return model, vectorizer


def main():
    if not os.path.exists(DATASET_PATH):
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        print("Run data/generate_dataset.py first or place your own CSV there.")
        sys.exit(1)

    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Loading and preprocessing dataset...")
    complaints, categories, priorities = load_dataset()
    print(f"  Loaded {len(complaints)} complaints.")

    # --- Category model ---
    cat_model, cat_vec = train_and_evaluate(complaints, categories, "category")

    # --- Priority model ---
    pri_model, pri_vec = train_and_evaluate(complaints, priorities, "priority")

    # --- Save models ---
    joblib.dump(cat_model, os.path.join(MODEL_DIR, "category_model.joblib"))
    joblib.dump(cat_vec, os.path.join(MODEL_DIR, "category_vectorizer.joblib"))
    joblib.dump(pri_model, os.path.join(MODEL_DIR, "priority_model.joblib"))
    joblib.dump(pri_vec, os.path.join(MODEL_DIR, "priority_vectorizer.joblib"))

    label_encoders = {
        "categories": sorted(set(categories)),
        "priorities": sorted(set(priorities)),
    }
    joblib.dump(label_encoders, os.path.join(MODEL_DIR, "label_encoders.joblib"))

    print("\n" + "=" * 60)
    print(f"  Models saved to {MODEL_DIR}")
    print("=" * 60)
    print("  - category_model.joblib")
    print("  - category_vectorizer.joblib")
    print("  - priority_model.joblib")
    print("  - priority_vectorizer.joblib")
    print("  - label_encoders.joblib")
    print("\nDone.")


if __name__ == "__main__":
    main()
