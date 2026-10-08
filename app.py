from pathlib import Path
import re
import joblib
import pandas as pd

from flask import Flask, jsonify, render_template, request
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "news_dataset.csv"
MODEL_PATH = BASE_DIR / "fake_news_model.pkl"

app = Flask(__name__)

def clean_text(text):
    text = str(text)
    text = re.sub(r"https?://\S+|www\.\S+", " URL ", text)
    text = re.sub(r"\S+@\S+", " EMAIL ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def build_model():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "news_dataset.csv was not found. Put your verified dataset beside app.py."
        )

    df = pd.read_csv(DATASET_PATH)

    if not {"text", "label"}.issubset(df.columns):
        raise ValueError("Dataset must contain 'text' and 'label' columns.")

    df = df[["text", "label"]].dropna()
    df["text"] = df["text"].map(clean_text)
    df["label"] = df["label"].astype(str).str.upper().str.strip()
    df = df[df["text"].str.len() >= 20]
    df = df[df["label"].isin(["REAL", "FAKE"])]
    df = df.drop_duplicates(subset=["text"])

    if len(df) < 100:
        raise ValueError(
            f"Dataset has only {len(df)} usable rows. Use at least 100 verified examples."
        )

    counts = df["label"].value_counts()
    if counts.get("REAL", 0) < 20 or counts.get("FAKE", 0) < 20:
        raise ValueError("Use at least 20 REAL and 20 FAKE examples.")

    x_train, x_test, y_train, y_test = train_test_split(
        df["text"],
        df["label"],
        test_size=0.20,
        random_state=42,
        stratify=df["label"],
    )

    vectorizer = FeatureUnion([
        ("word", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            max_df=0.98,
            max_features=120000,
        )),
        ("char", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
            min_df=2,
            max_features=80000,
        )),
    ])

    x_train_vec = vectorizer.fit_transform(x_train)

    base_model = LogisticRegression(
        C=2.0,
        max_iter=3000,
        class_weight="balanced",
        solver="liblinear",
        random_state=42,
    )

    model = CalibratedClassifierCV(base_model, method="sigmoid", cv=5)
    model.fit(x_train_vec, y_train)

    accuracy = accuracy_score(y_test, model.predict(vectorizer.transform(x_test)))

    package = {
        "vectorizer": vectorizer,
        "model": model,
        "accuracy": float(accuracy),
        "dataset_size": int(len(df)),
        "test_size": int(len(x_test)),
    }
    joblib.dump(package, MODEL_PATH)
    return package

def load_model():
    if MODEL_PATH.exists():
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            pass
    return build_model()

PACKAGE = None
MODEL_ERROR = None
try:
    PACKAGE = load_model()
except Exception as exc:
    MODEL_ERROR = str(exc)

@app.get("/")
def index():
    meta = {
        "ready": PACKAGE is not None,
        "accuracy": round(PACKAGE["accuracy"] * 100, 1) if PACKAGE else None,
        "dataset_size": PACKAGE["dataset_size"] if PACKAGE else None,
    }
    return render_template("index.html", meta=meta, error=MODEL_ERROR)

@app.post("/api/analyze")
def analyze():
    if PACKAGE is None:
        return jsonify({"error": MODEL_ERROR or "Model is not ready."}), 503

    body = request.get_json(silent=True) or {}
    text = clean_text(body.get("text", ""))

    if len(text) < 20:
        return jsonify({"error": "Enter at least 20 characters of news text."}), 400

    vector = PACKAGE["vectorizer"].transform([text])
    probabilities = PACKAGE["model"].predict_proba(vector)[0]
    classes = list(PACKAGE["model"].classes_)

    probs = {label: float(probabilities[i]) for i, label in enumerate(classes)}
    real = probs.get("REAL", 0.0)
    fake = probs.get("FAKE", 0.0)

    if max(real, fake) < 0.60:
        verdict = "UNCERTAIN"
        confidence = max(real, fake)
    elif real >= fake:
        verdict = "REAL"
        confidence = real
    else:
        verdict = "FAKE"
        confidence = fake

    return jsonify({
        "verdict": verdict,
        "confidence": round(confidence * 100, 1),
        "real_probability": round(real * 100, 1),
        "fake_probability": round(fake * 100, 1),
        "model_accuracy": round(PACKAGE["accuracy"] * 100, 1),
        "dataset_size": PACKAGE["dataset_size"],
    })

@app.post("/api/retrain")
def retrain():
    global PACKAGE, MODEL_ERROR
    try:
        PACKAGE = build_model()
        MODEL_ERROR = None
        return jsonify({
            "ok": True,
            "accuracy": round(PACKAGE["accuracy"] * 100, 1),
            "dataset_size": PACKAGE["dataset_size"],
        })
    except Exception as exc:
        MODEL_ERROR = str(exc)
        return jsonify({"error": MODEL_ERROR}), 400

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
