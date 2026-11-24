"""Crea 3 archivos de sucursales con encabezados distintos y errores intencionales (como en la vida real)."""
import random
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
rnd = random.Random(7)
PRODUCTS = {"Notebook Pro": 1200, "Monitor 27": 320, "Mouse Inalámbrico": 25, "Teclado Mecánico": 90,
            "Auriculares": 75, "Webcam HD": 60, "Silla Ergonómica": 280, "Dock USB-C": 110}


def rows(branch, region, n):
    out = []
    for _ in range(n):
        p = rnd.choice(list(PRODUCTS))
        out.append([f"{rnd.randint(1, 30):02d}/11/2026", branch, region, p, rnd.randint(1, 6),
                    round(PRODUCTS[p] * rnd.uniform(0.9, 1.1), 2), rnd.choice(["Ana", "Luis", "Sofía", "Diego"])])
    return out


# Sucursal 1: Excel, encabezados en español
a = pd.DataFrame(rows("Palermo", "CABA", 60), columns=["Fecha", "Sucursal", "Región", "Producto", "Unidades",
                                                       "Precio Unitario", "Vendedor"])
a.loc[3, "Unidades"] = -2          # error: unidades negativas
a = pd.concat([a, a.iloc[[5]]])    # error: fila duplicada
a.to_excel(HERE / "ventas_palermo_nov2026.xlsx", index=False)

# Sucursal 2: CSV con ; y encabezados en inglés
b = pd.DataFrame(rows("cordoba centro", "Centro", 45), columns=["Date", "Store", "Zone", "SKU", "Qty", "Price", "Rep"])
b.loc[10, "Date"] = "31/02/2026"   # error: fecha imposible
b.to_csv(HERE / "sales_cordoba_nov2026.csv", sep=";", index=False)

# Sucursal 3: Excel con nombres alternativos
c = pd.DataFrame(rows("Rosario", "Litoral", 50), columns=["fecha_venta", "tienda", "zona", "articulo", "cantidad",
                                                          "pu", "vendedora"])
c.loc[7, "pu"] = None              # error: precio vacío
c.to_excel(HERE / "ventas_rosario_nov2026.xlsx", index=False)
print("Archivos de ejemplo creados en", HERE)
