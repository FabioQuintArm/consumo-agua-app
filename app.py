import pandas as pd
import os
import sys
import streamlit as st

# --- Detectar la ruta del archivo CSV dentro del .exe o local ---
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

csv_path = os.path.join(base_path, 'dataset.csv')

# --- Cargar CSV sin caché y con codificación robusta ---
try:
    df = pd.read_csv(csv_path, sep=';', decimal=',', encoding='utf-8')
    df.columns = df.columns.str.strip().str.lower()  # Limpieza de nombres de columnas
except Exception as e:
    st.error(f"Error al cargar el archivo: {e}")
    df = pd.DataFrame()

st.subheader("📋 Primeras filas del dataset")
st.write(df.head())
st.write("Columnas detectadas:", df.columns.tolist())

st.title("Calculo de consumo de agua en cultivos")

cultivos_permanentes = ['Viñedo', 'Cítricos', 'Aguacate', 'Mango', 'Olivo', 'Platanera']
cultivos_no_permanentes = ['Tomate', 'Papaya', 'Papa', 'Pimiento', 'Calabací­n', 'Otras hortalizas']

months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
month_columns = {
    'Enero': 'ETo01',
    'Febrero': 'ETo02',
    'Marzo': 'ETo03',
    'Abril': 'ETo04',
    'Mayo': 'ETo05',
    'Junio': 'ETo06',
    'Julio': 'ETo07',
    'Agosto': 'ETo08',
    'Septiembre': 'ETo09',
    'Octubre': 'ETo10',
    'Noviembre': 'ETo11',
    'Diciembre': 'ETo12'
}

cultivos_kc = {
    'Viñedo':     dict.fromkeys(months, 0.3) | {'Marzo': 0.5, 'Abril': 0.7, 'Mayo': 0.75, 'Junio': 0.75, 'Julio': 0.75, 'Agosto': 0.7, 'Septiembre': 0.5, 'Octubre': 0.4},
    'Cí­tricos':   dict.fromkeys(months, 0.7) | {'Enero': 0.65, 'Febrero': 0.65, 'Noviembre': 0.65, 'Diciembre': 0.65},
    'Aguacate':   dict.fromkeys(months, 0.7) | {'Marzo': 0.75, 'Abril': 0.8, 'Mayo': 0.8, 'Junio': 0.8, 'Julio': 0.75, 'Agosto': 0.75},
    'Mango':      dict.fromkeys(months, 0.5) | {'Marzo': 0.6, 'Abril': 0.65, 'Mayo': 0.7, 'Junio': 0.7, 'Julio': 0.7, 'Agosto': 0.65, 'Septiembre': 0.6, 'Octubre': 0.55},
    'Olivo':      dict.fromkeys(months, 0.3) | {'Marzo': 0.4, 'Abril': 0.5, 'Mayo': 0.55, 'Junio': 0.6, 'Julio': 0.55, 'Agosto': 0.5, 'Septiembre': 0.4, 'Octubre': 0.35},
    'Platanera':  dict.fromkeys(months, 1.05) | {'Marzo': 1.1, 'Abril': 1.1, 'Mayo': 1.15, 'Junio': 1.15, 'Julio': 1.2, 'Agosto': 1.2, 'Septiembre': 1.15, 'Octubre': 1.1},
}

col1, col2 = st.columns(2)
provincia = col1.text_input("provincia")
municipio = col2.text_input("municipio")
poligono = col1.text_input("poli­gono")
parcela = col2.text_input("parcela")
recinto = col1.text_input("recinto")
superficie = col2.number_input("Superficie cultivada (m²)", min_value=1.0)

cultivo_tipo = st.radio("Tipo de cultivo", ["Permanente", "No permanente"])
if cultivo_tipo == "Permanente":
    cultivo = st.selectbox("Selecciona el cultivo", cultivos_permanentes)
    mes_inicio = None
    mes_fin = None
else:
    cultivo = st.selectbox("Selecciona el cultivo", cultivos_no_permanentes)
    mes_inicio = st.selectbox("Mes de inicio", months)
    mes_fin = st.selectbox("Mes de finalización", months)

st.subheader("🔍 Valores ingresados")
st.write("Provincia:", provincia)
st.write("Municipio:", municipio)
st.write("Polígono:", poligono)
st.write("Parcela:", parcela)
st.write("Recinto:", recinto)

coincidencias_parcela = df[
    (df['provincia'].astype(str).str.strip().str.lower() == str(provincia).strip().lower()) &
    (df['municipio'].astype(str).str.strip().str.lower() == str(municipio).strip().lower()) &
    (df['poligono'].astype(str).str.strip() == str(poligono).strip()) &
    (df['parcela'].astype(str).str.strip() == str(parcela).strip()) &
    (df['recinto'].astype(str).str.strip() == str(recinto).strip())
]

st.subheader("🔎 Coincidencias con filtro completo (nivel parcela)")
st.write("Cantidad de coincidencias:", len(coincidencias_parcela))
st.write(coincidencias_parcela.head())


# --- Cálculo al presionar el botón ---
if st.button("Calcular consumo"):
    parcela_data = df[
        (df['provincia'].astype(str).str.strip().str.lower() == str(provincia).strip().lower()) &
        (df['municipio'].astype(str).str.strip().str.lower() == str(municipio).strip().lower()) &
        (df['poligono'].astype(str).str.strip() == str(poligono).strip()) &
        (df['parcela'].astype(str).str.strip() == str(parcela).strip()) &
        (df['recinto'].astype(str).str.strip() == str(recinto).strip())
    ]

    if parcela_data.empty:
        st.error("Parcela no encontrada en el dataset.")
    else:
        # Definir meses segÃºn tipo de cultivo
        if cultivo_tipo == "Permanente":
            selected_months = months
            fase_kc = cultivos_kc[cultivo]
        else:
            idx_ini = months.index(mes_inicio)
            idx_fin = months.index(mes_fin)
            if idx_ini <= idx_fin:
                selected_months = months[idx_ini:idx_fin+1]
            else:
                selected_months = months[idx_ini:] + months[:idx_fin+1]

            # Kc por fase
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
        
        # Cálculo del consumo mensual
        resumen = []
        total = 0
    
  consumo_total = 0

    for mes in nombres_meses[mes_inicio - 1: mes_fin]:
    columna = month_columns[mes]
        try:
            eto = float(parcela_data[columna].values[0])
            consumo_mes = eto * kc * superficie / 1000
            consumo_total += consumo_mes
            st.write(f"{mes}: {consumo_mes:.2f} m³")
        except Exception as e:
            st.warning(f"No se pudo calcular para {mes}: {e}")


        # Mostrar resultados
        st.subheader("ðŸ“Š Resumen del consumo mensual")
        st.dataframe(pd.DataFrame(resumen, columns=["Mes", "ETo (mm)", "Kc", "Consumo (mÂ³)"]))
        st.success(f"ðŸ’§ Consumo total: {round(total, 2)} mÂ³")
