import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="TQ Enterprise - Auditoría Pro", layout="wide")

# Columnas Estándar con nuevo campo 'Ciudad'
COLUMNAS = [
    'Fecha', 'Nombre', 'Contacto', 'Ciudad', 'Region', 
    'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'
]

# ==========================================
# 2. MEMORIA SEGURA
# ==========================================
if 'datos_dashboard' not in st.session_state:
    st.session_state.datos_dashboard = pd.DataFrame(columns=COLUMNAS)
if 'datos_historico' not in st.session_state:
    st.session_state.datos_historico = pd.DataFrame(columns=COLUMNAS)

# ==========================================
# 3. DICCIONARIOS TÉCNICOS (ISO 9001)
# ==========================================
SOLUCIONES_ISO = {
    "1. Calidad": "Aplicar protocolo de Cuarentena (ISO 8.7). Inspección de lote.",
    "2. Precios": "Auditoría de facturación y lista de precios (ISO 8.2).",
    "3. Logística": "Optimización de rutas de última milla (ISO 8.4).",
    "4. Agotados": "Ajuste de stock de seguridad y pronóstico de demanda.",
    "5. Atención": "Plan de capacitación en competencias blandas (ISO 7.2).",
    "6. Vencimientos": "Control estricto de rotación FEFO.",
    "7. Averías": "Rediseño de embalaje secundario (ISO 8.5.4).",
    "8. Cambios": "Simplificación de flujo de devoluciones.",
    "9. Publicidad": "Validación de cumplimiento comercial.",
    "10. Otro": "Análisis de causa raíz mediante Ishikawa."
}

# ==========================================
# 4. SIDEBAR - INGRESO DE DATOS PROFESIONAL
# ==========================================
st.sidebar.title("🏢 TECNOQUÍMICAS S.A.")
st.sidebar.markdown("**Sistema de Gestión de Calidad v2.0**")
st.sidebar.markdown("---")

with st.sidebar.form("formulario_pro", clear_on_submit=True):
    st.subheader("📝 Registro de Campo")
    nombre = st.text_input("Nombre Cliente / Punto de Venta")
    contacto = st.text_input("Celular o Email")
    ciudad = st.text_input("Ciudad / Municipio")
    
    region = st.selectbox("Región Administrativa", 
                         ["Antioquia", "Bogotá D.C.", "Valle", "Atlántico", "Santander", "Eje Cafetero", "Otro"])
    
    # MEJORA 2: Corrección de canales
    canal = st.selectbox("Canal de Venta", ["Ventas Directas", "Mercadeo", "Digital", "Distribuidor"])
    
    satisfaccion = st.slider("Nivel de Satisfacción (%)", 0, 100, 80)
    reclamos = st.number_input("Cantidad de Reclamos (PQRS)", 0, 100, 0)
    
    motivo = st.selectbox("Motivo Principal PQRS", ["Ninguna (0 PQRS)"] + list(SOLUCIONES_ISO.keys()))
    obs = st.text_area("Observaciones Técnicas")
    
    guardar = st.form_submit_button("📥 Registrar Auditoría")

if guardar:
    if not nombre or not ciudad:
        st.sidebar.error("❌ Nombre y Ciudad son obligatorios.")
    else:
        nuevo = pd.DataFrame([[
            str(date.today()), nombre, contacto, ciudad, region,
            canal, satisfaccion, reclamos, motivo, obs
        ]], columns=COLUMNAS)
        
        st.session_state.datos_dashboard = pd.concat([st.session_state.datos_dashboard, nuevo], ignore_index=True)
        st.session_state.datos_historico = pd.concat([st.session_state.datos_historico, nuevo], ignore_index=True)
        st.sidebar.success(f"✅ Registro exitoso en {ciudad}")

# ==========================================
# 5. CUERPO PRINCIPAL - DASHBOARD ANALÍTICO
# ==========================================
st.title("🛡️ Dashboard de Auditoría y Control - TQ")

tab1, tab2, tab3 = st.tabs(["📊 ANALÍTICA BI", "📁 GESTIÓN DE DATOS", "📑 INFORME GERENCIAL"])

# --- FILTROS AVANZADOS (MEJORA 6 y 7) ---
with st.expander("🔍 Filtros Avanzados de Análisis"):
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        reg_filtro = st.multiselect("Filtrar por Región", st.session_state.datos_dashboard['Region'].unique())
    with f_col2:
        canal_filtro = st.multiselect("Filtrar por Canal", st.session_state.datos_dashboard['Canal'].unique())
    with f_col3:
        tiempo = st.selectbox("Periodo", ["Todo el histórico", "Hoy", "Últimos 7 días"])

# Aplicar lógica de filtros
df_f = st.session_state.datos_dashboard.copy()
if reg_filtro:
    df_f = df_f[df_f['Region'].isin(reg_filtro)]
if canal_filtro:
    df_f = df_f[df_f['Canal'].isin(canal_filtro)]
if tiempo == "Hoy":
    df_f = df_f[df_f['Fecha'] == str(date.today())]
elif tiempo == "Últimos 7 días":
    hace_7 = str(date.today() - timedelta(days=7))
    df_f = df_f[df_f['Fecha'] >= hace_7]

# ==========================================
# PESTAÑA 1: ANALÍTICA (MEJORA 4 y 5)
# ==========================================
with tab1:
    if df_f.empty:
        st.warning("No hay datos que coincidan con los filtros seleccionados.")
    else:
        # KPI SEMÁFORO (MEJORA 5)
        avg_sat = df_f['Satisfaccion'].mean()
        color = "green" if avg_sat >= 80 else ("orange" if avg_sat >= 60 else "red")
        
        st.markdown(f"""
            <div style="background-color: {color}; padding: 20px; border-radius: 10px; text-align: center;">
                <h1 style="color: white; margin:0;">{avg_sat:.1f}%</h1>
                <p style="color: white; margin:0;">Satisfacción General del Segmento Seleccionado</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # MÉTRICAS
        m1, m2, m3 = st.columns(3)
        m1.metric("Registros", len(df_f))
        m2.metric("Total PQRS", int(df_f['Reclamos'].sum()))
        m3.metric("Ciudades Impactadas", df_f['Ciudad'].nunique())

        # DOBLE GRÁFICA COMPARATIVA (MEJORA 4)
        st.markdown("---")
        st.subheader("🌍 Análisis Comparativo: Segmento vs. Nacional")
        g1, g2 = st.columns(2)
        
        with g1:
            st.write("**Satisfacción Segmento Filtrado**")
            st.line_chart(df_f.groupby('Region')['Satisfaccion'].mean())
        
        with g2:
            st.write("**Satisfacción Total Nacional (Histórico)**")
            st.line_chart(st.session_state.datos_dashboard.groupby('Region')['Satisfaccion'].mean())

# ==========================================
# PESTAÑA 2: GESTIÓN (MEJORA 1 y 9)
# ==========================================
with tab2:
    st.subheader("🗄️ Administración de Registros")
    
    # Mostrar tabla con opción de edición (MEJORA 9)
    edited_df = st.data_editor(st.session_state.datos_historico, use_container_width=True, num_rows="dynamic")
    st.session_state.datos_historico = edited_df

    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        # MEJORA 1: Borrar inteligente
        if st.button("🔙 Eliminar Último Registro (Dashboard)"):
            if not st.session_state.datos_dashboard.empty:
                st.session_state.datos_dashboard = st.session_state.datos_dashboard.iloc[:-1]
                st.rerun()
                
    with col_btn2:
        csv = st.session_state.datos_historico.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exportar Base de Datos (CSV)", csv, "tq_historico.csv")

    with col_btn3:
        if st.button("🚨 FORMATEAR SISTEMA", help="Borra histórico y dashboard"):
            st.session_state.datos_dashboard = pd.DataFrame(columns=COLUMNAS)
            st.session_state.datos_historico = pd.DataFrame(columns=COLUMNAS)
            st.rerun()

# ==========================================
# PESTAÑA 3: INFORME (MEJORA 8)
# ==========================================
with tab3:
    st.subheader("📑 Dictamen Técnico de Mejora Continua")
    df_h = st.session_state.datos_historico
    
    if df_h.empty:
        st.info("Esperando datos para análisis ISO 9001...")
    else:
        df_p = df_h[df_h['Motivo PQRS'] != "Ninguna (0 PQRS)"]
        
        col_inf1, col_inf2 = st.columns(2)
        
        with col_inf1:
            st.success("✅ Trazabilidad Digital Conforme")
            if not df_p.empty:
                top = df_p['Motivo PQRS'].mode()[0]
                st.error(f"**Hallazgo Principal:** {top}")
                st.info(f"**Solución Recomendada:** {SOLUCIONES_ISO.get(top)}")
            else:
                st.success("No se reportan No Conformidades.")
        
        with col_inf2:
            # Resumen para el informe descargable
            resumen_informe = f"""
            INFORME DE AUDITORÍA TQ
            Fecha: {date.today()}
            Total Registros: {len(df_h)}
            Satisfacción Promedio: {df_h['Satisfaccion'].mean():.1f}%
            """
            st.download_button("📄 Generar Informe PDF/Texto", resumen_informe, "Informe_Auditoria.txt")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Tecnoquímicas S.A. | Auditoría de Calidad 2026</p>", unsafe_allow_html=True)
