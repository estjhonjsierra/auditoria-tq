import streamlit as st
import pandas as pd              
import os
import sqlite3 # Base de datos real
import numpy as np
from datetime import date, timedelta

# ==========================================
# 1. SEGURIDAD Y GESTIÓN DE SESIÓN (PRO)
# ==========================================
def check_password():
    def password_entered():
        # En producción real, esto se lee de st.secrets
        usuarios_db = st.secrets.get("passwords", {"admin": "tq2026", "jhon.marin": "auditoria2026"})
        if st.session_state["username"] in usuarios_db and \
           st.session_state["password"] == usuarios_db[st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 TQ Enterprise: Login Seguro")
        st.text_input("Usuario Corporativo", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Acceder al Sistema", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Usuario Corporativo", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Acceder al Sistema", on_click=password_entered)
        st.error("❌ Credenciales inválidas.")
        return False
    return True

# ==========================================
# 2. MOTOR DE BASE DE DATOS (SQLITE - NIVEL PRO)
# ==========================================
DB_SQL = "tq_audit_pro.db"

def init_db():
    conn = sqlite3.connect(DB_SQL)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS auditoria 
                 (Fecha TEXT, Nombre_Consumidor TEXT, Contacto TEXT, Ciudad_Residencia TEXT, 
                  Region TEXT, Canal TEXT, Satisfaccion REAL, Reclamos INTEGER, 
                  Motivo_PQRS TEXT, Observaciones TEXT)''')
    conn.commit()
    conn.close()

def cargar_datos_sql():
    conn = sqlite3.connect(DB_SQL)
    df = pd.read_sql_query("SELECT * FROM auditoria", conn)
    conn.close()
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
    # Mapeo de nombres para mantener compatibilidad con el código
    df.columns = ['Fecha', 'Nombre Consumidor', 'Contacto', 'Ciudad Residencia', 'Region', 'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones']
    return df

def guardar_dato_sql(datos):
    conn = sqlite3.connect(DB_SQL)
    c = conn.cursor()
    c.execute("INSERT INTO auditoria VALUES (?,?,?,?,?,?,?,?,?,?)", datos)
    conn.commit()
    conn.close()

# Iniciar DB
init_db()

st.set_page_config(page_title="Plan de Mejora TQ v8.0", layout="wide")

if not check_password():
    st.stop()

# ==========================================
# 3. SESIÓN Y DICCIONARIO ISO
# ==========================================
if 'db' not in st.session_state:
    st.session_state.db = cargar_datos_sql()

DICCIONARIO_ISO = {
    "1. Calidad": {"numeral": "8.7 (Salidas No Conformes)", "plan": "Segregación inmediata y análisis de lote."},
    "2. Precios": {"numeral": "8.2.1 (Comunicación)", "plan": "Auditoría de precios y ajuste en CRM."},
    "3. Logística": {"numeral": "8.4 (Suministros)", "plan": "Evaluación OTIF de transportadores."},
    "4. Agotados": {"numeral": "8.1 (Operación)", "plan": "Ajuste de stock de seguridad."},
    "5. Atención": {"numeral": "7.2 (Competencia)", "plan": "Capacitación en protocolos TQ."},
    "10. Otro": {"numeral": "10.2 (Acción Correctiva)", "plan": "Análisis Causa Raíz."}
}

# ==========================================
# 4. SIDEBAR: CARGA Y CONTROL
# ==========================================
st.sidebar.title("🏢 Tecnoquímicas S.A.")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

with st.sidebar.form("form_v8", clear_on_submit=True):
    st.subheader("📝 Registro Auditoría")
    nombre = st.text_input("Nombre Consumidor")
    contacto = st.text_input("Contacto")
    ciudad_res = st.selectbox("Ciudad Residencia", ["Cali", "Bogotá", "Medellín", "Barranquilla", "Pereira"])
    region_sel = st.selectbox("Región", ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Eje Cafetero"])
    canal_sel = st.selectbox("Canal", ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa"])
    sat_val = st.slider("Satisfacción (%)", 0, 100, 85)
    pqrs_val = st.number_input("Cantidad PQRS", 0, 100, 0)
    motivo_sel = st.selectbox("Falla ISO", ["Ninguna (0 PQRS)"] + list(DICCIONARIO_ISO.keys()))
    obs_txt = st.text_area("Observaciones")
    
    if st.form_submit_button("🚀 GUARDAR EN SQL"):
        if nombre and contacto:
            fila = (str(date.today()), nombre, contacto, ciudad_res, region_sel, canal_sel, sat_val, pqrs_val, motivo_sel, obs_txt)
            guardar_dato_sql(fila)
            st.session_state.db = cargar_datos_sql()
            st.sidebar.success("✅ Guardado en Base de Datos SQL")
            st.rerun()

# VALIDACIÓN DE BORRADO
if st.sidebar.button("🗑️ Eliminar Último Registro"):
    if not st.session_state.db.empty:
        conn = sqlite3.connect(DB_SQL)
        conn.execute("DELETE FROM auditoria WHERE rowid = (SELECT MAX(rowid) FROM auditoria)")
        conn.commit()
        conn.close()
        st.session_state.db = cargar_datos_sql()
        st.rerun()

# ==========================================
# 5. DASHBOARD: BI DE ALTO NIVEL (WOW INSIGHTS)
# ==========================================
st.title("📊 TQ Intelligence Pro: Dashboard Ejecutivo")

if not st.session_state.db.empty:
    # FILTROS
    f_reg = st.multiselect("📍 Regiones", st.session_state.db['Region'].unique(), default=st.session_state.db['Region'].unique())
    df_f = st.session_state.db[st.session_state.db['Region'].isin(f_reg)]

    # --- 🧠 INSIGHTS "WOW" (NUEVO) ---
    st.subheader("💡 Business Insights Automáticos")
    c_wow1, c_wow2, c_wow3 = st.columns(3)
    
    with c_wow1:
        # INSIGHT DE CONCENTRACIÓN (WOW)
        total_pqrs_global = st.session_state.db['Reclamos'].sum()
        if total_pqrs_global > 0:
            pqrs_por_region = st.session_state.db.groupby('Region')['Reclamos'].sum()
            max_reg = pqrs_por_region.idxmax()
            porcentaje_critico = (pqrs_por_region.max() / total_pqrs_global) * 100
            st.error(f"⚠️ **Concentración PQRS:** La región **{max_reg}** concentra el **{porcentaje_critico:.1f}%** de las fallas nacionales.")
    
    with c_wow2:
        # INSIGHT DE CANAL
        peor_canal = df_f.groupby('Canal')['Satisfaccion'].mean().idxmin()
        st.warning(f"🚩 **Alerta de Canal:** El canal **{peor_canal}** requiere intervención inmediata (Baja Satisfacción).")

    with c_wow3:
        # VARIACIÓN SEMANAL
        hace_7 = date.today() - timedelta(days=7)
        reciente = df_f[df_f['Fecha'] >= hace_7]['Satisfaccion'].mean()
        if not np.isnan(reciente):
            st.info(f"📈 **Tendencia 7D:** La satisfacción semanal se sitúa en **{reciente:.1f}%**.")

    # --- MÉTRICAS Y GRÁFICAS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Satisfacción Promedio", f"{df_f['Satisfaccion'].mean():.1f}%")
    m2.metric("Total Auditorías", len(df_f))
    m3.metric("PQRS en Segmento", int(df_f['Reclamos'].sum()))

    g1, g2 = st.columns(2)
    with g1:
        st.write("**🏆 Top Ciudades de Residencia (Satisfacción)**")
        # CORRECCIÓN DE BUG: 'Ciudad Residencia'
        top_ciudades = df_f.groupby('Ciudad Residencia')['Satisfaccion'].mean().sort_values(ascending=False).head(5)
        st.bar_chart(top_ciudades)

    with g2:
        st.write("**📈 Línea de Tiempo de Calidad**")
        df_ev = df_f.groupby('Fecha')['Satisfaccion'].mean().sort_index()
        st.line_chart(df_ev)

# ==========================================
# 6. TRAZABILIDAD E ISO
# ==========================================
tab1, tab2 = st.tabs(["🗄️ Trazabilidad SQL", "📑 Plan de Mejora ISO"])

with tab1:
    st.write("Datos extraídos de motor SQLite (Seguro para Producción)")
    st.dataframe(st.session_state.db, use_container_width=True)

with tab2:
    st.subheader("Reporte de No Conformidades")
    df_iso = st.session_state.db[st.session_state.db['Motivo PQRS'] != "Ninguna (0 PQRS)"]
    if not df_iso.empty:
        falla = df_iso['Motivo PQRS'].mode()[0]
        plan = DICCIONARIO_ISO.get(falla)
        st.error(f"**Hallazgo Principal:** {falla}")
        st.info(f"**Plan ISO 9001:** {plan['plan']} (Ref: {plan['numeral']})")

st.caption(f"Tecnoquímicas S.A. | BI Pro v8.0 | Motor SQL Activo")
