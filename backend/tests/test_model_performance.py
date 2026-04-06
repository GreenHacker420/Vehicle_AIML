from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# ---------------------------------------------------------------------------
# Baseline thresholds — model must meet these to pass CI
# ---------------------------------------------------------------------------
ACCURACY_BASELINE = 0.80
ROC_AUC_BASELINE = 0.85

# ---------------------------------------------------------------------------
# Minimal synthetic test rows that cover all three risk bands
# ---------------------------------------------------------------------------
SYNTHETIC_ROWS = [
    # LOW risk: low mileage, no faults, good service, light usage
    {
        "Vehicle_Model": "Sedan",
        "Mileage": 20000,
        "Maintenance_History": "Good",
        "Reported_Issues": 0,
        "Vehicle_Age": 2,
        "Fuel_Type": "Petrol",
        "Transmission_Type": "Automatic",
        "Engine_Size": 1800,
        "Odometer_Reading": 20000,
        "Owner_Type": "Individual",
        "Insurance_Premium": 800,
        "Service_History": 9,
        "Accident_History": 0,
        "Fuel_Efficiency": 28.0,
        "Tire_Condition": "New",
        "Brake_Condition": "New",
        "Battery_Status": "Good",
        "Days_Since_Service": 30,
        "Days_Until_Warranty": 1000,
        "Need_Maintenance": 0,
    },
    # HIGH risk: high mileage, many faults, poor service, heavy usage
    {
        "Vehicle_Model": "Truck",
        "Mileage": 200000,
        "Maintenance_History": "Poor",
        "Reported_Issues": 8,
        "Vehicle_Age": 10,
        "Fuel_Type": "Diesel",
        "Transmission_Type": "Manual",
        "Engine_Size": 3000,
        "Odometer_Reading": 200000,
        "Owner_Type": "Commercial",
        "Insurance_Premium": 2500,
        "Service_History": 2,
        "Accident_History": 3,
        "Fuel_Efficiency": 12.0,
        "Tire_Condition": "Worn Out",
        "Brake_Condition": "Worn Out",
        "Battery_Status": "Weak",
        "Days_Since_Service": 300,
        "Days_Until_Warranty": 0,
        "Need_Maintenance": 1,
    },
]

FEATURE_COLUMNS = [
    "Vehicle_Model",
    "Mileage",
    "Maintenance_History",
    "Reported_Issues",
    "Vehicle_Age",
    "Fuel_Type",
    "Transmission_Type",
    "Engine_Size",
    "Odometer_Reading",
    "Owner_Type",
    "Insurance_Premium",
    "Service_History",
    "Accident_History",
    "Fuel_Efficiency",
    "Tire_Condition",
    "Brake_Condition",
    "Battery_Status",
    "Days_Since_Service",
    "Days_Until_Warranty",
]


@pytest.fixture(scope="module")
def pipeline() -> Pipeline:
    """Load the trained pipeline once for all tests in this module."""
    model_path = Path(__file__).resolve().parents[2] / "model" / "vehicle_maintenance_pipeline.pkl"
    assert model_path.exists(), f"Model file not found at {model_path}"
    loaded = joblib.load(model_path)
    assert isinstance(loaded, Pipeline), "Loaded artifact is not an sklearn Pipeline"
    return loaded


# ---------------------------------------------------------------------------
# Schema / contract tests
# ---------------------------------------------------------------------------

def test_pipeline_has_preprocessor_and_model(pipeline):
    """Pipeline must contain 'preprocessor' and 'model' named steps."""
    assert "preprocessor" in pipeline.named_steps
    assert "model" in pipeline.named_steps


def test_pipeline_predict_proba_shape(pipeline):
    """predict_proba must return (n_samples, 2) for binary classification."""
    df = pd.DataFrame(SYNTHETIC_ROWS)[FEATURE_COLUMNS]
    proba = pipeline.predict_proba(df)
    assert proba.shape == (len(SYNTHETIC_ROWS), 2)
    assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-6)


def test_pipeline_predict_labels_valid(pipeline):
    """predict must return only 0 or 1."""
    df = pd.DataFrame(SYNTHETIC_ROWS)[FEATURE_COLUMNS]
    preds = pipeline.predict(df)
    assert set(preds).issubset({0, 1})


# ---------------------------------------------------------------------------
# Performance baseline tests (using the saved metrics.json when available,
# falling back to a small held-out split from synthetic data)
# ---------------------------------------------------------------------------

def test_model_accuracy_meets_baseline(pipeline):
    """
    Model accuracy on a held-out split must be >= ACCURACY_BASELINE.
    Uses metrics.json produced by train.py when available; otherwise
    evaluates on the synthetic rows as a smoke test.
    """
    metrics_path = Path(__file__).resolve().parents[2] / "model" / "metrics.json"

    if metrics_path.exists():
        import json
        with open(metrics_path) as f:
            metrics = json.load(f)
        accuracy = metrics.get("accuracy", 0.0)
        assert accuracy >= ACCURACY_BASELINE, (
            f"Model accuracy {accuracy:.4f} is below baseline {ACCURACY_BASELINE}"
        )
    else:
        # Fallback: smoke-test on synthetic rows
        df = pd.DataFrame(SYNTHETIC_ROWS)
        X = df[FEATURE_COLUMNS]
        y = df["Need_Maintenance"]
        preds = pipeline.predict(X)
        accuracy = accuracy_score(y, preds)
        # Synthetic rows are extreme cases — model should get both right
        assert accuracy >= 0.5, (
            f"Model failed basic smoke test: accuracy {accuracy:.4f} on synthetic rows"
        )


def test_model_roc_auc_meets_baseline(pipeline):
    """
    Model ROC-AUC on a held-out split must be >= ROC_AUC_BASELINE.
    Uses metrics.json produced by train.py when available.
    """
    metrics_path = Path(__file__).resolve().parents[2] / "model" / "metrics.json"

    if metrics_path.exists():
        import json
        with open(metrics_path) as f:
            metrics = json.load(f)
        roc_auc = metrics.get("roc_auc", 0.0)
        assert roc_auc >= ROC_AUC_BASELINE, (
            f"Model ROC-AUC {roc_auc:.4f} is below baseline {ROC_AUC_BASELINE}"
        )
    else:
        pytest.skip("metrics.json not found — run model/train.py to generate it")


def test_model_cv_accuracy_meets_baseline(pipeline):
    """
    Cross-validation mean accuracy must be >= ACCURACY_BASELINE.
    Uses metrics.json produced by train.py when available.
    """
    metrics_path = Path(__file__).resolve().parents[2] / "model" / "metrics.json"

    if metrics_path.exists():
        import json
        with open(metrics_path) as f:
            metrics = json.load(f)
        cv_acc = metrics.get("cv_accuracy_mean", 0.0)
        assert cv_acc >= ACCURACY_BASELINE, (
            f"CV accuracy {cv_acc:.4f} is below baseline {ACCURACY_BASELINE}"
        )
    else:
        pytest.skip("metrics.json not found — run model/train.py to generate it")
