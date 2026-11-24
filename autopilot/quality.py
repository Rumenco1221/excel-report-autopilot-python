"""Reglas de calidad de datos: detectan, explican y separan filas problemáticas."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class QualityResult:
    clean: pd.DataFrame
    issues: pd.DataFrame  # una fila por problema detectado

    @property
    def score(self) -> float:
        total = len(self.clean) + self.issues["row_id"].nunique() if len(self.issues) else len(self.clean)
        return 100.0 if total == 0 else round(100 * len(self.clean) / total, 1)


RULES = {
    "fecha_invalida": lambda d: d["date"].isna(),
    "unidades_invalidas": lambda d: d["units"].isna() | (d["units"] <= 0),
    "precio_invalido": lambda d: d["unit_price"].isna() | (d["unit_price"] <= 0),
    "campo_vacio": lambda d: d[["branch", "region", "product"]].isna().any(axis=1),
    "duplicado": lambda d: d.duplicated(subset=["date", "branch", "product", "units", "unit_price"], keep="first"),
}


def validate(df: pd.DataFrame) -> QualityResult:
    df = df.reset_index(drop=True).copy()
    df["row_id"] = df.index
    problems = []
    bad_mask = pd.Series(False, index=df.index)
    for rule, check in RULES.items():
        mask = check(df).fillna(True)
        bad_mask |= mask
        for _, row in df[mask].iterrows():
            problems.append({"row_id": row["row_id"], "source_file": row["source_file"], "rule": rule,
                             "branch": row["branch"], "product": row["product"]})
    issues = pd.DataFrame(problems, columns=["row_id", "source_file", "rule", "branch", "product"])
    return QualityResult(clean=df[~bad_mask].drop(columns="row_id"), issues=issues)
