import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Auditoría TQ", layout="wide")

st.title("🩺 Sistema de Auditoría - Calidad TQ")
st.markdown("Plataforma de registro y control de hallazgos (ISO 9001).")

with st.sidebar:
    st.header("👤 Datos del Auditor")
    auditor = st.selectbox("Seleccionar auditor", ["Jhon Sierra", "Otro Auditor"])
    sede = st.selectbox("Sede", ["Bogotá", "Cali", "Medellín", "Barranquilla"])
    fecha = st.date_input("Fecha", date.today())

st.subheader("📝 Registro de Hallazgos")
col1, col2 = st.columns(2)

with col1:
    proceso = st.selectbox("Proceso", ["Empaque", "Producción", "Logística", "Calidad"])
    riesgo = st.selectbox("Riesgo", ["🟢 Bajo", "🟡 Medio", "🔴 Alto"])

with col2:
    hallazgo = st.text_area("Descripción", placeholder="Escriba aquí...")
    evidencia = st.file_uploader("📸 Evidencia", type=['jpg', 'png', 'jpeg'])

if 'datos' not in st.session_state:
    st.session_state.datos = []

if st.button("💾 Registrar Auditoría"):
    if hallazgo:
        st.session_state.datos.append({"Fecha": fecha, "Auditor": auditor, "Proceso": proceso, "Hallazgo": hallazgo})
        st.success("✅ Registrado")

st.markdown("---")
if st.session_state.datos:
    st.write("### 📊 Registros", pd.DataFrame(st.session_state.datos))
