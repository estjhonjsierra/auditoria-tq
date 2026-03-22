import streamlit as st
import pandas as pd
from datetime import date

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="App Auditoría TQ - Canal Ventas", layout="wide")

# Columnas estándar (EVITA ERRORES)
COLUMNAS = [
    'Fecha', 'Nombre', 'Contacto', 'Region', 'Canal',
    'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'
]

# ==========================================
# MEMORIA SEGURA
# ==========================================
if 'datos_dashboard' not in st.session_state:
    st.session_state.datos_dashboard = pd.DataFrame(columns=COLUMNAS)

if 'datos_historico' not in st.session_state:
    st.session_state.datos_historico = pd.DataFrame(columns=COLUMNAS)

# Asegurar columnas siempre
st.session_state.datos_dashboard = st.session_state.datos_dashboard.reindex(columns=COLUMNAS)
st.session_state.datos_historico = st.session_state.datos_historico.reindex(columns=COLUMNAS)

# ==========================================
# SOLUCIONES ISO
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
# SIDEBAR
# ==========================================
st.sidebar.title("🏢 TECNOQUÍMICAS")
st.sidebar.markdown("Sistema de Gestión de Calidad")

with st.sidebar.form("formulario", clear_on_submit=True):
    nombre = st.text_input("Nombre Cliente")
    contacto = st.text_input("Contacto")
    region = st.selectbox("Región", ["Antioquia", "Bogotá", "Valle", "Otro"])
    canal = st.selectbox("Canal", ["Ventas", "Mercadeo", "PQRS"])
    satisfaccion = st.slider("Satisfacción", 0, 100, 80)
    reclamos = st.number_input("Cantidad PQRS", 0, 50, 0)
    motivo = st.selectbox("Motivo", [
        "Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística",
        "4. Agotados", "5. Atención", "6. Vencimientos",
        "7. Averías", "8. Cambios", "9. Publicidad", "10. Otro"
    ])
    obs = st.text_area("Observaciones")
    guardar = st.form_submit_button("Guardar")

if guardar:
    nuevo = pd.DataFrame([[
        str(date.today()), nombre, contacto, region,
        canal, satisfaccion, reclamos, motivo, obs
    ]], columns=COLUMNAS)

    st.session_state.datos_dashboard = pd.concat([st.session_state.datos_dashboard, nuevo], ignore_index=True)
    st.session_state.datos_historico = pd.concat([st.session_state.datos_historico, nuevo], ignore_index=True)
    st.sidebar.success("✅ Registro guardado")

# ==========================================
# MAIN
# ==========================================
st.title("🛡️ Sistema Auditoría TQ")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📁 Histórico", "📑 Informe"])

df = st.session_state.datos_dashboard

# ==========================================
# PESTAÑA 1: DASHBOARD
# ==========================================
with tab1:
    if df.empty:
        st.warning("Sin datos registrados aún.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Registros", len(df))
        c2.metric("Satisfacción Promedio", f"{df['Satisfaccion'].mean():.1f}%")
        c3.metric("Total PQRS", int(df['Reclamos'].sum()))

        st.line_chart(df.groupby('Fecha')['Satisfaccion'].mean())

        df_m = df[df['Motivo PQRS'] != "Ninguna (0 PQRS)"]
        if not df_m.empty:
            st.bar_chart(df_m['Motivo PQRS'].value_counts())
        else:
            st.success("No hay motivos de reclamo registrados.")

# ==========================================
# PESTAÑA 2: HISTÓRICO
# ==========================================
with tab2:
    st.subheader("Base de Datos de Auditoría")
    st.dataframe(st.session_state.datos_historico, use_container_width=True)

    if not st.session_state.datos_historico.empty:
        csv = st.session_state.datos_historico.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar CSV", csv, "reporte_tq.csv", "text/csv")

    if st.button("🗑️ Borrar todo el historial"):
        st.session_state.datos_dashboard = pd.DataFrame(columns=COLUMNAS)
        st.session_state.datos_historico = pd.DataFrame(columns=COLUMNAS)
        st.rerun()

# ==========================================
# PESTAÑA 3: INFORME
# ==========================================
with tab3:
    st.subheader("Dictamen de Calidad ISO 9001")
    df_h = st.session_state.datos_historico

    if df_h.empty:
        st.info("Ingrese datos para generar el dictamen automático.")
    else:
        st.success("Trazabilidad conforme a la norma.")
        
        # Filtramos los que tienen reclamos reales
        df_p = df_h[df_h['Motivo PQRS'] != "Ninguna (0 PQRS)"]

        if not df_p.empty:
            # Calculamos el motivo más frecuente
            top_motivo = df_p['Motivo PQRS'].mode()[0]
            st.error(f"**Hallazgo Crítico:** {top_motivo}")
            
            # Buscamos la solución en el diccionario
            propuesta = SOLUCIONES_ISO.get(top_motivo, "Revisión técnica de procesos.")
            st.info(f"**Plan de Acción:** {propuesta}")
        else:
            st.success("No se detectan causas raíz de fallas. Proceso bajo control.")

# ==========================================
st.markdown("---")
st.markdown("<p style='text-align: center;'>© 2026 Auditoría TQ - Mejora Continua</p>", unsafe_allow_html=True)
