import pandas as pd
import os
import sys

# --- Detectar la ruta del archivo CSV dentro del .exe o local ---
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

csv_path = os.path.join(base_path, 'Dataset.csv')

# --- Cargar CSV sin caché y con codificación robusta ---
try:
    df = pd.read_csv(csv_path, sep=';', decimal=',', encoding='utf-8', errors='replace')
except Exception as e:
    import streamlit as st
    st.error(f"Error al cargar el archivo: {e}")
    df = pd.DataFrame()
st.write("Columnas disponibles:", df.columns.tolist())

st.title("Calculo de consumo de agua en cultivos")

cultivos_permanentes = ['Viñedo', 'Cítricos', 'Aguacate', 'Mango', 'Olivo', 'Platanera']
cultivos_no_permanentes = ['Tomate', 'Papaya', 'Papa', 'Pimiento', 'Calabací­n', 'Otras hortalizas']

months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

cultivos_kc = {
    'Viñedo':     dict.fromkeys(months, 0.3) | {'Marzo': 0.5, 'Abril': 0.7, 'Mayo': 0.75, 'Junio': 0.75, 'Julio': 0.75, 'Agosto': 0.7, 'Septiembre': 0.5, 'Octubre': 0.4},
    'Cí­tricos':   dict.fromkeys(months, 0.7) | {'Enero': 0.65, 'Febrero': 0.65, 'Noviembre': 0.65, 'Diciembre': 0.65},
    'Aguacate':   dict.fromkeys(months, 0.7) | {'Marzo': 0.75, 'Abril': 0.8, 'Mayo': 0.8, 'Junio': 0.8, 'Julio': 0.75, 'Agosto': 0.75},
    'Mango':      dict.fromkeys(months, 0.5) | {'Marzo': 0.6, 'Abril': 0.65, 'Mayo': 0.7, 'Junio': 0.7, 'Julio': 0.7, 'Agosto': 0.65, 'Septiembre': 0.6, 'Octubre': 0.55},
    'Olivo':      dict.fromkeys(months, 0.3) | {'Marzo': 0.4, 'Abril': 0.5, 'Mayo': 0.55, 'Junio': 0.6, 'Julio': 0.55, 'Agosto': 0.5, 'Septiembre': 0.4, 'Octubre': 0.35},
    'Platanera':  dict.fromkeys(months, 1.05) | {'Marzo': 1.1, 'Abril': 1.1, 'Mayo': 1.15, 'Junio': 1.15, 'Julio': 1.2, 'Agosto': 1.2, 'Septiembre': 1.15, 'Octubre': 1.1},
}

month_columns = {
    'Enero': 'ETo01', 'Febrero': 'ETo02', 'Marzo': 'ETo03', 'Abril': 'ETo04',
    'Mayo': 'ETo05', 'Junio': 'ETo06', 'Julio': 'ETo07', 'Agosto': 'ETo08',
    'Septiembre': 'ETo09', 'Octubre': 'ETo10', 'Noviembre': 'ETo11', 'Diciembre': 'Eto12'
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

# --- Cálculo al presionar el botón ---
if st.button("Calcular consumo"):
    parcela_data = df[
        (df['provincia'] == provincia) &
        (df['municipio'] == municipio) &
        (df['poligono'] == poligono) &
        (df['parcela'] == parcela) &
        (df['recinto'] == recinto)
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

        for mes in selected_months:
            try:
                eto_raw = parcela_data.iloc[0][month_columns[mes]]
                eto = float(str(eto_raw).replace(',', '.'))
                kc = fase_kc[mes]
                consumo = eto * kc * superficie / 1000
                resumen.append([mes, round(eto, 2), round(kc, 2), round(consumo, 2)])
                total += consumo
            except Exception as e:
                st.warning(f"No se pudo calcular para {mes}: {e}")

        # Mostrar resultados
        st.subheader("ðŸ“Š Resumen del consumo mensual")
        st.dataframe(pd.DataFrame(resumen, columns=["Mes", "ETo (mm)", "Kc", "Consumo (mÂ³)"]))
        st.success(f"ðŸ’§ Consumo total: {round(total, 2)} mÂ³")
