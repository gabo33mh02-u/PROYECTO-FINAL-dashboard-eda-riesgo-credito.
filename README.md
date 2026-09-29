# Riesgo de crédito de la banca privada del Ecuador (enero - agosto 2026)

Proyecto final · **Dashboard EDA por profesión** · Profesión: **Finanzas (análisis de riesgo de crédito)**

## Problema y decisión
Un analista de riesgo de un banco privado debe decidir **dónde reforzar provisiones y dónde ampliar la colocación**.
El dashboard responde: ¿qué segmentos de crédito, regiones y entidades concentran más morosidad?

**Morosidad** = (cartera que no devenga intereses + cartera vencida) / saldo total. Se agrega de forma ponderada.

## Datos
Datos **reales** de la Superintendencia de Bancos del Ecuador, Portal Estadístico, sección *Cartera y Depósitos*, Año 2026, banca privada, corte agosto 2026:
consumo, productivo, microcrédito y vivienda (inmobiliario y vivienda de interés público).
Se usan las hojas `BASE ...` de cada Excel (formato tabla: entidad, provincia, cantón, mes, montos).

No se simularon datos.

## Estructura del repositorio
```
├── app.py                      # dashboard Streamlit
├── preparar_datos.py           # limpieza: data/raw -> data/processed (mismo proceso del notebook)
├── requirements.txt
├── notebooks/
│   └── EDA_cartera_banca_privada.ipynb   # EDA en 7 pasos
├── data/
│   ├── raw/                    # 4 Excel originales de la Superintendencia de Bancos
│   └── processed/              # cartera_banca_privada_2026.csv (13.765 filas)
└── docs/                       # documento del proyecto (PDF)
```

## Cómo ejecutarlo
```bash
pip install -r requirements.txt
python preparar_datos.py          # opcional: regenera el CSV limpio
streamlit run app.py              # abre el dashboard
pip install jupyter               # solo para abrir el notebook
jupyter notebook notebooks/EDA_cartera_banca_privada.ipynb
```

## EDA en 7 pasos (notebook)
1. Pregunta · 2. Estructura · 3. Univariado · 4. Bivariado · 5. Faltantes y atípicos · 6. Segmentación · 7. Hallazgos

## Decisiones metodológicas clave
- Morosidad **ponderada** (suma/suma), no promedio de porcentajes.
- Filas con saldo < USD 100 mil (16% de las filas, 0,014% del saldo) se excluyen solo de los rankings a nivel cantón-entidad; los agregados usan todos los datos.
- 13 filas duplicadas de BP Pichincha (Quito) se consolidan sumando.
- Región asignada por provincia (Costa, Sierra, Oriente, Insular); Santo Domingo de los Tsáchilas se clasifica en Sierra.

## Limitaciones
Solo banca privada (sin cooperativas ni banca pública), sin datos de provisiones, ocho meses de historia.
La morosidad aquí es una definición propia (improductiva / saldo) y puede diferir levemente de la cifra oficial.

## Dashboard en línea
Enlace: _(pegar aquí la URL de Streamlit Community Cloud)_
