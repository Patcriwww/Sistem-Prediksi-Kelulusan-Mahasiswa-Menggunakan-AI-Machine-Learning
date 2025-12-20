# train_model_80_10_10_sigmoid.py

import warnings
warnings.filterwarnings("ignore")

import os
import json
import pandas as pd

from joblib import dump
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix

RANDOM_STATE = 42

DATA_PATH = "dataset_kelulusan_mahasiswa.csv"
OUTPUT_MODEL = "model_kelulusan.joblib"
SUMMARY_JSON = "train_summary_80_10_10_sigmoid.json"

FEATURES = ["ipk", "sks_lulus", "presensi", "mengulang"]
TARGET = "lulus_tepat_waktu"


# -----------------------
# Utilities
# -----------------------
def load_data(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found: {path}")
    return pd.read_csv(path)


def prepare_features(df):
    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    X = df[FEATURES].copy()
    y = df[TARGET].astype(int)

    for col in FEATURES:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    return X, y


def build_pipeline():
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("clf", RandomForestClassifier(
            random_state=RANDOM_STATE,
            n_jobs=-1
        ))
    ])


def evaluate(model, X, y, label):
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]

    acc = accuracy_score(y, y_pred)
    auc = roc_auc_score(y, y_prob)

    print(f"\n[{label}] Accuracy : {acc:.4f}")
    print(f"[{label}] ROC AUC  : {auc:.4f}")
    print(f"[{label}] Report:\n{classification_report(y, y_pred, digits=4)}")
    print(f"[{label}] Confusion Matrix:\n{confusion_matrix(y, y_pred)}")

    return {"accuracy": acc, "roc_auc": auc}


# -----------------------
# Main
# -----------------------
def main():
    print("Loading dataset...")
    df = load_data(DATA_PATH)
    X, y = prepare_features(df)

    # 80 / 10 / 10 split
    X_tmp, X_test, y_tmp, y_test = train_test_split(
        X, y, test_size=0.10, stratify=y, random_state=RANDOM_STATE
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp,
        test_size=0.10 / 0.90,
        stratify=y_tmp,
        random_state=RANDOM_STATE
    )

    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    pipe = build_pipeline()

    print("\nTraining + Hyperparameter Search...")
    param_dist = {
        "clf__n_estimators": [100, 200, 400],
        "clf__max_depth": [5, 8, None],
        "clf__min_samples_split": [2, 4, 6],
        "clf__min_samples_leaf": [1, 2, 3],
        "clf__class_weight": [None, "balanced"]
    }

    rs = RandomizedSearchCV(
        pipe,
        param_dist,
        n_iter=20,
        scoring="roc_auc",
        cv=4,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1
    )

    rs.fit(X_train, y_train)
    best_model = rs.best_estimator_

    print("Best params:", rs.best_params_)

    print("\nValidation (before calibration)")
    val_uncal = evaluate(best_model, X_val, y_val, "VAL-Uncalibrated")

    # -----------------------
    # SIGMOID CALIBRATION
    # -----------------------
    print("\nApplying SIGMOID calibration (using VAL)...")
    calibrated = CalibratedClassifierCV(
        best_model,
        method="sigmoid",
        cv="prefit"
    )
    calibrated.fit(X_val, y_val)

    print("\nValidation (after calibration)")
    val_cal = evaluate(calibrated, X_val, y_val, "VAL-Calibrated")

    print("\nFinal Test Evaluation")
    test_cal = evaluate(calibrated, X_test, y_test, "TEST-Calibrated")

    # Save model
    dump(calibrated, OUTPUT_MODEL)
    print(f"\nModel saved to: {OUTPUT_MODEL}")

    # Save summary
    summary = {
        "features": FEATURES,
        "split": {"train": 0.8, "val": 0.1, "test": 0.1},
        "best_params": rs.best_params_,
        "metrics": {
            "val_uncalibrated": val_uncal,
            "val_calibrated": val_cal,
            "test_calibrated": test_cal
        },
        "model_path": OUTPUT_MODEL
    }

    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary saved to: {SUMMARY_JSON}")


if __name__ == "__main__":
    main()
