"""Tests for validation.py, using the real input_schema.json, sample_batch.csv and model."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from validation import predict_segment, validate_input  # noqa: E402

SCHEMA = json.loads((REPO_ROOT / "input_schema.json").read_text())
FEATURES = SCHEMA["features"]
SAMPLE_ROWS = pd.read_csv(REPO_ROOT / "sample_batch.csv").to_dict("records")

# A customer that passes validation; tests change one field at a time.
VALID = {
    "age": 30,
    "gender": "Female",
    "city": "Lahore",
    "monthly_income": 85000.0,
    "avg_balance": 40000.0,
    "monthly_transactions": 20,
    "monthly_logins": 10,
    "ticket_count": 1,
}


def with_(**changes):
    return {**VALID, **changes}


def test_valid_customer_has_no_errors():
    assert validate_input(VALID, FEATURES) == []


# --- sample_batch.csv --------------------------------------------------------

def test_sample_batch_has_expected_rows():
    assert len(SAMPLE_ROWS) == 7


@pytest.mark.parametrize("index", range(6))
def test_sample_batch_valid_rows(index):
    assert validate_input(SAMPLE_ROWS[index], FEATURES) == []


def test_sample_batch_last_row_is_deliberately_invalid():
    # Row 7 (age -5, gender Other, city Paris) is the bad example for the app's batch tab.
    assert validate_input(SAMPLE_ROWS[6], FEATURES) == [
        "age: -5 is outside the allowed range 18 to 100",
        "gender: 'Other' is not allowed. Choose from ['Male', 'Female']",
        "city: 'Paris' is not allowed. Choose from "
        "['Islamabad', 'Karachi', 'Lahore', 'Peshawar', 'Quetta']",
    ]


# --- presence ----------------------------------------------------------------

def test_missing_required_feature():
    customer = dict(VALID)
    del customer["city"]
    assert validate_input(customer, FEATURES) == ["Missing required feature: city"]


def test_unexpected_extra_feature():
    assert validate_input(with_(customer_id=42), FEATURES) == ["Unexpected feature: customer_id"]


# --- empty values ------------------------------------------------------------

@pytest.mark.parametrize("empty", [None, float("nan"), np.nan], ids=["None", "float-nan", "np-nan"])
@pytest.mark.parametrize("name", ["age", "monthly_income", "gender"])
def test_empty_value(name, empty):
    assert validate_input(with_(**{name: empty}), FEATURES) == [f"{name}: value is empty"]


# --- categories --------------------------------------------------------------

@pytest.mark.parametrize("name,value", [("gender", "Other"), ("city", "Paris"), ("city", "lahore")])
def test_category_not_allowed(name, value):
    errors = validate_input(with_(**{name: value}), FEATURES)
    assert errors == [f"{name}: '{value}' is not allowed. Choose from {FEATURES[name]['allowed']}"]


# --- numeric types -----------------------------------------------------------

@pytest.mark.parametrize("name", ["age", "monthly_income"])
@pytest.mark.parametrize("value", ["30", "abc", [30]], ids=["numeric-string", "text", "list"])
def test_non_number_rejected(name, value):
    assert validate_input(with_(**{name: value}), FEATURES) == [
        f"{name}: must be a number, got '{value}'"
    ]


@pytest.mark.parametrize("name", ["age", "monthly_income", "ticket_count"])
@pytest.mark.parametrize("value", [True, False])
def test_bool_rejected_as_number(name, value):
    assert validate_input(with_(**{name: value}), FEATURES) == [
        f"{name}: must be a number, got '{value}'"
    ]


def test_int_feature_rejects_non_whole_float():
    assert validate_input(with_(age=30.5), FEATURES) == ["age: must be a whole number, got 30.5"]


def test_int_feature_accepts_whole_float():
    assert validate_input(with_(age=30.0, ticket_count=2.0), FEATURES) == []


def test_float_feature_accepts_int():
    assert validate_input(with_(monthly_income=85000), FEATURES) == []


# --- min / max boundaries ----------------------------------------------------

@pytest.mark.parametrize(
    "name,value",
    [
        ("age", 18), ("age", 100),
        ("ticket_count", 0), ("ticket_count", 100),
        ("monthly_income", 0.0), ("monthly_income", 1000000.0),
        ("avg_balance", 0), ("avg_balance", 2000000.0),
    ],
)
def test_boundary_inclusive(name, value):
    assert validate_input(with_(**{name: value}), FEATURES) == []


@pytest.mark.parametrize(
    "name,value",
    [
        ("age", 17), ("age", 101),
        ("ticket_count", -1), ("ticket_count", 101),
        ("monthly_income", -0.01), ("monthly_income", 1000000.01),
        ("avg_balance", -0.01), ("avg_balance", 2000000.01),
    ],
)
def test_boundary_just_outside(name, value):
    rule = FEATURES[name]
    assert validate_input(with_(**{name: value}), FEATURES) == [
        f"{name}: {value} is outside the allowed range {rule['min']} to {rule['max']}"
    ]


# --- several problems --------------------------------------------------------

def test_several_problems_give_several_errors():
    customer = with_(age=12, gender="Other", monthly_income="lots", ticket_count=None, extra=1)
    del customer["city"]
    errors = validate_input(customer, FEATURES)
    assert sorted(errors) == sorted([
        "Missing required feature: city",
        "Unexpected feature: extra",
        "age: 12 is outside the allowed range 18 to 100",
        "gender: 'Other' is not allowed. Choose from ['Male', 'Female']",
        "monthly_income: must be a number, got 'lots'",
        "ticket_count: value is empty",
    ])


# --- known bugs (xfail; validation.py intentionally not changed) -------------

@pytest.mark.xfail(
    strict=True,
    reason="Bug: numpy integers (np.int64) are not instances of int, so validate_input "
           "reports 'must be a number' for a valid numpy int value.",
)
def test_numpy_int_accepted():
    assert validate_input(with_(age=np.int64(30)), FEATURES) == []


@pytest.mark.xfail(
    strict=True,
    raises=OverflowError,
    reason="Bug: infinity for an int feature crashes with OverflowError in int(value) "
           "instead of returning a validation error.",
)
def test_infinity_for_int_feature_gives_error_not_crash():
    errors = validate_input(with_(age=math.inf), FEATURES)
    assert len(errors) == 1 and errors[0].startswith("age:")


# --- predict_segment ---------------------------------------------------------

class ExplodingModel:
    """Stub model that fails the test if it is used."""
    classes_ = np.array([0, 1, 2])

    def predict(self, X):
        raise AssertionError("model.predict must not be called for invalid input")

    def predict_proba(self, X):
        raise AssertionError("model.predict_proba must not be called for invalid input")


def test_predict_segment_invalid_input_does_not_call_model():
    customer = with_(age=-5, city="Paris")
    result = predict_segment(customer, ExplodingModel(), SCHEMA)
    assert result == {"ok": False, "errors": validate_input(customer, FEATURES)}
    assert len(result["errors"]) == 2


@pytest.fixture(scope="module")
def real_model():
    joblib = pytest.importorskip("joblib")
    return joblib.load(REPO_ROOT / "cluster_model.joblib")


@pytest.mark.parametrize("customer", [VALID] + SAMPLE_ROWS[:6], ids=["VALID"] + [f"row{i + 1}" for i in range(6)])
def test_predict_segment_valid_input(real_model, customer):
    result = predict_segment(customer, real_model, SCHEMA)
    assert result["ok"] is True
    assert str(result["cluster"]) in SCHEMA["segments"]
    assert result["segment"] == SCHEMA["segments"][str(result["cluster"])]
    assert set(result["probabilities"]) == set(SCHEMA["segments"].values())
    # probabilities are rounded to 3 decimals, so allow a small tolerance
    assert sum(result["probabilities"].values()) == pytest.approx(1.0, abs=0.01)
    # the predicted segment should be the most likely one
    assert max(result["probabilities"], key=result["probabilities"].get) == result["segment"]
