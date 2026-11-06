"""Pruebas del paquete de Databricks Apps: qué archivos lleva y qué NO debe llevar."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_databricks_app", ROOT / "scripts" / "prepare_databricks_app.py")
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


@pytest.fixture()
def fake_root(tmp_path):
    for rel in prep.APP_FILES:
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text(
        "pandas==1.0\nnumpy==2.0\nscikit-learn==1.5\njoblib==1.4\nstreamlit==1.40\nmlflow==3.0\noptuna==4.0\n", encoding="utf-8")
    (tmp_path / ".env").write_text("DATABRICKS_TOKEN=secreto", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "student_exam_performance.csv").write_text("a,b", encoding="utf-8")
    return tmp_path


def test_bundle_has_app_model_schema_and_config(fake_root, tmp_path):
    files = prep.build_bundle(fake_root, tmp_path / "out")
    assert {"app.yaml", "requirements.txt", "app/streamlit_app.py", "models/model.joblib", "models/input_schema.json"} <= set(files)


def test_bundle_never_copies_secrets_or_data(fake_root, tmp_path):
    files = prep.build_bundle(fake_root, tmp_path / "out")
    assert not any(f.startswith("data/") or f.endswith(".env") for f in files)


def test_runtime_requirements_keep_only_what_the_app_imports(fake_root, tmp_path):
    prep.build_bundle(fake_root, tmp_path / "out")
    text = (tmp_path / "out" / "requirements.txt").read_text(encoding="utf-8")
    assert "scikit-learn==1.5" in text and "streamlit==1.40" in text
    assert "mlflow" not in text and "optuna" not in text


def test_app_yaml_launches_the_streamlit_app(fake_root, tmp_path):
    prep.build_bundle(fake_root, tmp_path / "out")
    text = (tmp_path / "out" / "app.yaml").read_text(encoding="utf-8")
    assert '"streamlit", "run", "app/streamlit_app.py"' in text


def test_missing_model_gives_a_clear_error(fake_root, tmp_path):
    (fake_root / "models" / "model.joblib").unlink()
    with pytest.raises(FileNotFoundError, match="09b_inferencia"):
        prep.build_bundle(fake_root, tmp_path / "out")


def test_requirements_missing_a_runtime_package_is_an_error(tmp_path):
    (tmp_path / "requirements.txt").write_text("pandas==1.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="scikit-learn"):
        prep.runtime_requirements(tmp_path / "requirements.txt")
