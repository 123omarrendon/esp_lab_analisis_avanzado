import mlflow
import pytest

from proyecto.tracking import mlflow_utils as mu


def test_force_local_uses_sqlite_and_logs_a_run(tmp_path):
    where = mu.configure_mlflow(force_local=True, local_db=tmp_path / "mlflow.db", env_file=tmp_path / "no_existe.env")
    assert where == "local"
    assert mlflow.get_tracking_uri().startswith("sqlite:///")
    assert not mu.uses_databricks()

    mu.set_experiment("prueba-local")
    run_id = mu.log_run("r1", {"alpha": 0.1, "depth": None}, {"cost": 0.5}, tags={"etapa": "test"})
    run = mlflow.get_run(run_id)
    assert run.data.params == {"alpha": "0.1", "depth": "None"}
    assert run.data.metrics["cost"] == 0.5
    assert run.data.tags["etapa"] == "test"


def test_registered_model_name_is_plain_when_local(tmp_path):
    mu.configure_mlflow(force_local=True, local_db=tmp_path / "mlflow.db", env_file=tmp_path / "no_existe.env")
    assert mu.registered_model_name("mi_modelo") == "mi_modelo"


def test_missing_credentials_fall_back_to_local(tmp_path, monkeypatch):
    for var in ("PROFILE", "DATABRICKS_HOST", "DATABRICKS_TOKEN", "MLFLOW_FORCE_LOCAL"):
        monkeypatch.delenv(var, raising=False)
    where = mu.configure_mlflow(local_db=tmp_path / "mlflow.db", env_file=tmp_path / "no_existe.env")
    assert where == "local"


def test_experiment_dir_is_ignored_in_local_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("EXPERIMENT_DIR", "/Users/alguien/carpeta")
    mu.configure_mlflow(force_local=True, local_db=tmp_path / "mlflow.db", env_file=tmp_path / "no_existe.env")
    assert mu.set_experiment("prueba") == "prueba"


def test_inside_databricks_the_tracking_goes_to_the_workspace(monkeypatch):
    monkeypatch.setattr(mu, "is_databricks", lambda: True)
    mlflow.set_tracking_uri("sqlite:///un_archivo_local_previo.db")               # configuración previa equivocada
    assert mu.configure_mlflow() == "databricks (dentro del workspace)"
    assert mlflow.get_tracking_uri() == "databricks"                                # se corrige al volver a ejecutar


def test_inside_databricks_the_local_fallback_never_writes_in_the_repo_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(mu, "is_databricks", lambda: True)
    monkeypatch.setattr(mu.tempfile, "gettempdir", lambda: str(tmp_path))
    assert mu.configure_mlflow(force_local=True, env_file=tmp_path / "no_existe.env") == "local"
    assert mlflow.get_tracking_uri() == f"sqlite:///{(tmp_path / 'mlflow_local.db').as_posix()}"
    assert str(mu.ROOT) not in mlflow.get_tracking_uri()                            # el repo (solo lectura) no se toca


def test_outside_databricks_an_explicit_local_db_is_respected(tmp_path):
    db = tmp_path / "mi.db"
    mu.configure_mlflow(force_local=True, local_db=db, env_file=tmp_path / "no_existe.env")
    assert mlflow.get_tracking_uri() == f"sqlite:///{db.as_posix()}"


def test_inside_databricks_an_explicit_local_db_is_still_respected(tmp_path, monkeypatch):
    monkeypatch.setattr(mu, "is_databricks", lambda: True)
    db = tmp_path / "elegido.db"
    mu.configure_mlflow(force_local=True, local_db=db, env_file=tmp_path / "no_existe.env")
    assert mlflow.get_tracking_uri() == f"sqlite:///{db.as_posix()}"                # solo se reemplaza el valor por defecto


def test_databricks_is_detected_by_its_filesystem_when_the_variable_is_missing(monkeypatch):
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    monkeypatch.setattr(mu, "_databricks_filesystem", lambda: False)
    assert not mu.is_databricks()
    monkeypatch.setattr(mu, "_databricks_filesystem", lambda: True)
    assert mu.is_databricks()                                                       # sin variable, pero con /databricks
    monkeypatch.setattr(mu, "_databricks_filesystem", lambda: False)
    monkeypatch.setenv("DATABRICKS_RUNTIME_VERSION", "15.4")
    assert mu.is_databricks()


def test_sqlite_writable_probe_says_yes_in_a_normal_folder_and_no_in_a_missing_one(tmp_path):
    assert mu._sqlite_writable(tmp_path / "x.db") is True
    assert list(tmp_path.iterdir()) == []                                           # no deja basura
    assert mu._sqlite_writable(tmp_path / "no_existe" / "x.db") is False


def test_if_the_repo_folder_is_not_writable_for_sqlite_the_fallback_goes_to_a_temp_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(mu, "is_databricks", lambda: False)                         # entorno NO detectado como Databricks
    monkeypatch.setattr(mu, "_sqlite_writable", lambda path: False)                 # pero la carpeta no sirve
    monkeypatch.setattr(mu.tempfile, "gettempdir", lambda: str(tmp_path))
    mu.configure_mlflow(env_file=tmp_path / "no_existe.env")
    assert mlflow.get_tracking_uri() == f"sqlite:///{(tmp_path / 'mlflow_local.db').as_posix()}"


def test_a_writable_repo_folder_keeps_the_default_local_db(tmp_path, monkeypatch):
    monkeypatch.setattr(mu, "is_databricks", lambda: False)
    monkeypatch.setattr(mu, "_sqlite_writable", lambda path: True)
    mu.configure_mlflow(env_file=tmp_path / "no_existe.env")
    assert mlflow.get_tracking_uri() == f"sqlite:///{mu.LOCAL_DB.as_posix()}"


def test_it_works_with_or_without_the_db_file(tmp_path):
    db = tmp_path / "mlflow_local.db"
    assert not db.exists() and mu._sqlite_writable(db) is True                      # sin archivo: se creará
    mu.configure_mlflow(force_local=True, local_db=db, env_file=tmp_path / "no_existe.env")
    mu.set_experiment("con-o-sin-archivo")
    mu.log_run("r1", {"a": 1}, {"cost": 0.1})
    assert db.exists() and mu._sqlite_writable(db) is True                          # con archivo (ya creado por MLflow)
    mu.log_run("r2", {"a": 2}, {"cost": 0.2})                                        # y se sigue pudiendo registrar


def test_an_existing_read_only_db_file_is_not_used(tmp_path, monkeypatch):
    import os
    db = tmp_path / "mlflow_local.db"
    db.write_bytes(b"")
    os.chmod(db, 0o444)                                                              # como el archivo que viene en el repo clonado
    if os.access(db, os.W_OK):
        pytest.skip("este usuario puede escribir aunque el archivo sea de solo lectura (p. ej. administrador)")
    assert mu._sqlite_writable(db) is False
    monkeypatch.setattr(mu, "is_databricks", lambda: False)
    monkeypatch.setattr(mu, "LOCAL_DB", db)                                          # el valor por defecto pasa a ser ese archivo
    monkeypatch.setattr(mu.tempfile, "gettempdir", lambda: str(tmp_path / "tmp"))
    (tmp_path / "tmp").mkdir()
    mu.configure_mlflow(local_db=db, env_file=tmp_path / "no_existe.env")
    assert mlflow.get_tracking_uri() == f"sqlite:///{(tmp_path / 'tmp' / 'mlflow_local.db').as_posix()}"
