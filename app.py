import streamlit as st
import pandas as pd              
import numpy as np
from datetime import date, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO EMPRESARIAL
# ==========================================
st.set_page_config(page_title="TQ Auditoría Pro - Business Intelligence", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; }
    .stApp { background-color: #ffffff; }
    .main-card {
        background-color: #f1f4f9;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #004aad;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Listas de Datos
CIUDADES_COL = ["Cali", "Bogotá", "Medellín", "Barranquilla", "Cartagena", "Bucaramanga", "Pereira", "Manizales", "Cúcuta", "Ibagué", "Santa Marta", "Neiva", "Villavicencio", "Pasto", "Armenia", "Popayán"]
REGIONES = ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Santanderes", "Eje Cafetero", "Pacífico", "Llanos Orientales"]
CANALES = ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa", "Distribuidor"]

COLUMNAS = ['Fecha', 'Nombre Consumidor', 'Contacto', 'Ciudad Residencia', 'Region', 'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones']

# --- ISO 9001 Dictionary ---
SOLUCIONES_ISO = {
    "1. Calidad": {"numeral": "8.7 (Salidas No Conformes)", "accion": "Segregar producto y análisis de lote."},
    "2. Precios": {"numeral": "8.2.1 (Comunicación)", "accion": "Revisión de listas de precios y facturación."},
    "3. Logística": {"numeral": "8.4 (Suministros Externos)", "accion": "Optimizar tiempos de entrega (OTIF)."},
    "4. Agotados": {"numeral": "8.1 (Control Operacional)", "accion": "Ajustar stock de seguridad y demanda."},
    "5. Atención": {"numeral": "7.2 (Competencia)", "accion": "Capacitación en protocolos de servicio."},
    "10. Otro": {"numeral": "10.2 (Acción Correctiva)", "accion": "Análisis causa raíz (Ishikawa)."}
}

# ==========================================
# 2. GESTIÓN DE DATOS (DATA CORE)
# ==========================================
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=COLUMNAS)

# ==========================================
# 3. SIDEBAR (INGRESO DE DATOS)
# ==========================================
st.sidebar.title("🏢 Tecnoquímicas S.A.")
st.sidebar.subheader("Panel de Carga Auditoría")

with st.sidebar.form("form_carga", clear_on_submit=True):
    nombre_c = st.text_input("Nombre Consumidor / Punto")
    contacto = st.text_input("Contacto (Tel/Email)")
    ciudad_r = st.selectbox("Ciudad Residencia", sorted(CIUDADES_COL))
    region = st.selectbox("Región", REGIONES)
    canal = st.selectbox("Canal de Atención", CANALES)
    
    st.markdown("---")
    sat = st.slider("Nivel Satisfacción (%)", 0, 100, 85)
    reclamos = st.number_input("Cantidad PQRS", 0, 50, 0)
    motivo = st.selectbox("Motivo PQRS", ["Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención", "10. Otro"])
    obs = st.text_area("Observaciones")
    
    btn_guardar = st.form_submit_button("🚀 GUARDAR DATOS")

if btn_guardar:
    if nombre_c and contacto:
        # Guardamos con la fecha exacta para filtros de tiempo
        nuevo = pd.DataFrame([[pd.Timestamp.now().date(), nombre_c, contacto, ciudad_r, region, canal, sat, reclamos, motivo, obs]], columns=COLUMNAS)
        st.session_state.db = pd.concat([st.session_state.db, nuevo], ignore_index=True)
        st.toast("Dato Almacenado", icon="✅")
    else:
        st.error("Nombre y Contacto son obligatorios.")

# Controles rápidos en Sidebar
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Eliminar Último"):
    if not st.session_state.db.empty:
        st.session_state.db = st.session_state.db.iloc[:-1]
        st.rerun()

csv = st.session_state.db.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Exportar Data Master", csv, "auditoria_tq.csv")

# ==========================================
# 4. DASHBOARD - INTELIGENCIA EJECUTIVA
# ==========================================
st.title("🛡️ Sistema TQ Intelligence - Canal Ventas")

tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD BI", "📁 TRAZABILIDAD", "📑 INFORME ISO"])

with tab1:
    if st.session_state.db.empty:
        st.info("Sin datos. Registre auditorías para activar el BI.")
    else:
        # --- FILTROS DE TIEMPO Y SEGMENTOS ---
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1:
            rango = st.selectbox("📅 Rango Temporal", ["Todo", "Hoy", "Últimos 7 días"])
        with c_f2:
            f_reg = st.multiselect("📍 Región", options=REGIONES, default=REGIONES)
        with c_f3:
            f_can = st.multiselect("🔄 Canal", options=CANALES, default=CANALES)

        # Lógica de filtrado
        df_f = st.session_state.db.copy()
        df_f['Fecha'] = pd.to_datetime(df_f['Fecha']).dt.date
        if rango == "Hoy":
            df_f = df_f[df_f['Fecha'] == date.today()]
        elif rango == "Últimos 7 días":
            df_f = df_f[df_f['Fecha'] >= (date.today() - timedelta(days=7))]
        
        df_f = df_f[(df_f['Region'].isin(f_reg)) & (df_f['Canal'].isin(f_can))]

        # --- KPI CARDS (SEMÁFORO GERENCIAL) ---
        avg_sat = df_f['Satisfaccion'].mean() if not df_f.empty else 0
        total_pqrs = df_f['Reclamos'].sum()

        # Lógica Semáforo
        sem_color = "🔴 Crítico" if avg_sat < 60 or total_pqrs > 10 else "🟡 Riesgo" if avg_sat < 80 else "🟢 Controlado"
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Satisfacción", f"{avg_sat:.1f}%")
        m2.metric("Total PQRS", int(total_pqrs))
        m3.metric("Auditorías", len(df_f))
        st.markdown(f"**Estado Gerencial:** {sem_color}")

        # --- DOBLE GRÁFICA COMPARATIVA ---
        st.markdown("### 📈 Análisis de Desempeño Comparativo")
        g1, g2 = st.columns(2)
        
        with g1:
            st.write("**Selección Actual vs Tendencia General**")
            # Comparación: Datos filtrados vs todos los datos
            chart_base = st.session_state.db.groupby('Region')['Satisfaccion'].mean()
            st.bar_chart(chart_base)
        
        with g2:
            st.write("**Participación por Motivo de Falla**")
            df_fallas = df_f[df_f['Motivo PQRS'] != "Ninguna (0 PQRS)"]
            if not df_fallas.empty:
                st.bar_chart(df_fallas['Motivo PQRS'].value_counts())
            else:
                st.success("No hay fallas en este periodo.")

with tab2:
    st.subheader("📁 Gestión de Datos Master")
    st.write("Edite directamente. Selección + 'Delete' para borrar filas.")
    # El editor permite sincronizar cambios manuales
    edited_db = st.data_editor(st.session_state.db, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Sincronizar Cambios"):
        st.session_state.db = edited_db
        st.success("Base de datos actualizada.")

with tab3:
    st.subheader("📑 Dictamen Técnico ISO 9001")
    df_err = st.session_state.db[st.session_state.db['Motivo PQRS'] != "Ninguna (0 PQRS)"]
    
    if df_err.empty:
        st.success("### ✅ CONFORME\nNo hay hallazgos registrados.")
    else:
        # FIX: Validación de Moda para evitar el "Error Potencial"
        moda_serie = df_err['Motivo PQRS'].mode()
        
        if not moda_serie.empty:
            top_falla = moda_serie[0]
            info = SOLUCIONES_ISO.get(top_falla, {"numeral": "N/A", "accion": "Revisión técnica."})
            
            st.error(f"### Hallazgo: {top_falla}")
            st.markdown(f"**Referencia:** {info['numeral']}")
            st.info(f"**Acción Correctiva:** {info['accion']}")
        else:
            st.info("Datos insuficientes para calcular tendencia de falla.")

st.caption("Tecnoquímicas S.A. | Auditoría BI Enterprise | 2026")
