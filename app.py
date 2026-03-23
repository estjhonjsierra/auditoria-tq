import streamlit as st
import pandas as pd              
import numpy as np
from datetime import date, timedelta

# ==========================================
# 1. CONFIGURACIÓN DE ALTO NIVEL
# ==========================================
st.set_page_config(page_title="TQ Auditoría - Control de Calidad ISO", layout="wide")

# Estilo profesional para métricas y fondo
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; color: #003366; }
    .stApp { background-color: #f4f7f9; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e1e4e8;
    }
    </style>
    """, unsafe_allow_html=True)

COLUMNAS = [
    'Fecha', 'Nombre', 'Ciudad', 'Region', 'Canal', 
    'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'
]

# ==========================================
# 2. GESTIÓN DE MEMORIA (DATA CORE)
# ==========================================
if 'db' not in st.session_state:
    seeds = [
        [str(date.today()), "Farmacia Central", "Cali", "Valle", "Ventas", 85, 0, "Ninguna (0 PQRS)", "Todo OK"],
        [str(date.today() - timedelta(days=1)), "Droguería XYZ", "Medellín", "Antioquia", "Digital", 40, 3, "3. Logística", "Retraso entrega"]
    ]
    st.session_state.db = pd.DataFrame(seeds, columns=COLUMNAS)

# ==========================================
# 3. SIDEBAR: PANEL DE CONTROL TÉCNICO
# ==========================================
# Logo TQ limpio
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Tecnoqu%C3%ADmicas_logo.svg/1200px-Tecnoqu%C3%ADmicas_logo.svg.png", width=180)
st.sidebar.title("📥 Registro de Auditoría")

with st.sidebar.form("input_form", clear_on_submit=True):
    nombre = st.sidebar.text_input("Nombre del Cliente")
    ciudad = st.sidebar.text_input("Ciudad / Municipio")
    region = st.sidebar.selectbox("Región Estratégica", ["Antioquia", "Bogotá", "Valle", "Costa", "Santanderes"])
    canal = st.sidebar.select_slider("Canal de Atención", options=["Ventas", "Mercadeo", "Digital"])
    
    st.sidebar.markdown("---")
    sat = st.sidebar.slider("Satisfacción (%)", 0, 100, 80)
    reclamos = st.sidebar.number_input("Cantidad de PQRS", 0, 100, 0)
    motivo = st.sidebar.selectbox("Categoría de Falla", ["Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención"])
    obs = st.sidebar.text_area("Notas Técnicas")
    
    btn_guardar = st.form_submit_button("🚀 GUARDAR REGISTRO")

if btn_guardar:
    if nombre and ciudad:
        nuevo_reg = pd.DataFrame([[str(date.today()), nombre, ciudad, region, canal, sat, reclamos, motivo, obs]], columns=COLUMNAS)
        st.session_state.db = pd.concat([st.session_state.db, nuevo_reg], ignore_index=True)
        st.toast("Guardado en Base de Datos Principal", icon="✅")
    else:
        st.sidebar.warning("⚠️ Complete Cliente y Ciudad.")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Mantenimiento de Datos")

# BOTÓN ELIMINAR ÚLTIMO (ELIMINACIÓN RÁPIDA)
if st.sidebar.button("🗑️ Eliminar Último Registro"):
    if not st.session_state.db.empty:
        st.session_state.db = st.session_state.db.drop(st.session_state.db.index[-1])
        st.sidebar.error("Último registro eliminado.")
        st.rerun()

# DESCARGA DE DATOS
csv = st.session_state.db.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="📥 DESCARGAR DATA MASTER (CSV)",
    data=csv,
    file_name=f"Data_Master_TQ_{date.today()}.csv",
    mime="text/csv",
)

# ==========================================
# 4. DASHBOARD ANALÍTICO (NIVEL BI)
# ==========================================
st.title("🛡️ Sistema de Auditoría TQ - Canal Ventas")
st.markdown("---")

# --- FILTROS DE SEGMENTACIÓN ---
f_col1, f_col2 = st.columns(2)
with f_col1:
    f_region = st.multiselect("📍 Filtrar por Región", options=st.session_state.db['Region'].unique(), default=st.session_state.db['Region'].unique())
with f_col2:
    f_canal = st.multiselect("🔄 Filtrar por Canal", options=st.session_state.db['Canal'].unique(), default=st.session_state.db['Canal'].unique())

df_filtrado = st.session_state.db[(st.session_state.db['Region'].isin(f_region)) & (st.session_state.db['Canal'].isin(f_canal))]

# --- KPI CARDS ---
m1, m2, m3, m4 = st.columns(4)
avg_sat = df_filtrado['Satisfaccion'].mean() if not df_filtrado.empty else 0
status_color = "normal" if avg_sat > 80 else "inverse" if avg_sat < 60 else "off"

m1.metric("Satisfacción Global", f"{avg_sat:.1f}%", delta=f"{avg_sat-80:.1f}% vs Meta", delta_color=status_color)
m2.metric("Total Auditorías", len(df_filtrado))
m3.metric("PQRS Detectadas", int(df_filtrado['Reclamos'].sum()), delta="Crítico" if df_filtrado['Reclamos'].sum() > 10 else "", delta_color="inverse")
m4.metric("Ciudad Líder", df_filtrado['Ciudad'].mode()[0] if not df_filtrado.empty else "N/A")

# --- GRÁFICAS ---
st.markdown("### 📈 Análisis de Tendencia y Motivos")
g1, g2 = st.columns(2)

with g1:
    st.write("**Desempeño de Satisfacción en el Tiempo**")
    st.line_chart(df_filtrado.groupby('Fecha')['Satisfaccion'].mean())

with g2:
    st.write("**Pareto de Motivos de Falla (PQRS)**")
    if not df_filtrado.empty:
        motivos_count = df_filtrado[df_filtrado['Motivo PQRS'] != "Ninguna (0 PQRS)"]['Motivo PQRS'].value_counts()
        st.bar_chart(motivos_count)
    else:
        st.info("No hay fallas registradas.")

# ==========================================
# 5. GESTIÓN DE DATOS PRO (EDICIÓN Y BORRADO)
# ==========================================
st.markdown("---")
st.subheader("🗄️ Trazabilidad de Auditoría (Gestión Master)")
st.info("💡 Consejo Pro: Para eliminar una fila específica, selecciónela y presione la tecla 'Suprimir' (Delete) de su teclado.")

edited_df = st.data_editor(
    st.session_state.db,
    num_rows="dynamic", 
    use_container_width=True,
    key="main_editor"
)

if st.button("💾 SINCRONIZAR CAMBIOS"):
    st.session_state.db = edited_df
    st.success("Base de Datos actualizada.")

st.caption("Proyecto de Innovación Digital | Auditoría de Calidad TQ 2026")
