import streamlit as st
import pandas as pd              
import numpy as np
from datetime import date, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO
# ==========================================
st.set_page_config(page_title="TQ Auditoría ISO 9001", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; color: #004aad; }
    .stApp { background-color: #ffffff; }
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #dee2e6;
    }
    </style>
    """, unsafe_allow_html=True)

# Listas de Selección
CIUDADES_COL = ["Cali", "Bogotá", "Medellín", "Barranquilla", "Cartagena", "Bucaramanga", "Pereira", "Manizales", "Cúcuta", "Ibagué", "Santa Marta", "Neiva", "Villavicencio", "Pasto", "Tunja", "Armenia", "Popayán", "Sincelejo", "Valledupar", "Montería", "Quibdó", "Riohacha"]
REGIONES = ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Santanderes", "Eje Cafetero", "Pacífico", "Llanos Orientales"]
CANALES = ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa", "Distribuidor"]

COLUMNAS = ['Fecha', 'Nombre', 'Ciudad', 'Region', 'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones']

# ==========================================
# 2. INTELIGENCIA ISO 9001 (NUMERALES)
# ==========================================
SOLUCIONES_ISO = {
    "1. Calidad": {"numeral": "Numeral 8.7 (Control de salidas no conformes)", "accion": "Segregar producto, aplicar cuarentena y análisis de lote en laboratorio."},
    "2. Precios": {"numeral": "Numeral 8.2.1 (Comunicación con el cliente)", "accion": "Auditoría de facturación y revisión de listas de precios vigentes."},
    "3. Logística": {"numeral": "Numeral 8.4 (Control de procesos externos/Suministros)", "accion": "Revaluar proveedor logístico y optimizar tiempos de entrega (OTIF)."},
    "4. Agotados": {"numeral": "Numeral 8.1 (Planificación y control operacional)", "accion": "Revisar pronósticos de demanda y ajustar stock de seguridad."},
    "5. Atención": {"numeral": "Numeral 7.2 (Competencia)", "accion": "Programa de capacitación en protocolos de servicio y trazabilidad."},
    "10. Otro": {"numeral": "Numeral 10.2 (No conformidad y acción correctiva)", "accion": "Realizar análisis de causa raíz mediante 5 Porqués o Ishikawa."}
}

# ==========================================
# 3. GESTIÓN DE DATOS
# ==========================================
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=COLUMNAS)

# ==========================================
# 4. SIDEBAR (ENTRADA DE DATOS)
# ==========================================
# Quitamos la imagen molesta y dejamos solo el título limpio
st.sidebar.title("🛠️ Registro de Auditoría TQ")
st.sidebar.markdown("---")

with st.sidebar.form("formulario_registro", clear_on_submit=True):
    nombre = st.text_input("Nombre del Cliente/Punto")
    ciudad = st.selectbox("Ciudad / Municipio", sorted(CIUDADES_COL))
    region = st.selectbox("Región Estratégica", REGIONES)
    canal = st.selectbox("Canal de Atención", CANALES)
    
    st.markdown("---")
    sat = st.slider("Satisfacción (%)", 0, 100, 85)
    reclamos = st.number_input("Cantidad PQRS", 0, 50, 0)
    motivo = st.selectbox("Categoría de Falla", ["Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención", "10. Otro"])
    obs = st.text_area("Observaciones del Auditor")
    
    btn_guardar = st.form_submit_button("💾 REGISTRAR EN BASE DE DATOS")

if btn_guardar:
    if nombre:
        nuevo = pd.DataFrame([[str(date.today()), nombre, ciudad, region, canal, sat, reclamos, motivo, obs]], columns=COLUMNAS)
        st.session_state.db = pd.concat([st.session_state.db, nuevo], ignore_index=True)
        st.toast("Registro Exitoso", icon="✅")
    else:
        st.error("El nombre del cliente es obligatorio.")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Eliminar Último Registro"):
    if not st.session_state.db.empty:
        st.session_state.db = st.session_state.db.iloc[:-1]
        st.rerun()

# Botón de Descarga
csv = st.session_state.db.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Descargar Data Master", csv, "auditoria_tq.csv", "text/csv")

# ==========================================
# 5. DASHBOARD (ANÁLISIS BI)
# ==========================================
st.title("🛡️ Sistema Integral de Gestión de Calidad TQ")

tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD ANALÍTICO", "🗄️ TRAZABILIDAD (HISTÓRICO)", "📑 INFORME ISO 9001"])

with tab1:
    if st.session_state.db.empty:
        st.info("No hay datos registrados. Por favor use el panel lateral.")
    else:
        # FILTROS
        f1, f2 = st.columns(2)
        with f1:
            f_reg = st.multiselect("Filtrar Región", options=REGIONES, default=REGIONES)
        with f2:
            f_can = st.multiselect("Filtrar Canal", options=CANALES, default=CANALES)
        
        df_f = st.session_state.db[(st.session_state.db['Region'].isin(f_reg)) & (st.session_state.db['Canal'].isin(f_can))]

        # MÉTRICAS
        m1, m2, m3, m4 = st.columns(4)
        avg_s = df_f['Satisfaccion'].mean() if not df_f.empty else 0
        m1.metric("Satisfacción Promedio", f"{avg_s:.1f}%")
        m2.metric("Total Auditorías", len(df_f))
        m3.metric("PQRS Totales", int(df_f['Reclamos'].sum()))
        m4.metric("Estado", "Óptimo" if avg_s > 80 else "En Alerta", delta_color="normal")

        # GRÁFICAS
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Tendencia de Calidad**")
            st.line_chart(df_f.groupby('Fecha')['Satisfaccion'].mean())
        with c2:
            st.markdown("**Pareto de Fallas (PQRS)**")
            f_fallas = df_f[df_f['Motivo PQRS'] != "Ninguna (0 PQRS)"]
            if not f_fallas.empty:
                st.bar_chart(f_fallas['Motivo PQRS'].value_counts())
            else:
                st.success("Sin fallas en este segmento")

with tab2:
    st.subheader("📁 Histórico de Trazabilidad")
    st.write("Puede editar celdas directamente. Use **Ctrl+Z** para deshacer cambios antes de guardar.")
    
    # El editor permite borrar filas seleccionando el cuadro de la izquierda y dando 'Delete'
    edited_db = st.data_editor(st.session_state.db, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 Guardar Cambios Editados"):
        st.session_state.db = edited_db
        st.success("Base de datos sincronizada.")

with tab3:
    st.subheader("📑 Dictamen Técnico de Auditoría")
    if st.session_state.db.empty:
        st.warning("No hay datos para generar el dictamen.")
    else:
        df_fallas_iso = st.session_state.db[st.session_state.db['Motivo PQRS'] != "Ninguna (0 PQRS)"]
        
        if not df_fallas_iso.empty:
            principal_falla = df_fallas_iso['Motivo PQRS'].mode()[0]
            info_iso = SOLUCIONES_ISO.get(principal_falla, {"numeral": "No especificado", "accion": "Revisión general"})
            
            st.error(f"### Hallazgo Crítico Detectado")
            st.markdown(f"**Motivo más frecuente:** {principal_falla}")
            st.markdown(f"**Referencia Normativa:** {info_iso['numeral']}")
            
            st.markdown("---")
            st.info(f"#### 💡 Plan de Acción Sugerido")
            st.write(info_iso['accion'])
            
            st.markdown("---")
            st.warning("**Nota:** Este dictamen es automático basado en la recurrencia de datos.")
        else:
            st.success("### ✅ Dictamen: CONFORME")
            st.write("El sistema no presenta desviaciones ni No Conformidades. Se recomienda seguir con el plan de mantenimiento preventivo.")

st.caption("Tecnoquímicas S.A. | Auditoría Digital v3.0 | 2026")
