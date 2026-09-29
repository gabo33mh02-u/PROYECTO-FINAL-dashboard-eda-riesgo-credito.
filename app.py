"""Dashboard EDA - Riesgo de credito de la banca privada del Ecuador (ene-ago 2026).

Ejecutar:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Riesgo de crédito · Banca privada Ecuador 2026", layout="wide")

RUTA = Path(__file__).parent / "data" / "processed" / "cartera_banca_privada_2026.csv"


# ------------------------------------------------------------------ datos
@st.cache_data
def cargar_datos() -> pd.DataFrame:
    return pd.read_csv(RUTA, parse_dates=["fecha"])


def tasa(df: pd.DataFrame) -> float:
    """Morosidad ponderada: suma de improductiva / suma de saldo."""
    saldo = df["saldo_total"].sum()
    return df["improductiva"].sum() / saldo * 100 if saldo > 0 else float("nan")


def agrupar(df: pd.DataFrame, por) -> pd.DataFrame:
    g = df.groupby(por)[["saldo_total", "improductiva"]].sum()
    g["morosidad_pct"] = g["improductiva"] / g["saldo_total"] * 100
    return g.reset_index()


datos = cargar_datos()
meses = sorted(datos["mes"].unique())

# ------------------------------------------------------------------ filtros
st.sidebar.header("Filtros")
mes_ini, mes_fin = st.sidebar.select_slider("Periodo", options=meses, value=(meses[0], meses[-1]))
segmentos = st.sidebar.multiselect("Segmento de crédito", sorted(datos["segmento"].unique()),
                                   default=sorted(datos["segmento"].unique()))
regiones = st.sidebar.multiselect("Región", sorted(datos["region"].unique()),
                                  default=sorted(datos["region"].unique()))

st.sidebar.header("Reglas de decisión")
umbral_alerta = st.sidebar.slider("Alerta si morosidad >= (%)", 2.0, 10.0, 5.0, 0.5)
umbral_ok = st.sidebar.slider("Oportunidad si morosidad <= (%)", 0.5, 4.0, 2.0, 0.5)
cartera_min = st.sidebar.number_input("Cartera mínima para comparar (millones USD)", 1, 1000, 50)

filtrado = datos[(datos["mes"] >= mes_ini) & (datos["mes"] <= mes_fin)
                 & datos["segmento"].isin(segmentos) & datos["region"].isin(regiones)]
if filtrado.empty:
    st.warning("No hay datos con los filtros elegidos.")
    st.stop()

fin = filtrado[filtrado["mes"] == mes_fin]
ini = filtrado[filtrado["mes"] == mes_ini]

# ------------------------------------------------------------------ encabezado y KPIs
st.title("Riesgo de crédito · Banca privada del Ecuador 2026")
st.caption("Fuente: Superintendencia de Bancos, Portal Estadístico (Cartera). Morosidad = (no devenga + vencida) / saldo total.")

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Cartera total ({mes_fin})", f"USD {fin['saldo_total'].sum() / 1e9:,.2f} mil M")
k2.metric("Cartera improductiva", f"USD {fin['improductiva'].sum() / 1e6:,.0f} M")
delta = None if mes_ini == mes_fin else f"{tasa(fin) - tasa(ini):+.2f} pp vs {mes_ini}"
k3.metric("Morosidad ponderada", f"{tasa(fin):.2f}%", delta, delta_color="inverse")
por_seg = agrupar(fin, "segmento").sort_values("morosidad_pct", ascending=False)
k4.metric("Segmento más moroso", por_seg["segmento"].iloc[0], f"{por_seg['morosidad_pct'].iloc[0]:.2f}%",
          delta_color="off")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Resumen", "Geografía", "Entidades", "Decisiones", "Datos"])

# ------------------------------------------------------------------ 1. Resumen
with tab1:
    c1, c2 = st.columns(2)
    serie = agrupar(filtrado, ["mes", "segmento"])
    fig = px.line(serie, x="mes", y="morosidad_pct", color="segmento", markers=True,
                  title="Morosidad por segmento y mes (%)", labels={"morosidad_pct": "Morosidad %", "mes": ""})
    c1.plotly_chart(fig, width="stretch")
    fig = px.bar(por_seg.sort_values("improductiva"), x="improductiva", y="segmento", orientation="h",
                 text=por_seg.sort_values("improductiva")["morosidad_pct"].map("{:.1f}%".format),
                 title=f"Cartera improductiva por segmento ({mes_fin})",
                 labels={"improductiva": "USD", "segmento": ""})
    c2.plotly_chart(fig, width="stretch")
    st.info("Lectura: el porcentaje (etiqueta) y los dólares (barra) cuentan historias distintas. "
            "Un segmento puede tener la tasa más alta y, aun así, pesar poco en dólares.")

# ------------------------------------------------------------------ 2. Geografía
with tab2:
    c1, c2 = st.columns(2)
    hm = agrupar(fin, ["segmento", "region"]).pivot(index="segmento", columns="region", values="morosidad_pct")
    fig = px.imshow(hm, text_auto=".1f", color_continuous_scale="YlOrRd", aspect="auto",
                    title=f"Morosidad % · segmento x región ({mes_fin})")
    c1.plotly_chart(fig, width="stretch")
    prov = agrupar(fin, "provincia")
    prov = prov[prov["saldo_total"] >= cartera_min * 1e6].sort_values("morosidad_pct", ascending=False).head(10)
    fig = px.bar(prov.sort_values("morosidad_pct"), x="morosidad_pct", y="provincia", orientation="h",
                 title=f"Provincias más morosas (cartera >= USD {cartera_min} M)",
                 labels={"morosidad_pct": "Morosidad %", "provincia": ""})
    c2.plotly_chart(fig, width="stretch")
    reg = agrupar(fin, "region").sort_values("morosidad_pct", ascending=False)
    st.dataframe(reg.rename(columns={"saldo_total": "Cartera USD", "improductiva": "Improductiva USD",
                                     "morosidad_pct": "Morosidad %", "region": "Región"}),
                 width="stretch", hide_index=True)

# ------------------------------------------------------------------ 3. Entidades
with tab3:
    ent = agrupar(fin, "entidad")
    ent = ent[ent["saldo_total"] >= cartera_min * 1e6]
    fig = px.scatter(ent, x="saldo_total", y="morosidad_pct", size="improductiva", color="morosidad_pct",
                     hover_name="entidad", log_x=True, color_continuous_scale="YlOrRd", size_max=55,
                     title="Matriz de riesgo por entidad (burbuja = cartera improductiva)",
                     labels={"saldo_total": "Cartera USD (log)", "morosidad_pct": "Morosidad %"})
    fig.add_hline(y=tasa(fin), line_dash="dash", annotation_text="Promedio del sistema")
    st.plotly_chart(fig, width="stretch")
    ranking = agrupar(fin, "entidad").sort_values("improductiva", ascending=False)
    ranking["acumulado_%"] = ranking["improductiva"].cumsum() / ranking["improductiva"].sum() * 100
    st.subheader("Concentración de la cartera improductiva")
    st.caption(f"Las 5 primeras entidades concentran {ranking['acumulado_%'].iloc[:5].iloc[-1]:.1f}% del total.")
    st.dataframe(ranking.head(10).round(2), width="stretch", hide_index=True)

# ------------------------------------------------------------------ 4. Decisiones
with tab4:
    st.subheader("¿Qué decisión tomamos con estos datos?")
    combo_fin = agrupar(fin, ["segmento", "region"])
    combo_ini = agrupar(ini, ["segmento", "region"])[["segmento", "region", "saldo_total"]]
    combo = combo_fin.merge(combo_ini, on=["segmento", "region"], how="left", suffixes=("", "_ini"))
    combo["crecimiento_%"] = (combo["saldo_total"] / combo["saldo_total_ini"] - 1) * 100 if mes_ini != mes_fin else 0.0
    combo = combo[combo["saldo_total"] >= cartera_min * 1e6]

    alertas = combo[combo["morosidad_pct"] >= umbral_alerta].sort_values("improductiva", ascending=False)
    oportun = combo[(combo["morosidad_pct"] <= umbral_ok) & (combo["crecimiento_%"] >= 0)] \
        .sort_values("saldo_total", ascending=False)

    cols = {"segmento": "Segmento", "region": "Región", "saldo_total": "Cartera USD",
            "improductiva": "Improductiva USD", "morosidad_pct": "Morosidad %", "crecimiento_%": "Crec. cartera %"}
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### Reforzar provisiones o endurecer política (morosidad >= {umbral_alerta}%)")
        if alertas.empty:
            st.success("Ninguna combinación supera el umbral con los filtros actuales.")
        else:
            top = alertas.iloc[0]
            st.error(f"Prioridad 1: **{top['segmento']} en {top['region']}** "
                     f"(USD {top['improductiva'] / 1e6:,.0f} M improductivos, {top['morosidad_pct']:.1f}%).")
            st.dataframe(alertas[list(cols)].rename(columns=cols).round(2), width="stretch", hide_index=True)
    with c2:
        st.markdown(f"#### Candidatas a ampliar colocación (morosidad <= {umbral_ok}% y cartera creciendo)")
        if oportun.empty:
            st.info("Ninguna combinación cumple la regla con los filtros actuales.")
        else:
            top = oportun.iloc[0]
            st.success(f"Mayor cartera sana: **{top['segmento']} en {top['region']}** "
                       f"(USD {top['saldo_total'] / 1e9:,.1f} mil M, {top['morosidad_pct']:.1f}%).")
            st.dataframe(oportun[list(cols)].rename(columns=cols).round(2), width="stretch", hide_index=True)

    st.markdown("#### Monitoreo por Fenómeno de El Niño")
    costa = filtrado[filtrado["region"] == "Costa"]
    if costa.empty:
        st.caption("Incluye la región Costa en los filtros para ver su evolución.")
    else:
        serie_costa = agrupar(costa, ["mes", "segmento"])
        fig = px.line(serie_costa, x="mes", y="morosidad_pct", color="segmento", markers=True,
                      title="Morosidad en la Costa por segmento (%)", labels={"morosidad_pct": "Morosidad %", "mes": ""})
        st.plotly_chart(fig, width="stretch")
        st.caption("Con datos hasta agosto aún no se observa impacto climático; este gráfico sirve de línea base "
                   "para detectar un deterioro en los próximos cortes.")

# ------------------------------------------------------------------ 5. Datos
with tab5:
    st.dataframe(filtrado.drop(columns="fecha").head(500), width="stretch", hide_index=True)
    st.download_button("Descargar datos filtrados (CSV)", filtrado.to_csv(index=False).encode("utf-8"),
                       file_name="cartera_filtrada.csv", mime="text/csv")
    st.caption("Se muestran las primeras 500 filas; la descarga incluye todas las filas filtradas.")
