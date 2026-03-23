import streamlit as st
import pandas as pd
from datetime import date, timedelta

# ==========================================
# CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="App Auditoría TQ - PRO", layout="wide")

# Columnas definitivas
COLUMNAS = [
    'Fecha', 'Nombre', 'Contacto', 'Ciudad', 'Region', 'Canal',
    'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'
]

# ==========================================
# MEMORIA SEGURA (ESTADO)
# ==========================================
if 'datos_historico' not in st.session_state:
    st.session_state.datos_historico = pd.DataFrame(columns=COLUMNAS)

if 'datos_dashboard' not in st.session_state:
    st.session_state.datos_dashboard = pd.DataFrame(columns=COLUMNAS)

# ==========================================
# DICCIONARIO ISO 
# ==========================================
SOLUCIONES_ISO = {
    "1. Calidad": "Aplicar protocolo de Cuarentena (ISO 8.7).",
    "2. Precios": "Auditoría de facturación (ISO 8.2).",
    "3. Logística": "Optimizar rutas y tiempos (ISO 8.4).",
    "4. Agotados": "Ajustar pronóstico de demanda.",
    "5. Atención": "Capacitación en servicio al cliente.",
    "6. Vencimientos": "Implementar FEFO.",
    "7. Averías": "Mejorar embalaje.",
    "8. Cambios": "Optimizar devoluciones.",
    "9. Publicidad": "Validar comunicación comercial.",
    "10. Otro": "Análisis de causa raíz."
}

# ==========================================
# ENCABEZADO Y ROLES
# ==========================================
col_login1, col_login2 = st.columns([8, 2])
with col_login2:
    rol_usuario = st.selectbox("🔐 Perfil Activo:", ["Supervisor", "Auditor", "Gerencia"])

# ==========================================
# SIDEBAR: INGRESO Y ELIMINACIÓN (ZONA DE ACCIÓN)
# ==========================================
st.sidebar.title("🏢 TECNOQUÍMICAS")
st.sidebar.markdown("Sistema de Gestión - Ingreso")

with st.sidebar.form("formulario", clear_on_submit=True):
    nombre = st.text_input("Nombre Cliente")
    contacto = st.text_input("Contacto")
    ciudad = st.text_input("Ciudad / Municipio") 
    region = st.selectbox("Región", ["Antioquia", "Bogotá", "Valle", "Costa", "Otro"])
    canal = st.selectbox("Canal", ["Ventas", "Mercadeo", "Digital"]) 
    satisfaccion = st.slider("Satisfacción (%)", 0, 100, 80)
    reclamos = st.number_input("Cantidad PQRS", 0, 50, 0)
    motivo = st.selectbox("Motivo PQRS", [
        "Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística",
        "4. Agotados", "5. Atención", "6. Vencimientos",
        "7. Averías", "8. Cambios", "9. Publicidad", "10. Otro"
    ])
    obs = st.text_area("Observaciones")
    
    # BOTÓN GUARDAR
    guardar = st.form_submit_button("Guardar Registro")

if guardar:
    nuevo = pd.DataFrame([[
        str(date.today()), nombre, contacto, ciudad, region,
        canal, satisfaccion, reclamos, motivo, obs
    ]], columns=COLUMNAS)

    st.session_state.datos_historico = pd.concat([st.session_state.datos_historico, nuevo], ignore_index=True)
    st.session_state.datos_dashboard = pd.concat([st.session_state.datos_dashboard, nuevo], ignore_index=True)
    st.sidebar.success("✅ Registro guardado")

# ESPACIO Y BOTÓN ELIMINAR (Tal cual lo pediste)
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Eliminar último registro", use_container_width=True):
    if not st.session_state.datos_dashboard.empty:
        # Solo afecta al dashboard, no al histórico (Nivel PRO)
        st.session_state.datos_dashboard = st.session_state.datos_dashboard.iloc[:-1]
        st.sidebar.warning("⚠️ Registro eliminado del Dashboard")
        st.rerun()
    else:
        st.sidebar.error("No hay registros para eliminar")

# ==========================================
# CUERPO PRINCIPAL
# ==========================================
st.title("🛡️ Sistema de Auditoría BI - TQ")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Analítico", "📁 Base de Datos", "📑 Informe Ejecutivo"])

# PESTAÑA 1: DASHBOARD
with tab1:
    st.subheader("Filtros de Análisis")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    filtro_fecha = f_col1.selectbox("📅 Periodo", ["Historico Total", "Hoy", "Últimos 7 días", "Este Mes"])
    filtro_region = f_col2.selectbox("📍 Región", ["Todas"] + list(st.session_state.datos_dashboard['Region'].unique()))
    filtro_canal = f_col3.selectbox("🔄 Canal", ["Todos"] + list(st.session_state.datos_dashboard['Canal'].unique()))

    # Lógica de Filtrado
    df_dash = st.session_state.datos_dashboard.copy()
    if not df_dash.empty:
        df_dash['Fecha'] = pd.to_datetime(df_dash['Fecha']).dt.date
        if filtro_fecha == "Hoy":
            df_dash = df_dash[df_dash['Fecha'] == date.today()]
        elif filtro_fecha == "Últimos 7 días":
            df_dash = df_dash[df_dash['Fecha'] >= (date.today() - timedelta(days=7))]
            
        if filtro_region != "Todas":
            df_dash = df_dash[df_dash['Region'] == filtro_region]
        if filtro_canal != "Todos":
            df_dash = df_dash[df_dash['Canal'] == filtro_canal]

    if df_dash.empty:
        st.warning("Sin datos para mostrar con los filtros actuales.")
    else:
        # Indicadores Visuales (Semáforo)
        promedio = df_dash['Satisfaccion'].mean()
        status = "🟢" if promedio > 80 else "🟡" if promedio >= 60 else "🔴"
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Registros", len(df_dash))
        c2.metric("Satisfacción Promedio", f"{promedio:.1f}%", f"{status} Desempeño")
        c3.metric("PQRS Totales", int(df_dash['Reclamos'].sum()))

        st.markdown("---")
        # Doble Gráfica (Comparativa)
        g1, g2 = st.columns(2)
        with g1:
            st.write("**Desempeño Local (Filtro)**")
            st.line_chart(df_dash.groupby('Fecha')['Satisfaccion'].mean())
        with g2:
            st.write("**Desempeño Nacional (Histórico)**")
            st.line_chart(st.session_state.datos_historico.groupby('Fecha')['Satisfaccion'].mean())

# PESTAÑA 2: BASE DE DATOS (EDICIÓN)
with tab2:
    st.subheader("Histórico de Auditorías")
    if rol_usuario in ["Auditor", "Gerencia"]:
        st.session_state.datos_historico = st.data_editor(
            st.session_state.datos_historico, 
            num_rows="dynamic",
            use_container_width=True,
            key="db_editor"
        )
    else:
        st.dataframe(st.session_state.datos_historico, use_container_width=True)

# PESTAÑA 3: INFORME
with tab3:
    st.subheader("Análisis de Causa Raíz e ISO")
    if not st.session_state.datos_historico.empty:
        df_pqrs = st.session_state.datos_historico[st.session_state.datos_historico['Motivo PQRS'] != "Ninguna (0 PQRS)"]
        if not df_pqrs.empty:
            peor_motivo = df_pqrs['Motivo PQRS'].mode()[0]
            plan = SOLUCIONES_ISO.get(peor_motivo, "Revisión general.")
            
            informe = f"""
            INFORME EJECUTIVO TQ - {date.today()}
            -----------------------------------
            HALLAZGO: {peor_motivo}
            ANÁLISIS: Se detecta recurrencia en el canal {df_pqrs['Canal'].mode()[0]}.
            ACCIÓN ISO: {plan}
            """
            st.code(informe)
            st.download_button("📥 Descargar Informe", informe, file_name="Reporte_TQ.txt")
        else:
            st.success("Operación Limpia: 0 PQRS detectadas.")

st.markdown("---")
st.markdown("<p style='text-align: center;'>© 2026 Auditoría TQ - Software Nivel Profesional</p>", unsafe_allow_html=True)
