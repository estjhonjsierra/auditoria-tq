import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta

# ==========================================
# 1. CONFIGURACIÓN DE ALTO NIVEL
# ==========================================
st.set_page_config(page_title="TQ Intelligence - Auditoría PRO", layout="wide")

# Estilo para tarjetas y métricas (Jerarquía Visual)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; }
    .stApp { background-color: #f8f9fa; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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
    # Datos semilla para que el dashboard no nazca vacío y se vea el nivel PRO
    seeds = [
        [str(date.today()), "Farmacia Central", "Cali", "Valle", "Ventas", 85, 0, "Ninguna (0 PQRS)", "Todo OK"],
        [str(date.today() - timedelta(days=1)), "Droguería XYZ", "Medellín", "Antioquia", "Digital", 40, 3, "3. Logística", "Retraso entrega"]
    ]
    st.session_state.db = pd.DataFrame(seeds, columns=COLUMNAS)

# ==========================================
# 3. SIDEBAR: CONTROL DE ENTRADA
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Tecnoqu%C3%ADmicas_logo.svg/1200px-Tecnoqu%C3%ADmicas_logo.svg.png", width=200)
st.sidebar.title("🛠️ Centro de Carga")

with st.sidebar.form("input_form", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    nombre = col_a.text_input("Cliente")
    ciudad = col_b.text_input("Ciudad")
    
    region = st.selectbox("Región Estratégica", ["Antioquia", "Bogotá", "Valle", "Costa", "Santanderes"])
    canal = st.select_slider("Canal de Atención", options=["Ventas", "Mercadeo", "Digital"])
    
    st.markdown("---")
    sat = st.slider("Nivel de Satisfacción (%)", 0, 100, 80)
    reclamos = st.number_input("Cantidad PQRS", 0, 100, 0)
    motivo = st.selectbox("Categoría de Falla", ["Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención"])
    obs = st.text_area("Notas de Auditoría")
    
    btn_guardar = st.form_submit_button("🚀 REGISTRAR EN SISTEMA")

if btn_guardar:
    nuevo_reg = pd.DataFrame([[str(date.today()), nombre, ciudad, region, canal, sat, reclamos, motivo, obs]], columns=COLUMNAS)
    st.session_state.db = pd.concat([st.session_state.db, nuevo_reg], ignore_index=True)
    st.toast("Registro guardado con éxito", icon="✅")

# ==========================================
# 4. DASHBOARD ANALÍTICO (NIVEL BI)
# ==========================================
st.title("📊 Dashboard de Control Maestro")
st.markdown("---")

# --- FILTROS DE SEGMENTACIÓN ---
f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
with f_col1:
    f_region = st.multiselect("📍 Filtrar Región", options=st.session_state.db['Region'].unique(), default=st.session_state.db['Region'].unique())
with f_col2:
    f_canal = st.multiselect("🔄 Filtrar Canal", options=st.session_state.db['Canal'].unique(), default=st.session_state.db['Canal'].unique())

df_filtrado = st.session_state.db[(st.session_state.db['Region'].isin(f_region)) & (st.session_state.db['Canal'].isin(f_canal))]

# --- 2. INTELIGENCIA VISUAL (KPI CARDS CON ALERTAS) ---
m1, m2, m3, m4 = st.columns(4)

avg_sat = df_filtrado['Satisfaccion'].mean() if not df_filtrado.empty else 0
# Lógica de colores dinámica
status_color = "normal" if avg_sat > 80 else "inverse" if avg_sat < 60 else "off"

m1.metric("Satisfacción Global", f"{avg_sat:.1f}%", delta=f"{avg_sat-80:.1f}% vs Meta", delta_color=status_color)
m2.metric("Total Auditorías", len(df_filtrado))
m3.metric("PQRS Detectadas", int(df_filtrado['Reclamos'].sum()), delta="Crítico" if df_filtrado['Reclamos'].sum() > 10 else "", delta_color="inverse")
m4.metric("Ciudad Top", df_filtrado['Ciudad'].mode()[0] if not df_filtrado.empty else "N/A")

# --- 1 y 4. COMPARATIVA Y SEGMENTACIÓN (GRÁFICAS) ---
st.markdown("### 📈 Análisis Comparativo y Ranking")
g1, g2 = st.columns(2)

with g1:
    st.write("**Desempeño Local (Selección) vs. Tendencia Nacional**")
    # Gráfica de comparación espejo
    chart_data = st.session_state.db.groupby('Fecha')['Satisfaccion'].mean().reset_index()
    chart_data['Filtro'] = df_filtrado.groupby('Fecha')['Satisfaccion'].mean().values if not df_filtrado.empty else 0
    st.line_chart(chart_data.set_index('Fecha'))

with g2:
    st.write("**Ranking de Problemas (Pareto de Motivos)**")
    if not df_filtrado.empty:
        motivos_count = df_filtrado[df_filtrado['Motivo PQRS'] != "Ninguna (0 PQRS)"]['Motivo PQRS'].value_counts()
        st.bar_chart(motivos_count)
    else:
        st.info("No hay fallas registradas en este segmento.")

# ==========================================
# 5. CONTROL DE REGISTROS (EDICIÓN Y ELIMINACIÓN)
# ==========================================
st.markdown("---")
st.subheader("⚙️ Gestión de Registros y Control de Calidad")

# 3. ELIMINAR Y EDITAR POR FILA
# Usamos data_editor que es nivel profesional para edición directa
edited_df = st.data_editor(
    st.session_state.db,
    num_rows="dynamic", # Esto permite al usuario eliminar filas seleccionándolas y dando a 'Delete'
    use_container_width=True,
    key="main_editor"
)

if st.button("💾 Sincronizar Cambios en Base de Datos"):
    st.session_state.db = edited_df
    st.success("Base de Datos actualizada y sincronizada.")

# ==========================================
# 6. EXPORTACIÓN PROFESIONAL
# ==========================================
st.sidebar.markdown("---")
csv = st.session_state.db.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="📥 DESCARGAR DATA MASTER (CSV)",
    data=csv,
    file_name=f"Reporte_Auditoria_TQ_{date.today()}.csv",
    mime="text/csv",
)

st.caption("Sistema de Auditoría de Alta Gerencia | Tecnoquímicas 2026")
