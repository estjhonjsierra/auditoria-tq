import streamlit as st
import pandas as pd
from datetime import date

# 1. Configuración de la página
st.set_page_config(page_title="App Auditoría TQ - Canal Ventas", layout="wide", initial_sidebar_state="expanded")

# 2. SISTEMA DE MEMORIA (Inicialización)
if 'datos_dashboard' not in st.session_state:
    st.session_state.datos_dashboard = pd.DataFrame(columns=[
        'Fecha', 'Nombre', 'Contacto', 'Region', 'Canal', 'Satisfaccion', 'Quejas', 'Motivo Queja', 'Observaciones'
    ])

if 'datos_historico' not in st.session_state:
    st.session_state.datos_historico = pd.DataFrame(columns=[
        'Fecha', 'Nombre', 'Contacto', 'Region', 'Canal', 'Satisfaccion', 'Quejas', 'Motivo Queja', 'Observaciones'
    ])

# ==========================================
# BARRA LATERAL (INGRESO DE DATOS)
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #004aad;'>🏢 TECNOQUÍMICAS</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-size: 14px; color: gray;'>Sistema de Gestión de Calidad</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.subheader("📝 Ingresar Nueva Encuesta")

with st.sidebar.form("formulario_encuesta_iso", clear_on_submit=True):
    nombre_cliente = st.text_input("Nombre del Cliente:")
    contacto_cliente = st.text_input("Celular/Correo:")
    
    region_colombia = st.selectbox("Región/Departamento:", [
        "Antioquia", "Atlantico", "Bogota D.C.", "Bolivar", "Boyaca", "Caldas",
        "Cauca", "Cesar", "Cundinamarca", "Huila", "La Guajira", "Magdalena",
        "Valle del Cauca", "Santander", "Norte de Santander", "Ninguno (No aplica)"
    ])
    
    canal_venta = st.selectbox("Canal de Contacto:", ["Fuerza de Ventas", "Mercadeo", "Digital/PQRS"])
    nivel_satisfaccion = st.slider("Satisfacción (0-100%):", 0, 100, 80)
    cantidad_quejas = st.number_input("Cantidad de Quejas:", min_value=0, max_value=50, value=0)
    
    motivo_queja = st.selectbox("Motivo Principal:", [
        "Ninguna (0 Quejas)", "1. Calidad", "2. Precios", "3. Logística", 
        "4. Agotados", "5. Atención", "6. Vencimientos", "7. Averías", 
        "8. Cambios", "9. Publicidad", "10. Otro"
    ])
    
    feedback = st.text_area("Observaciones detalladas:")
    submit_button = st.form_submit_button(label="💾 Guardar Trazabilidad")

if submit_button:
    if motivo_queja == "10. Otro" and not feedback.strip():
        st.sidebar.error("❌ ERROR: Escriba el detalle en Observaciones.")
    else:
        nuevo = pd.DataFrame({
            'Fecha': [str(date.today())], 'Nombre': [nombre_cliente], 'Contacto': [contacto_cliente],
            'Region': [region_colombia], 'Canal': [canal_venta], 'Satisfaccion': [nivel_satisfaccion],
            'Quejas': [cantidad_quejas], 'Motivo Queja': [motivo_queja], 'Observaciones': [feedback]
        })
        st.session_state.datos_dashboard = pd.concat([st.session_state.datos_dashboard, nuevo], ignore_index=True)
        st.session_state.datos_historico = pd.concat([st.session_state.datos_historico, nuevo], ignore_index=True)
        st.sidebar.success(f"✅ Guardado: {region_colombia}")

if st.sidebar.button("🧹 Limpiar Gráficas"):
    st.session_state.datos_dashboard = pd.DataFrame(columns=st.session_state.datos_dashboard.columns)
    st.rerun()

# ==========================================
# CUERPO PRINCIPAL
# ==========================================
st.title("🛡️ Sistema Integral de Auditoría: TQ")
tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "🗄️ HISTÓRICO", "📑 INFORME ISO"])

df_actual = st.session_state.datos_dashboard

with tab1:
    if df_actual.empty:
        st.warning("⚠️ Sin datos. Registre una encuesta en el panel izquierdo.")
    else:
        # FILTRO DE REGIÓN
        opciones_reg = ["Todas (Nacional)"] + list(df_actual['Region'].unique())
        filtro_region = st.selectbox("🔍 Selector Regional:", opciones_reg)
        
        # APLICAR FILTRO ESTRICTO
        df_f = df_actual if filtro_region == "Todas (Nacional)" else df_actual[df_actual['Region'] == filtro_region]
        
        # MÉTRICAS
        m1, m2, m3 = st.columns(3)
        m1.metric("Encuestas", len(df_f))
        m2.metric("Satisfacción", f"{df_f['Satisfaccion'].mean():.1f}%")
        m3.metric("Total Quejas", int(df_f['Quejas'].sum()))

        # GRÁFICAS
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**📈 Tendencia ({filtro_region})**")
            st.line_chart(df_f.groupby('Fecha')['Satisfaccion'].mean())
        with c2:
            st.write("**⚠️ Causas Raíz**")
            df_m = df_f[df_f['Motivo Queja'] != "Ninguna (0 Quejas)"]
            if not df_m.empty:
                st.bar_chart(df_m['Motivo Queja'].value_counts())
            else:
                st.success("Sin quejas")

with tab2:
    st.subheader("🗄️ Trazabilidad Total")
    st.dataframe(st.session_state.datos_historico, use_container_width=True)
    if not st.session_state.datos_historico.empty:
        csv = st.session_state.datos_historico.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte", data=csv, file_name='Auditoria_TQ.csv')

with tab3:
    st.subheader("📑 Dictamen ISO 9001")
    if not st.session_state.datos_historico.empty:
        df_p = st.session_state.datos_historico[st.session_state.datos_historico['Motivo Queja'] != "Ninguna (0 Quejas)"]
        if not df_p.empty:
            top = df_p['Motivo Queja'].mode()[0]
            st.error(f"**ALERTA:** Problema detectado: **{top}**. Se requiere Plan de Acción.")
        else:
            st.success("✅ Sistema en estado Óptimo.")
    else:
        st.info("No hay datos para dictaminar.")
