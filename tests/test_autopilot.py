import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autopilot.ingest import normalize_columns, load_folder  # noqa: E402
from autopilot.quality import validate  # noqa: E402
from autopilot.report import write_reports  # noqa: E402


def test_aliases_are_normalized():
    df = pd.DataFrame(columns=["Fecha", "Tienda", "Zona", "SKU", "Qty", "Precio Unitario"])
    assert list(normalize_columns(df).columns) == ["date", "branch", "region", "product", "units", "unit_price"]


def test_missing_required_column_raises():
    with pytest.raises(ValueError, match="Faltan columnas"):
        normalize_columns(pd.DataFrame(columns=["Fecha", "Tienda"]))


def test_quality_rules_catch_errors(tmp_path):
    pd.DataFrame({
        "Fecha": ["01/11/2026", "02/11/2026", "xx", "01/11/2026"],
        "Sucursal": ["A", "A", "A", "A"], "Region": ["R", "R", "R", "R"],
        "Producto": ["P", "Q", "P", "P"], "Unidades": [1, -1, 2, 1], "Precio": [10, 10, 10, 10],
    }).to_csv(tmp_path / "f.csv", index=False)
    result = validate(load_folder(tmp_path))
    assert set(result.issues["rule"]) == {"unidades_invalidas", "fecha_invalida", "duplicado"}
    assert len(result.clean) == 1


def test_end_to_end(tmp_path):
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "sample_data" / "make_samples.py")], check=True)
    result = validate(load_folder(ROOT / "sample_data"))
    paths = write_reports(result, tmp_path)
    assert paths["excel"].exists() and paths["html"].exists()
    assert len(result.issues) >= 4
