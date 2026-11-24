"""Genera el Excel ejecutivo (con formato) y un resumen HTML listo para enviar por email."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Template
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .quality import QualityResult

HEADER_FILL = PatternFill("solid", fgColor="1E3A8A")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def build_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    kpis = pd.DataFrame({
        "Indicador": ["Ingreso total", "Unidades vendidas", "Transacciones", "Ticket promedio", "Sucursales"],
        "Valor": [df["revenue"].sum(), df["units"].sum(), len(df), df["revenue"].mean(), df["branch"].nunique()],
    })
    by_region = (df.groupby("region", as_index=False)
                 .agg(Ingreso=("revenue", "sum"), Unidades=("units", "sum"), Transacciones=("revenue", "size"))
                 .sort_values("Ingreso", ascending=False))
    by_region["% del total"] = by_region["Ingreso"] / by_region["Ingreso"].sum()
    by_branch = (df.groupby(["region", "branch"], as_index=False)
                 .agg(Ingreso=("revenue", "sum"), Unidades=("units", "sum"))
                 .sort_values("Ingreso", ascending=False))
    top_products = (df.groupby("product", as_index=False)
                    .agg(Ingreso=("revenue", "sum"), Unidades=("units", "sum"))
                    .sort_values("Ingreso", ascending=False).head(10))
    return {"Resumen": kpis, "Por región": by_region, "Por sucursal": by_branch, "Top productos": top_products}


def _format_workbook(path: Path) -> None:
    wb = load_workbook(path)
    for ws in wb.worksheets:
        for cell in ws[1]:
            cell.fill, cell.font = HEADER_FILL, HEADER_FONT
            cell.alignment = Alignment(horizontal="center")
        for col_idx, col in enumerate(ws.columns, start=1):
            width = max(len(str(c.value)) if c.value is not None else 0 for c in col) + 3
            ws.column_dimensions[get_column_letter(col_idx)].width = min(width, 45)
            header = str(col[0].value or "")
            for c in col[1:]:
                if isinstance(c.value, (int, float)):
                    c.number_format = "0.0%" if header.startswith("%") else "#,##0.00"
        ws.freeze_panes = "A2"
    wb.save(path)


HTML = Template("""<!doctype html><html lang="es"><meta charset="utf-8"><title>Reporte {{ period }}</title>
<body style="font-family:Segoe UI,Arial,sans-serif;max-width:720px;margin:auto;color:#1f2937">
<h2 style="color:#1e3a8a">Reporte de ventas · {{ period }}</h2>
<p>Generado automáticamente el {{ generated }}. Calidad de datos: <b>{{ score }}%</b> de filas válidas.</p>
<table style="border-collapse:collapse;width:100%">
{% for k, v in kpis %}<tr><td style="padding:6px;border-bottom:1px solid #e5e7eb">{{ k }}</td>
<td style="padding:6px;border-bottom:1px solid #e5e7eb;text-align:right"><b>{{ v }}</b></td></tr>{% endfor %}
</table>
<h3>Región líder: {{ top_region }}</h3>
{% if issues %}<h3 style="color:#b91c1c">Filas excluidas por calidad ({{ issues|length }})</h3>
<ul>{% for r, n in issues %}<li>{{ r }}: {{ n }}</li>{% endfor %}</ul>{% endif %}
</body></html>""")


def write_reports(result: QualityResult, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = result.clean
    period = f"{df['date'].min():%d/%m/%Y} – {df['date'].max():%d/%m/%Y}"
    tables = build_tables(df)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    xlsx = out_dir / f"reporte_ventas_{stamp}.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=name, index=False)
        df.drop(columns=["source_file"]).to_excel(writer, sheet_name="Datos limpios", index=False)
        result.issues.to_excel(writer, sheet_name="Calidad de datos", index=False)
    _format_workbook(xlsx)

    kpis = tables["Resumen"]
    fmt = [f"$ {kpis.Valor[0]:,.0f}", f"{kpis.Valor[1]:,.0f}", f"{kpis.Valor[2]:,.0f}",
           f"$ {kpis.Valor[3]:,.2f}", f"{kpis.Valor[4]:,.0f}"]
    issues_count = result.issues["rule"].value_counts().items() if len(result.issues) else []
    html = out_dir / f"resumen_email_{stamp}.html"
    html.write_text(HTML.render(period=period, generated=datetime.now().strftime("%d/%m/%Y %H:%M"),
                                score=result.score, kpis=zip(kpis.Indicador, fmt),
                                top_region=tables["Por región"].iloc[0]["region"],
                                issues=list(issues_count)), encoding="utf-8")
    return {"excel": xlsx, "html": html}
