"""
train.py - Reproducible training script for the vehicle maintenance prediction pipeline.

Usage:
    python model/train.py

Outputs:
    model/vehicle_maintenance_pipeline.pkl  - Trained sklearn pipeline
    model/metrics.json                      - Evaluation metrics (accuracy, ROC-AUC, classification report)

Requirements:
    pip install pandas scikit-learn joblib kagglehub
"""

import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_PATH = SCRIPT_DIR / "vehicle_maintenance_pipeline.pkl"
METRICS_PATH = SCRIPT_DIR / "metrics.json"

# ---------------------------------------------------------------------------
# Feature configuration (mirrors prediction_service.py _MODEL_COLUMNS_FALLBACK)
# ---------------------------------------------------------------------------
NUMERIC_FEATURES = [
    "Mileage",
    "Reported_Issues",
    "Vehicle_Age",
    "Engine_Size",
    "Odometer_Reading",
    "Insurance_Premium",
    "Service_History",
    "Accident_History",
    "Fuel_Efficiency",
    "Days_Since_Service",
    "Days_Until_Warranty",
]

CATEGORICAL_FEATURES = [
    "Vehicle_Model",
    "Maintenance_History",
    "Fuel_Type",
    "Transmission_Type",
    "Owner_Type",
    "Tire_Condition",
    "Brake_Condition",
    "Battery_Status",
]

TARGET = "Need_Maintenance"

# ---------------------------------------------------------------------------
# Hyperparameters (tuned values from data_processing.ipynb)
# ---------------------------------------------------------------------------
RF_PARAMS = {
    "n_estimators": 100,
    "max_depth": None,
    "min_samples_split": 2,
    "min_samples_leaf": 1,
    "class_weight": "balanced",
    "random_state": 42,
    "n_jobs": -1,
}

CV_FOLDS = 5
TEST_SIZE = 0.2
RANDOM_STATE = 42


def load_data() -> pd.DataFrame:
    """Load the vehicle maintenance dataset via kagglehub."""
    try:
        import kagglehub
        from kagglehub import KaggleDatasetAdapter

        df = kagglehub.dataset_load(
            KaggleDatasetAdapter.PANDAS,
            "chavindudulaj/vehicle-maintenance-data",
            "vehicle_maintenance_data.csv",
        )
        print(f"Dataset loaded via kagglehub: {df.shape}")
        return df
    except Exception as e:
        raise RuntimeError(
            f"Failed to load dataset via kagglehub: {e}\n"
            "Ensure kagglehub is installed and Kaggle credentials are configured."
        ) from e


def preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Drop date columns that leak information and separate features from target.
    The columns Last_Service_Date and Warranty_Expiry_Date are dropped because
    they are raw dates; the model uses the derived numeric columns
    Days_Since_Service and Days_Until_Warranty instead.
    """
    drop_cols = [c for c in ["Last_Service_Date", "Warranty_Expiry_Date"] if c in df.columns]
    df = df.drop(columns=drop_cols)

    all_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    missing = [f for f in all_features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in dataset: {missing}")

    X = df[all_features]
    y = df[TARGET]
    return X, y


def build_pipeline() -> Pipeline:
    """Build the sklearn preprocessing + classifier pipeline."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", RandomForestClassifier(**RF_PARAMS)),
        ]
    )
    return pipeline


def evaluate(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Compute and return evaluation metrics on the held-out test set."""
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "accuracy": round(acc, 4),
        "roc_auc": round(roc_auc, 4),
        "classification_report": report,
        "confusion_matrix": cm,
    }
    return metrics


def cross_validate(pipeline: Pipeline, X: pd.DataFrame, y: pd.Series) -> dict:
    """Run stratified k-fold cross-validation and return mean/std scores."""
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    acc_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
    roc_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)

    return {
        "cv_folds": CV_FOLDS,
        "cv_accuracy_mean": round(float(np.mean(acc_scores)), 4),
        "cv_accuracy_std": round(float(np.std(acc_scores)), 4),
        "cv_roc_auc_mean": round(float(np.mean(roc_scores)), 4),
        "cv_roc_auc_std": round(float(np.std(roc_scores)), 4),
    }


def main():
    print("=== FleetAI Training Script ===\n")

    # 1. Load data
    df = load_data()

    # 2. Preprocess
    X, y = preprocess(df)
    print(f"Features: {X.shape[1]}  |  Samples: {X.shape[0]}")
    print(f"Class distribution:\n{y.value_counts().to_string()}\n")

    # 3. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    print(f"Train size: {len(X_train)}  |  Test size: {len(X_test)}\n")

    # 4. Build and train pipeline
    pipeline = build_pipeline()
    print("Training pipeline...")
    pipeline.fit(X_train, y_train)
    print("Training complete.\n")

    # 5. Evaluate on test set
    print("Evaluating on test set...")
    test_metrics = evaluate(pipeline, X_test, y_test)
    print(f"  Accuracy : {test_metrics['accuracy']}")
    print(f"  ROC-AUC  : {test_metrics['roc_auc']}\n")

    # 6. Cross-validation
    print(f"Running {CV_FOLDS}-fold cross-validation on full dataset...")
    cv_metrics = cross_validate(pipeline, X, y)
    print(f"  CV Accuracy : {cv_metrics['cv_accuracy_mean']} ± {cv_metrics['cv_accuracy_std']}")
    print(f"  CV ROC-AUC  : {cv_metrics['cv_roc_auc_mean']} ± {cv_metrics['cv_roc_auc_std']}\n")

    # 7. Save pipeline
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Pipeline saved to: {MODEL_PATH}")

    # 8. Save metrics
    all_metrics = {**test_metrics, **cv_metrics}
    with open(METRICS_PATH, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"Metrics saved to: {METRICS_PATH}\n")

    print("=== Done ===")


if __name__ == "__main__":
    main()
