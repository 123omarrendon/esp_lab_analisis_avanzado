"""Conexión y registro de ejecuciones en MLflow: Databricks si hay conexión, local si no.

Cómo usarlo en un notebook (ver `.env.example` para la conexión):
    from proyecto.tracking.mlflow_utils import configure_mlflow, set_experiment, log_run
    where = configure_mlflow()                 # 'databricks (...)' o 'local' (respaldo automático)
    set_experiment("mi-proyecto-optimizacion")  # en Databricks va a EXPERIMENT_DIR si lo definiste
    log_run("ensayo-1", {"depth": 6}, {"cost": 0.48}, tags={"etapa": "06_optimizacion"})
Si no hay conexión (o pones MLFLOW_FORCE_LOCAL=1 en .env), todo se guarda en `mlflow_local.db`.

Dos formas de conectar a Databricks, ambas leídas de `.env`:
  - PROFILE=<perfil de ~/.databrickscfg>        -> databricks://<perfil>
  - DATABRICKS_HOST + DATABRICKS_TOKEN          -> databricks
"""
import os
import sqlite3
import tempfile
import warnings
from pathlib import Path

import mlflow
from dotenv import load_dotenv

# src/proyecto/tracking/mlflow_utils.py -> la raíz del repositorio está tres niveles arriba de `proyecto`
ROOT = Path(__file__).resolve().parents[3]
LOCAL_DB = ROOT / "mlflow_local.db"  # se genera sola; no se versiona
PLACEHOLDER_PROFILE = "nombre-de-tu-perfil"  # valor de .env.example sin completar


def _databricks_filesystem() -> bool:
    """True si existe la carpeta `/databricks` (solo está en las máquinas de Databricks)."""
    return Path("/databricks").is_dir()


def is_databricks() -> bool:
    """True si el código corre dentro de un workspace de Databricks.

    Mira la variable `DATABRICKS_RUNTIME_VERSION` y, por si algún tipo de cómputo no la define, la carpeta `/databricks`.
    """
    return "DATABRICKS_RUNTIME_VERSION" in os.environ or _databricks_filesystem()


def _sqlite_writable(db_path: Path) -> bool:
    """True si SQLite puede ESCRIBIR en `db_path`, exista ya el archivo o no. Se prueba de verdad, con un archivo de prueba.

    Mirar permisos no basta: en `/Workspace/...` de Databricks se pueden crear archivos, pero SQLite falla con
    «attempt to write a readonly database».
    """
    if Path(db_path).exists() and not os.access(db_path, os.W_OK):
        return False                                    # el archivo existe (p. ej. viene en el repo) pero es de solo lectura
    probe = Path(db_path).parent / ".mlflow_probe.db"
    try:
        with sqlite3.connect(probe) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS probe (x INTEGER)")
            conn.execute("INSERT INTO probe VALUES (1)")
        return True
    except (sqlite3.Error, OSError):
        return False
    finally:
        try:
            probe.unlink()
        except OSError:
            pass


def _reachable() -> bool:
    try:
        mlflow.search_experiments(max_results=1)
        return True
    except Exception as error:  # sin red, credenciales inválidas, cuota agotada, CLI fuera del PATH...
        reason = str(error).splitlines()[0][:140]
        warnings.warn(f"Databricks no disponible ({reason}). Se usa MLflow local.", stacklevel=3)
        return False


def configure_mlflow(force_local: bool = False, local_db: Path = LOCAL_DB, env_file: Path = ROOT / ".env") -> str:
    """Configura MLflow y devuelve una descripción de dónde quedó: 'databricks (...)' o 'local'."""
    if is_databricks() and not force_local:
        # Dentro del workspace se apunta explícitamente a Databricks: así, si en la misma sesión se había configurado
        # un archivo local antes, se corrige al volver a ejecutar la celda.
        mlflow.set_tracking_uri("databricks")
        mlflow.set_registry_uri("databricks-uc")
        return "databricks (dentro del workspace)"
    load_dotenv(env_file)
    if not force_local and os.environ.get("MLFLOW_FORCE_LOCAL") != "1":
        profile = os.environ.get("PROFILE")
        if profile and profile != PLACEHOLDER_PROFILE:
            mlflow.set_tracking_uri(f"databricks://{profile}")
            mlflow.set_registry_uri(f"databricks-uc://{profile}")
            if _reachable():
                return f"databricks (perfil {profile})"
        elif os.environ.get("DATABRICKS_HOST") and os.environ.get("DATABRICKS_TOKEN"):
            mlflow.set_tracking_uri("databricks")
            mlflow.set_registry_uri("databricks-uc")
            if _reachable():
                return "databricks (token)"
    if Path(local_db) == LOCAL_DB and (is_databricks() or not _sqlite_writable(LOCAL_DB)):
        # La carpeta del repo en el workspace (/Workspace/...) no sirve para SQLite
        # («attempt to write a readonly database»): el respaldo local va a una carpeta temporal escribible.
        # Un archivo elegido a propósito (`local_db` distinto del valor por defecto) se respeta siempre.
        local_db = Path(tempfile.gettempdir()) / LOCAL_DB.name
    local_uri = f"sqlite:///{Path(local_db).as_posix()}"
    mlflow.set_tracking_uri(local_uri)
    mlflow.set_registry_uri(local_uri)
    return "local"


def uses_databricks() -> bool:
    """True si MLflow quedó apuntando a Databricks (tras `configure_mlflow`)."""
    return mlflow.get_tracking_uri().startswith("databricks")


def _databricks_user() -> str:
    from databricks.sdk import WorkspaceClient

    profile = os.environ.get("PROFILE")
    if profile and profile != PLACEHOLDER_PROFILE and not is_databricks():
        return WorkspaceClient(profile=profile).current_user.me().user_name
    return WorkspaceClient().current_user.me().user_name


def set_experiment(name: str) -> str:
    """Crea o activa el experimento. En Databricks el nombre debe ser una ruta.

    Si `.env` define EXPERIMENT_DIR (una carpeta del workspace que ya existe), el experimento va ahí;
    si no, en /Users/<usuario>/.
    """
    if uses_databricks():
        folder = os.environ.get("EXPERIMENT_DIR", "").rstrip("/") or f"/Users/{_databricks_user()}"
        full_name = f"{folder}/{name}"
    else:
        full_name = name
    mlflow.set_experiment(full_name)
    return full_name


def registered_model_name(name: str) -> str:
    """Nombre completo para el registro: catalog.schema.name en Unity Catalog; el nombre solo en local."""
    if not mlflow.get_registry_uri().startswith("databricks"):
        return name
    catalog = os.environ.get("UC_CATALOG", "workspace")
    schema = os.environ.get("UC_SCHEMA", "default")
    return f"{catalog}.{schema}.{name}"


def log_run(run_name: str, params: dict, metrics: dict, tags: dict | None = None, nested: bool = False) -> str:
    """Registra una ejecución completa (parámetros, métricas y etiquetas) y devuelve su run_id."""
    with mlflow.start_run(run_name=run_name, nested=nested) as run:
        mlflow.log_params({k: ("None" if v is None else v) for k, v in params.items()})
        mlflow.log_metrics({k: float(v) for k, v in metrics.items()})
        if tags:
            mlflow.set_tags(tags)
        return run.info.run_id
