import streamlit as st
import pandas as pd              
import os
import numpy as np
from datetime import date, timedelta

# ==========================================
# 1. SEGURIDAD Y GESTIÓN DE SESIÓN
# ==========================================
def check_password():
    def password_entered():
        # Usuarios y claves nivel profesional
        usuarios_validos = {"admin": "tq2026", "jhon.marin": "auditoria2026"}
        if st.session_state["username"] in usuarios_validos and \
           st.session_state["password"] == usuarios_validos[st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 TQ Intelligence: Acceso Restringido")
        st.text_input("Usuario Corporativo", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar al Sistema", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Usuario Corporativo", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar al Sistema", on_click=password_entered)
        st.error("❌ Credenciales inválidas. Contacte al administrador de red.")
        return False
    else:
        # BOTÓN DE CERRAR SESIÓN (NUEVO)
        if st.sidebar.button("🚪 Cerrar Sesión Segura"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
        return True

# ==========================================
# 2. PERSISTENCIA DE DATOS (CSV REFORZADO)
# ==========================================
DB_FILE = "database_tq_pro_v7.csv"

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
            return df
        except:
            return crear_df_vacio()
    return crear_df_vacio()

def crear_df_vacio():
    return pd.DataFrame(columns=['Fecha', 'Nombre Consumidor', 'Contacto', 'Ciudad Residencia', 'Region', 'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones'])

def guardar_datos(df):
    df.to_csv(DB_FILE, index=False)

st.set_page_config(page_title="Plan de Mejora Continua TQ - Pro BI", layout="wide")

# Estilos CSS Avanzados
st.markdown("""
    <style>
    .kpi-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-top: 4px solid #004aad; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .insight-text { color: #155724; font-weight: bold; }
    .critical-text { color: #721c24; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if not check_password():
    st.stop()

# Diccionario ISO 9001
DICCIONARIO_ISO = {
    "1. Calidad": {"numeral": "8.7 (Salidas No Conformes)", "plan": "Segregación y análisis de lote."},
    "2. Precios": {"numeral": "8.2.1 (Comunicación)", "plan": "Auditoría de precios en PDV."},
    "3. Logística": {"numeral": "8.4 (Suministros Externos)", "plan": "Evaluación OTIF de transportadores."},
    "4. Agotados": {"numeral": "8.1 (Control Operacional)", "plan": "Ajuste de stock de seguridad."},
    "5. Atención": {"numeral": "7.2 (Competencia)", "plan": "Capacitación en protocolos TQ."},
    "10. Otro": {"numeral": "10.2 (Acción Correctiva)", "plan": "Análisis Causa Raíz (5 Porqués)."}
}

if 'db' not in st.session_state:
    st.session_state.db = cargar_datos()

# ==========================================
# 3. SIDEBAR: CARGA Y VALIDACIÓN DE BORRADO
# ==========================================
st.sidebar.title("🏢 Tecnoquímicas S.A.")
st.sidebar.info(f"Sesión activa: {st.session_state.username}")

with st.sidebar.form("registro_pro", clear_on_submit=True):
    st.subheader("📝 Registro de Auditoría")
    nombre = st.text_input("Nombre Consumidor")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad", ["Cali", "Bogotá", "Medellín", "Barranquilla", "Bucaramanga", "Pereira", "Manizales", "Cartagena"])
    region = st.selectbox("Región", ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Santanderes", "Eje Cafetero"])
    canal = st.selectbox("Canal", ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa"])
    sat = st.slider("Satisfacción (%)", 0, 100, 85)
    reclamos = st.number_input("Cantidad PQRS", 0, 100, 0)
    motivo = st.selectbox("Falla ISO", ["Ninguna (0 PQRS)"] + list(DICCIONARIO_ISO.keys()))
    obs = st.text_area("Observaciones Técnicas")
    btn_guardar = st.form_submit_button("📥 GUARDAR EN SISTEMA")

if btn_guardar and nombre and contacto:
    nuevo = pd.DataFrame([[date.today(), nombre, contacto, ciudad, region, canal, sat, reclamos, motivo, obs]], columns=st.session_state.db.columns)
    st.session_state.db = pd.concat([st.session_state.db, nuevo], ignore_index=True)
    guardar_datos(st.session_state.db)
    st.sidebar.success(f"✅ Registro exitoso en {ciudad}")

st.sidebar.markdown("---")
st.sidebar.subheader("⚠️ Zona de Peligro")

# VALIDACIÓN DE BORRADO (NUEVO)
if st.sidebar.button("🗑️ Eliminar Último Registro"):
    st.session_state.confirm_delete = True

if st.session_state.get("confirm_delete"):
    st.sidebar.warning("¿Está seguro de eliminar el último dato?")
    col_del1, col_del2 = st.sidebar.columns(2)
    if col_del1.button("SÍ, BORRAR"):
        st.session_state.db = st.session_state.db.iloc[:-1]
        guardar_datos(st.session_state.db)
        st.session_state.confirm_delete = False
        st.rerun()
    if col_del2.button("CANCELAR"):
        st.session_state.confirm_delete = False
        st.rerun()

# ==========================================
# 4. DASHBOARD: BI DE ALTO NIVEL
# ==========================================
st.title("📊 Plan de Mejora Continua TQ: Intelligence Suite")

if st.session_state.db.empty:
    st.warning("Base de datos vacía. Ingrese registros para activar los algoritmos de BI.")
else:
    # FILTROS
    f_reg = st.multiselect("📍 Filtrar Regiones", st.session_state.db['Region'].unique(), default=st.session_state.db['Region'].unique())
    df_f = st.session_state.db[st.session_state.db['Region'].isin(f_reg)]

    # --- INSIGHTS DE ALTO NIVEL (NUEVO) ---
    st.subheader("🧠 Centro de Insights Gerenciales")
    c_ins1, c_ins2 = st.columns(2)
    
    with c_ins1:
        # Cálculo de tendencia (Últimos 7 días vs Histórico)
        hoy = date.today()
        hace_7 = hoy - timedelta(days=7)
        sat_reciente = df_f[df_f['Fecha'] >= hace_7]['Satisfaccion'].mean()
        sat_antigua = df_f[df_f['Fecha'] < hace_7]['Satisfaccion'].mean()
        
        if not np.isnan(sat_reciente) and not np.isnan(sat_antigua):
            variacion = sat_reciente - sat_antigua
            color_v = "insight-text" if variacion >= 0 else "critical-text"
            st.markdown(f"📈 **Variación semanal:** <span class='{color_v}'>{variacion:+.1f}%</span> en satisfacción.", unsafe_allow_html=True)
        else:
            st.write("📈 Tendencia semanal: *Datos insuficientes*")

    with c_ins2:
        peor_canal = df_f.groupby('Canal')['Satisfaccion'].mean().idxmin()
        val_peor = df_f.groupby('Canal')['Satisfaccion'].mean().min()
        st.markdown(f"🚩 **Alerta Operativa:** El canal <span class='critical-text'>{peor_canal}</span> presenta el menor desempeño ({val_peor:.1f}%).", unsafe_allow_html=True)

    # --- MÉTRICAS ---
    avg_sat = df_f['Satisfaccion'].mean()
    avg_nac = st.session_state.db['Satisfaccion'].mean()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Satisfacción Filtro", f"{avg_sat:.1f}%", delta=f"{avg_sat-80:.1f}% vs Meta")
    m2.metric("Promedio Nacional", f"{avg_nac:.1f}%")
    m3.metric("PQRS Totales", int(df_f['Reclamos'].sum()))
    m4.metric("Auditorías", len(df_f))

    # --- GRÁFICAS COMPARATIVAS ---
    g1, g2 = st.columns(2)
    with g1:
        st.write("**🏆 Ranking Top 5 Ciudades (Satisfacción)**")
        top_ciudades = df_f.groupby('Ciudad')['Satisfaccion'].mean().sort_values(ascending=False).head(5)
        st.bar_chart(top_ciudades)

    with g2:
        st.write("**📈 Tendencia Temporal (Ordenada)**")
        df_ev = df_f.groupby('Fecha')['Satisfaccion'].mean().sort_index()
        st.area_chart(df_ev)

# ==========================================
# 5. PLAN DE ACCIÓN E ISO
# ==========================================
st.markdown("---")
tab_traz, tab_iso = st.tabs(["🗄️ Trazabilidad Master", "📑 Plan de Acción ISO 9001"])

with tab_traz:
    st.subheader("Control de Registros y Edición")
    edited = st.data_editor(st.session_state.db, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Sincronizar Cambios Master"):
        st.session_state.db = edited
        guardar_datos(edited)
        st.success("Sincronización completa con base de datos CSV.")

with tab_iso:
    st.subheader("Dictamen Técnico para Mejora Continua")
    df_err = st.session_state.db[st.session_state.db['Motivo PQRS'] != "Ninguna (0 PQRS)"]
    
    if df_err.empty:
        st.success("✅ No hay hallazgos de no conformidad.")
    else:
        moda_serie = df_err['Motivo PQRS'].mode()
        if not moda_serie.empty:
            falla = moda_serie[0]
            plan = DICCIONARIO_ISO.get(falla)
            st.error(f"### Hallazgo Crítico: {falla}")
            st.write(f"**Referencia:** {plan['numeral']}")
            st.info(f"**Plan de Mejora:** {plan['plan']}")

st.caption(f"Tecnoquímicas S.A. | BI Pro Suite v7.0 | {date.today()}")
