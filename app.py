import pandas as pd
import streamlit as st
from pathlib import Path

# Cargar CSV
csv_path = Path(__file__).parent / "Dataset.csv"

try:
    df = pd.read_csv(csv_path, sep=';', decimal=',', encoding='utf-8')
    df.columns = df.columns.str.strip().str.lower()
except Exception as e:
    st.error(f"Error al cargar el archivo: {e}")
    df = pd.DataFrame()

st.title("Cálculo de Consumo de Agua en Cultivos")

# Entradas
st.header("📋 Formulario de entrada")
col1, col2 = st.columns(2)
with col1:
    provincia = st.text_input("Provincia")
    municipio = st.text_input("Municipio")
    poligono = st.text_input("Polígono")
with col2:
    parcela = st.text_input("Parcela")
    recinto = st.text_input("Recinto")
    superficie = st.number_input("Superficie (m²)", min_value=0.0, step=0.1)

cultivo_tipo = st.selectbox("Tipo de cultivo", ["Permanente", "No permanente"])

# Columnas de ETo
month_columns = {
    'Enero': 'eto01', 'Febrero': 'eto02', 'Marzo': 'eto03', 'Abril': 'eto04',
    'Mayo': 'eto05', 'Junio': 'eto06', 'Julio': 'eto07', 'Agosto': 'eto08',
    'Septiembre': 'eto09', 'Octubre': 'eto10', 'Noviembre': 'eto11', 'Diciembre': 'eto12'
}
month_names = list(month_columns.keys())

if cultivo_tipo == "No permanente":
    mes_inicio = st.selectbox("Mes de inicio", month_names)
    mes_fin = st.selectbox("Mes de fin", month_names)
else:
    mes_inicio = None
    mes_fin = None

# Kc base por cultivo permanente
cultivos_kc = {
    'Viñedo': 0.7, 'Cítricos': 0.65, 'Aguacate': 0.6,
    'Mango': 0.6, 'Olivo': 0.55, 'Platanera': 0.75
}

cultivo = st.selectbox("Cultivo", list(cultivos_kc.keys()) if cultivo_tipo == "Permanente"
                       else ['Tomate', 'Papaya', 'Papa', 'Pimiento', 'Calabacín', 'Otras hortalizas'])

# Botón
if st.button("Calcular consumo"):
    parcela_data = df[
        (df['provincia'].astype(str).str.strip().str.lower() == provincia.strip().lower()) &
        (df['municipio'].astype(str).str.strip().str.lower() == municipio.strip().lower()) &
        (df['poligono'].astype(str).str.strip() == str(poligono).strip()) &
        (df['parcela'].astype(str).str.strip() == str(parcela).strip()) &
        (df['recinto'].astype(str).str.strip() == str(recinto).strip())
    ]

    if parcela_data.empty:
        st.error("Parcela no encontrada en el dataset.")
    else:
        mes_a_num = {mes: i+1 for i, mes in enumerate(month_names)}

        if cultivo_tipo == "Permanente":
            selected_months = month_names
            fase_kc = {mes: cultivos_kc[cultivo] for mes in month_names}
        else:
            idx_ini = month_names.index(mes_inicio)
            idx_fin = month_names.index(mes_fin)
            if idx_ini <= idx_fin:
                selected_months = month_names[idx_ini:idx_fin+1]
            else:
                selected_months = month_names[idx_ini:] + month_names[:idx_fin+1]

            fase_kc = {}
            for i, mes in enumerate(selected_months):
                if i == 0:
                    fase_kc[mes] = 0.5
                elif i == 1:
                    fase_kc[mes] = 0.7
                elif i == len(selected_months) - 1:
                    fase_kc[mes] = 0.8
                else:
                    fase_kc[mes] = 1.05

        consumo_total = 0.0
        resumen = []

        for mes in selected_months:
            columna = month_columns[mes]
            try:
                eto = float(parcela_data[columna].values[0])
                kc = fase_kc[mes]
                consumo_mes = eto * kc * superficie / 1000
                consumo_total += consumo_mes
                resumen.append([mes, eto, kc, consumo_mes])
                st.write(f"{mes}: {consumo_mes:.2f} m³")
            except Exception as e:
                st.warning(f"No se pudo calcular para {mes}: {e}")

        st.subheader("📊 Resumen del consumo mensual")
        st.dataframe(pd.DataFrame(resumen, columns=["Mes", "ETo (mm)", "Kc", "Consumo (m³)"]))
        st.success(f"💧 Consumo total: {consumo_total:.2f} m³")

