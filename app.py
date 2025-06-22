import streamlit as st
import pandas as pd
import joblib
import io

# Cargar modelo y columnas
modelo = joblib.load('modelo_arbol.joblib')
columnas_modelo = joblib.load('columnas_modelo.joblib')

# Diccionarios para transformar datos
mapeo_caracter_estrato = {
    'PRIVADO1': 0, 'PRIVADO2': 1, 'PRIVADO3': 2, 'PRIVADO4': 3, 'PRIVADO5': 4,
    'PÚBLICO1': 5, 'PÚBLICO2': 6, 'PÚBLICO3': 7, 'PÚBLICO4': 8, 'PÚBLICO5': 9
}
mapeo_desplazado = {'NO': 0, 'SÍ': 1}

# Función para clasificar alerta
def clasificar_alerta(pred, promedio):
    if pred == 0 and promedio < 3.9:
        return 'CRÍTICA'
    elif pred == 0:
        return 'LEVE'
    else:
        return 'SIN_ALERTA'

# Función para generar Excel en memoria
@st.cache_data
def convertir_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# Interfaz principal
st.set_page_config(page_title="Predicción Académica", layout="centered")
st.title("🎓 Modelo de Riesgo Académico")

# Selector de modo
opcion = st.radio("Selecciona un modo de uso:", ["📥 Predicción con archivo", "🧍 Predicción individual"])

# --------------------------
# Modo 1: Predicción por archivo
# --------------------------
if opcion == "📥 Predicción con archivo":
    st.header("📂 Subir archivo Excel")
    archivo = st.file_uploader("Selecciona un archivo .xlsx con los datos de estudiantes", type=["xlsx"])

    if archivo is not None:
        df = pd.read_excel(archivo)

        try:
            df = df.replace({r',': '.', r'\xa0': ''}, regex=True)
            columnas_numericas = ['N1', 'N2', 'PROMEDIO_ACUMULADO', 'EDAD']
            df[columnas_numericas] = df[columnas_numericas].astype(float)
            df['caracter_estrato'] = df['CARACTER_ESTRATO'].map(mapeo_caracter_estrato)
            df['desplazado'] = df['DESPLAZADO'].map(mapeo_desplazado)

            X = df[columnas_modelo]

            predicciones = modelo.predict(X)
            df['Predicción'] = predicciones
            df['TIPO_ALERTA'] = df.apply(lambda fila: clasificar_alerta(fila['Predicción'], fila['PROMEDIO_ACUMULADO']), axis=1)

            st.success("✅ Predicciones generadas")
            st.dataframe(df[['N1', 'N2', 'PROMEDIO_ACUMULADO', 'Predicción', 'TIPO_ALERTA']])

            st.download_button(
                label="📥 Descargar resultados en Excel",
                data=convertir_a_excel(df),
                file_name="predicciones_resultado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"⚠️ Error procesando el archivo: {e}")

# --------------------------
# Modo 2: Predicción individual
# --------------------------
else:
    st.header("🧍 Ingresar datos del estudiante")

    N1 = st.number_input("Nota N1", min_value=0.0, max_value=5.0, step=0.1)
    N2 = st.number_input("Nota N2", min_value=0.0, max_value=5.0, step=0.1)
    PROMEDIO_ACUMULADO = st.number_input("Promedio acumulado", min_value=0.0, max_value=5.0, step=0.1)
    EDAD = st.number_input("Edad", min_value=10, max_value=100, step=1)
    CARACTER_ESTRATO = st.selectbox("Carácter y estrato", list(mapeo_caracter_estrato.keys()))
    DESPLAZADO = st.selectbox("¿Desplazado?", list(mapeo_desplazado.keys()))

    if st.button("🔍 Predecir resultado"):
        datos = pd.DataFrame([[
            N1,
            N2,
            PROMEDIO_ACUMULADO,
            EDAD,
            mapeo_caracter_estrato[CARACTER_ESTRATO],
            mapeo_desplazado[DESPLAZADO]
        ]], columns=columnas_modelo)

        pred = modelo.predict(datos)[0]
        alerta = clasificar_alerta(pred, PROMEDIO_ACUMULADO)

        resultado_texto = "✅ El estudiante APROBARÍA" if pred == 1 else "❌ El estudiante REPROBARÍA"
        st.subheader(resultado_texto)
        st.markdown(f"### 🛑 Tipo de alerta: **{alerta}**")
