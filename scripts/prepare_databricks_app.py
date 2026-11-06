"""Arma la carpeta que se sube a Databricks Apps (la app de Streamlit con su modelo y su esquema).

Qué hace: copia SOLO lo que la app necesita para correr (la app, el código de inferencia, `models/model.joblib`,
`models/input_schema.json` y la ficha) a una carpeta limpia, y escribe ahí `app.yaml` y un `requirements.txt` mínimo
con las versiones del proyecto. Mantiene el mismo diseño de carpetas del repo (app/, src/, models/), así que
`streamlit_app.py` funciona sin cambios.

La app NO consulta MLflow ni el registro de Databricks: solo se aloja en Databricks Apps. No se copian datos,
credenciales ni `.env`.

Uso (desde la raíz del repo):
    python scripts/prepare_databricks_app.py                      # crea deploy/databricks_app/
    python scripts/prepare_databricks_app.py --out ~/databricks_app

Luego se sube al repo (git push) y en Databricks se trae con «pull» desde una carpeta Git y se despliega desde la
interfaz web; sin CLI. Los pasos están en reports/09_despliegue.md.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "deploy" / "databricks_app"

APP_FILES = [
    "app/streamlit_app.py",
    "src/proyecto/__init__.py",
    "src/proyecto/inference/__init__.py",
    "src/proyecto/inference/predict.py",
    "src/proyecto/inference/schema.py",
    "models/model.joblib",
    "models/input_schema.json",
    "models/ficha_modelo.md",
]
# Solo lo que importa la app en tiempo de ejecución (el modelo es un Pipeline de scikit-learn: no necesita nada de src/ más).
RUNTIME_PACKAGES = ("streamlit", "pandas", "numpy", "scikit-learn", "joblib")
# Databricks Apps usa Python 3.11 (menor que el 3.12 del proyecto): numpy 2.5.x exige 3.12 o más y pip lo descarta
# («Ignored the following versions that require a different python version: ... 2.5.4»). Para numpy se usa un rango que
# resuelve en 3.11; las demás versiones se mantienen fijas (comprobado: resuelven en Python 3.11).
REQUIREMENT_OVERRIDES = {"numpy": "numpy>=2.3,<2.5"}

APP_YAML = """# Configuración de la app para Databricks Apps.
# Lanza la misma app que se prueba en local: streamlit run app/streamlit_app.py
command: ["streamlit", "run", "app/streamlit_app.py"]
env:
  - name: STREAMLIT_BROWSER_GATHER_USAGE_STATS
    value: "false"
"""


def runtime_requirements(requirements_path: Path) -> str:
    """Las líneas de requirements.txt del proyecto que la app necesita, con sus versiones fijadas."""
    wanted, found = {p.lower() for p in RUNTIME_PACKAGES}, []
    for line in requirements_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.\-]+)==", line.strip())
        if match and match.group(1).lower() in wanted:
            found.append(REQUIREMENT_OVERRIDES.get(match.group(1).lower(), line.strip()))
    missing = wanted - {re.split(r"==|>=", f)[0].lower() for f in found}
    if missing:
        raise ValueError(f"Faltan en requirements.txt (con versión fijada): {', '.join(sorted(missing))}")
    return "\n".join(found) + "\n"


def build_bundle(root: Path = ROOT, out: Path = DEFAULT_OUT) -> list[str]:
    """Crea `out` con la app lista para Databricks Apps. Devuelve la lista de archivos escritos (rutas relativas)."""
    root, out = Path(root), Path(out)
    missing = [f for f in APP_FILES if not (root / f).exists()]
    if missing:
        raise FileNotFoundError(
            "Faltan archivos para armar la app: " + ", ".join(missing)
            + ". Ejecuta antes el notebook notebooks/09b_inferencia_aprueba_o_no.ipynb."
        )
    if out.exists():
        shutil.rmtree(out)
    for rel in APP_FILES:
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, target)
    (out / "app.yaml").write_text(APP_YAML, encoding="utf-8")
    (out / "requirements.txt").write_text(runtime_requirements(root / "requirements.txt"), encoding="utf-8")
    return sorted(str(p.relative_to(out)).replace("\\", "/") for p in out.rglob("*") if p.is_file())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="carpeta de salida (por defecto deploy/databricks_app)")
    args = parser.parse_args()
    files = build_bundle(ROOT, args.out.expanduser())
    size = sum((args.out.expanduser() / f).stat().st_size for f in files) / 1e6
    print(f"Paquete listo en {args.out} ({len(files)} archivos, {size:.2f} MB):")
    for f in files:
        print("  ", f)
    print("\nSiguiente paso (sin CLI): git add deploy/databricks_app && git commit && git push; luego, en Databricks:")
    print("  carpeta Git -> Pull, y Compute -> Apps -> Deploy con la ruta .../deploy/databricks_app (ver reports/09_despliegue.md)")


if __name__ == "__main__":
    sys.exit(main())
