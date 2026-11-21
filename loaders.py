"""Load the model and data files the app needs, and fail with a clear message if one is broken.

Every loader raises LoadError naming the file and what to do. The app calls them through
load_or_stop(), which shows that message with st.error and stops the script, so a missing
or broken file never ends in a traceback.
"""
import io
import json

import joblib
import pandas as pd
import streamlit as st
from PIL import Image

NOTEBOOK_HINT = "Re-run fintech_ml_pipeline.ipynb to create it again, or restore it from the repository."
REPO_HINT = "Restore it from the repository."

METRIC_KEYS = ["best_model", "test_rows", "accuracy", "precision_macro", "recall_macro", "f1_macro",
               "segment_sizes", "tuning"]


class LoadError(Exception):
    """A required file is missing, unreadable or invalid."""

    def __init__(self, path, problem, hint):
        self.path, self.problem, self.hint = path, problem, hint
        super().__init__(f"Could not load `{path}`: {problem}. {hint}")


def _read_bytes(path, hint):
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        raise LoadError(path, "the file is missing", hint) from None
    except IsADirectoryError:
        raise LoadError(path, "expected a file but found a folder", hint) from None
    except OSError as e:
        raise LoadError(path, f"the file could not be read ({e.strerror or e})", hint) from None


def load_model(path="cluster_model.joblib"):
    _read_bytes(path, NOTEBOOK_HINT)  # clear message for missing / unreadable before joblib tries
    try:
        model = joblib.load(path)
    except Exception as e:
        raise LoadError(path, f"the file is not a valid saved model ({type(e).__name__}: {e})",
                        NOTEBOOK_HINT + " Also check that scikit-learn and joblib match requirements.txt.") from None
    missing = [a for a in ("predict", "predict_proba", "classes_") if not hasattr(model, a)]
    if missing:
        raise LoadError(path, f"the saved object is not a fitted classifier (missing {', '.join(missing)})",
                        NOTEBOOK_HINT)
    return model


def load_json(path, hint=NOTEBOOK_HINT):
    raw = _read_bytes(path, hint)
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise LoadError(path, f"the file is not valid JSON ({e})", hint) from None


def load_schema(path="input_schema.json", required=()):
    schema = load_json(path)
    features = schema.get("features") if isinstance(schema, dict) else None
    segments = schema.get("segments") if isinstance(schema, dict) else None
    if not isinstance(features, dict) or not features:
        raise LoadError(path, "it has no \"features\" section", NOTEBOOK_HINT)
    if not isinstance(segments, dict) or not segments:
        raise LoadError(path, "it has no \"segments\" section", NOTEBOOK_HINT)
    for name, rule in features.items():
        kind = rule.get("type") if isinstance(rule, dict) else None
        if kind == "category":
            if not isinstance(rule.get("allowed"), list) or not rule["allowed"]:
                raise LoadError(path, f"feature \"{name}\" has no \"allowed\" list", NOTEBOOK_HINT)
        elif kind in ("int", "float"):
            if "min" not in rule or "max" not in rule:
                raise LoadError(path, f"feature \"{name}\" needs \"min\" and \"max\"", NOTEBOOK_HINT)
        else:
            raise LoadError(path, f"feature \"{name}\" has an unknown type {kind!r}", NOTEBOOK_HINT)
    missing = [name for name in required if name not in features]
    if missing:
        raise LoadError(path, f"it is missing the feature(s) {', '.join(missing)}", NOTEBOOK_HINT)
    return schema


def check_model_matches_schema(model, schema, segment_names, model_path="cluster_model.joblib",
                               schema_path="input_schema.json"):
    """The model's classes must all have a segment name in the schema that the app knows how to show."""
    for c in model.classes_:
        name = schema["segments"].get(str(c))
        if name is None:
            raise LoadError(schema_path, f"it has no segment name for model class {c} from `{model_path}`",
                            "Make sure both files come from the same run of fintech_ml_pipeline.ipynb.")
        if name not in segment_names:
            raise LoadError(schema_path, f"segment name \"{name}\" is not one of {', '.join(segment_names)}",
                            "Make sure both files come from the same run of fintech_ml_pipeline.ipynb.")


def load_metrics(path="metrics.json"):
    metrics = load_json(path)
    if not isinstance(metrics, dict):
        raise LoadError(path, "it should hold a JSON object", NOTEBOOK_HINT)
    missing = [k for k in METRIC_KEYS if k not in metrics]
    if missing:
        raise LoadError(path, f"it is missing {', '.join(missing)}", NOTEBOOK_HINT)
    return metrics


def load_csv_bytes(path="sample_batch.csv"):
    raw = _read_bytes(path, REPO_HINT)
    try:
        pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        raise LoadError(path, f"the file is not a valid CSV ({e})", REPO_HINT) from None
    return raw


def load_image_bytes(path="confusion_matrix.png"):
    raw = _read_bytes(path, NOTEBOOK_HINT)
    try:
        Image.open(io.BytesIO(raw)).verify()
    except Exception as e:
        raise LoadError(path, f"the file is not a valid image ({e})", NOTEBOOK_HINT) from None
    return raw


def load_text(path="MODEL_CARD.md"):
    raw = _read_bytes(path, REPO_HINT)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise LoadError(path, f"the file is not UTF-8 text ({e})", REPO_HINT) from None


def load_or_stop(loader, *args, **kwargs):
    """Run a loader; on LoadError show a clear st.error and stop the app."""
    try:
        return loader(*args, **kwargs)
    except LoadError as e:
        st.error(f"**Could not load `{e.path}`**: {e.problem}.\n\n{e.hint}")
        st.stop()
