"""Genera data/processed/cartera_banca_privada_2026.csv a partir de los Excel de data/raw.

Es la misma limpieza del notebook (paso 2), en formato script:
    python preparar_datos.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).parent
RAW = RAIZ / "data" / "raw"
SALIDA = RAIZ / "data" / "processed" / "cartera_banca_privada_2026.csv"

COLUMNAS = ["segmento", "fecha", "entidad", "provincia", "canton",
            "por_vencer", "no_devenga", "vencida", "saldo_total"]
SEGMENTOS = {"CONSUMO": "Consumo", "MICROCREDITO": "Microcrédito", "PRODUCTIVO": "Productivo",
             "INMOBILIARIO": "Inmobiliario", "VIVIENDA INTERES PUBLICO": "Vivienda interés público"}
REGION = {}
for p in ["EL ORO", "ESMERALDAS", "GUAYAS", "LOS RIOS", "MANABI", "SANTA ELENA"]:
    REGION[p] = "Costa"
for p in ["AZUAY", "BOLIVAR", "CAÑAR", "CARCHI", "CHIMBORAZO", "COTOPAXI", "IMBABURA", "LOJA",
          "PICHINCHA", "SANTO DOMINGO DE LOS TSÁCHILAS", "TUNGURAHUA"]:
    REGION[p] = "Sierra"
for p in ["MORONA SANTIAGO", "NAPO", "ORELLANA", "PASTAZA", "SUCUMBIOS", "ZAMORA CHINCHIPE"]:
    REGION[p] = "Oriente"
REGION["GALAPAGOS"] = "Insular"


def entidad_corta(nombre: str) -> str:
    n = " ".join(nombre.split())
    if "CODESARROLLO" in n:
        return "CODESARROLLO"
    if "AMIBANK" in n:
        return "AMIBANK (liquidacion)"
    if "VISIONFUND" in n:
        return "VISIONFUND"
    return n.replace("BP ", "").replace("BANCO ", "").replace(" S.A.", "")


def main() -> None:
    tablas = []
    for archivo in sorted(RAW.glob("*.xlsx")):
        libro = pd.ExcelFile(archivo)
        for hoja in libro.sheet_names:
            if hoja.startswith("BASE"):
                t = libro.parse(hoja, header=1).iloc[:, 1:]
                t.columns = COLUMNAS
                t["segmento"] = t["segmento"].ffill()
                tablas.append(t)
    df = pd.concat(tablas, ignore_index=True)
    df["entidad"] = df["entidad"].map(entidad_corta)

    llave = ["segmento", "fecha", "entidad", "provincia", "canton"]
    df = df.groupby(llave, as_index=False)[["por_vencer", "no_devenga", "vencida", "saldo_total"]].sum()

    df["segmento"] = df["segmento"].map(SEGMENTOS)
    df["region"] = df["provincia"].map(REGION).fillna("Otros")
    df["improductiva"] = df["no_devenga"] + df["vencida"]
    df["morosidad_pct"] = np.where(df["saldo_total"] > 0, df["improductiva"] / df["saldo_total"] * 100, np.nan)
    df["mes"] = df["fecha"].dt.strftime("%Y-%m")

    columnas = ["fecha", "mes", "segmento", "entidad", "provincia", "region", "canton",
                "por_vencer", "no_devenga", "vencida", "saldo_total", "improductiva", "morosidad_pct"]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df[columnas].to_csv(SALIDA, index=False)
    print(f"Guardado {SALIDA} ({len(df):,} filas)")


if __name__ == "__main__":
    main()
