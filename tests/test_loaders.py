import json
import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import loaders  # noqa: E402
from loaders import LoadError  # noqa: E402

SEGMENT_NAMES = ["Low value", "Medium value", "High value"]


def copy_repo_file(name, tmp_path):
    dest = tmp_path / name
    shutil.copy(os.path.join(ROOT, name), dest)
    return str(dest)


# ---------- the real files load ----------
def test_real_files_load():
    model = loaders.load_model(os.path.join(ROOT, "cluster_model.joblib"))
    schema = loaders.load_schema(os.path.join(ROOT, "input_schema.json"), required=("gender", "city"))
    loaders.check_model_matches_schema(model, schema, SEGMENT_NAMES)
    assert "accuracy" in loaders.load_metrics(os.path.join(ROOT, "metrics.json"))
    assert loaders.load_csv_bytes(os.path.join(ROOT, "sample_batch.csv"))
    assert loaders.load_image_bytes(os.path.join(ROOT, "confusion_matrix.png"))
    assert loaders.load_text(os.path.join(ROOT, "MODEL_CARD.md"))


# ---------- missing files ----------
@pytest.mark.parametrize("loader", [loaders.load_model, loaders.load_schema, loaders.load_metrics,
                                    loaders.load_csv_bytes, loaders.load_image_bytes, loaders.load_text])
def test_missing_file_names_the_file(loader, tmp_path):
    path = str(tmp_path / "nope.file")
    with pytest.raises(LoadError) as e:
        loader(path)
    assert e.value.path == path
    assert "missing" in e.value.problem
    assert e.value.hint


def test_folder_instead_of_file(tmp_path):
    with pytest.raises(LoadError, match="folder"):
        loaders.load_json(str(tmp_path))


# ---------- invalid files ----------
def test_corrupt_model(tmp_path):
    path = tmp_path / "cluster_model.joblib"
    path.write_bytes(b"not a model")
    with pytest.raises(LoadError, match="not a valid saved model"):
        loaders.load_model(str(path))


def test_model_without_predict(tmp_path):
    import joblib
    path = tmp_path / "cluster_model.joblib"
    joblib.dump({"just": "a dict"}, path)
    with pytest.raises(LoadError, match="not a fitted classifier"):
        loaders.load_model(str(path))


def test_bad_json(tmp_path):
    path = tmp_path / "input_schema.json"
    path.write_text("{ broken")
    with pytest.raises(LoadError, match="not valid JSON"):
        loaders.load_schema(str(path))


@pytest.mark.parametrize("schema, message", [
    ([], "features"),
    ({"segments": {"0": "Low value"}}, "features"),
    ({"features": {"age": {"type": "int", "min": 0, "max": 1}}}, "segments"),
    ({"features": {"city": {"type": "category"}}, "segments": {"0": "x"}}, "allowed"),
    ({"features": {"age": {"type": "int"}}, "segments": {"0": "x"}}, "min"),
    ({"features": {"age": {"type": "date"}}, "segments": {"0": "x"}}, "unknown type"),
])
def test_invalid_schema(schema, message, tmp_path):
    path = tmp_path / "input_schema.json"
    path.write_text(json.dumps(schema))
    with pytest.raises(LoadError, match=message):
        loaders.load_schema(str(path))


def test_schema_missing_required_feature(tmp_path):
    path = tmp_path / "input_schema.json"
    path.write_text(json.dumps({"features": {"age": {"type": "int", "min": 0, "max": 1}}, "segments": {"0": "x"}}))
    with pytest.raises(LoadError, match="gender"):
        loaders.load_schema(str(path), required=("age", "gender"))


def test_model_schema_mismatch():
    class Model:
        classes_ = [0, 1, 7]
    schema = {"segments": {"0": "Low value", "1": "High value"}}
    with pytest.raises(LoadError, match="model class 7"):
        loaders.check_model_matches_schema(Model(), schema, SEGMENT_NAMES)
    schema["segments"]["7"] = "Unknown"
    with pytest.raises(LoadError, match="Unknown"):
        loaders.check_model_matches_schema(Model(), schema, SEGMENT_NAMES)


def test_metrics_missing_keys(tmp_path):
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps({"accuracy": 1.0}))
    with pytest.raises(LoadError, match="best_model"):
        loaders.load_metrics(str(path))


def test_bad_image(tmp_path):
    path = tmp_path / "confusion_matrix.png"
    path.write_bytes(b"not a png")
    with pytest.raises(LoadError, match="not a valid image"):
        loaders.load_image_bytes(str(path))


def test_bad_csv(tmp_path):
    path = tmp_path / "sample_batch.csv"
    path.write_bytes(b"")
    with pytest.raises(LoadError, match="not a valid CSV"):
        loaders.load_csv_bytes(str(path))


def test_non_utf8_text(tmp_path):
    path = tmp_path / "MODEL_CARD.md"
    path.write_bytes(b"\xff\xfe\xfa")
    with pytest.raises(LoadError, match="UTF-8"):
        loaders.load_text(str(path))


# ---------- load_or_stop shows st.error and stops ----------
class StopCalled(Exception):
    pass


class FakeSt:
    def __init__(self):
        self.errors = []

    def error(self, message):
        self.errors.append(message)

    def stop(self):
        raise StopCalled


def test_load_or_stop_shows_error_and_stops(monkeypatch, tmp_path):
    fake = FakeSt()
    monkeypatch.setattr(loaders, "st", fake)
    path = str(tmp_path / "cluster_model.joblib")
    with pytest.raises(StopCalled):
        loaders.load_or_stop(loaders.load_model, path)
    assert len(fake.errors) == 1
    assert path in fake.errors[0] and "missing" in fake.errors[0] and "fintech_ml_pipeline.ipynb" in fake.errors[0]


def test_load_or_stop_returns_value(monkeypatch):
    fake = FakeSt()
    monkeypatch.setattr(loaders, "st", fake)
    assert loaders.load_or_stop(lambda: 42) == 42
    assert fake.errors == []
