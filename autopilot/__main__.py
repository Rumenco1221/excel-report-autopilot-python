"""CLI: python -m autopilot --input carpeta_con_archivos --output outputs"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .ingest import load_folder
from .quality import validate
from .report import write_reports


def main() -> None:
    ap = argparse.ArgumentParser(description="Consolida archivos de ventas y genera el reporte ejecutivo.")
    ap.add_argument("--input", default="sample_data", help="Carpeta con .xlsx/.csv de sucursales")
    ap.add_argument("--output", default="outputs", help="Carpeta de salida")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    log = logging.getLogger("autopilot")

    df = load_folder(Path(args.input))
    log.info("Filas leídas: %s de %s archivos", len(df), df["source_file"].nunique())
    result = validate(df)
    log.info("Filas válidas: %s · problemas: %s · calidad: %s%%", len(result.clean), len(result.issues), result.score)
    paths = write_reports(result, Path(args.output))
    for kind, path in paths.items():
        log.info("Reporte %s → %s", kind, path)


if __name__ == "__main__":
    main()
