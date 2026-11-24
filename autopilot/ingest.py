"""Lectura y normalización de archivos heterogéneos (.xlsx / .csv)."""
from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

# Cada columna canónica acepta varios nombres "del mundo real".
COLUMN_ALIASES: dict[str, list[str]] = {
    "date": ["fecha", "date", "fecha venta", "dia", "order date"],
    "branch": ["sucursal", "branch", "tienda", "local", "store"],
    "region": ["region", "zona", "zone", "area"],
    "product": ["producto", "product", "articulo", "item", "sku"],
    "units": ["unidades", "units", "cantidad", "qty", "quantity"],
    "unit_price": ["precio", "precio unitario", "unit price", "price", "pu"],
    "seller": ["vendedor", "seller", "vendedora", "rep", "sales rep"],
}

REQUIRED = ["date", "branch", "region", "product", "units", "unit_price"]


def _clean(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return " ".join(text.lower().replace("_", " ").replace(".", " ").split())


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    lookup = {alias: canon for canon, aliases in COLUMN_ALIASES.items() for alias in aliases}
    renamed = {col: lookup[_clean(col)] for col in df.columns if _clean(col) in lookup}
    df = df.rename(columns=renamed)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {missing}. Columnas recibidas: {list(df.columns)}")
    return df


def read_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path, sep=None, engine="python")  # detecta ; o ,
    else:
        raise ValueError(f"Formato no soportado: {path.name}")
    df = normalize_columns(df)
    df["source_file"] = path.name
    return df


def load_folder(folder: Path) -> pd.DataFrame:
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".xlsx", ".xls", ".csv"}
                   and not p.name.startswith("~$"))
    if not files:
        raise FileNotFoundError(f"No hay archivos .xlsx/.csv en {folder}")
    frames = [read_file(p) for p in files]
    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df["units"] = pd.to_numeric(df["units"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    for col in ("branch", "region", "product"):
        df[col] = df[col].astype("string").str.strip().str.title()
    df["revenue"] = df["units"] * df["unit_price"]
    return df
