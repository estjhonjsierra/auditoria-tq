import streamlit as st
import pandas as pd              
import os
import sqlite3 
import numpy as np
from datetime import date, timedelta

# ==========================================
# 1. SEGURIDAD PRO: ROLES Y SESIÓN
# ==========================================
def check_password():
    def password_entered():
        usuarios_db = {
            "admin": {"pass": "tq2026", "role": "Administrador"},
            "jhon.marin": {"pass": "auditoria2026", "role": "Auditor Senior"}
        }
        
        user = st.session_state["username_input"]
        password = st.session_state["password_input"]
        
        if user in usuarios_db and password == usuarios_db[user]["pass"]:
            st.session_state["password_correct"] = True
            st.session_state["user_role"] = usuarios_db[user]["role"]
            st.session_state["usuario_actual"] = user # Guardamos en una llave segura
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.title("🔐 TQ Enterprise: Login")
        st.text_input("Usuario Corporativo", key="username_input")
        st.text_input("Contraseña", type="password", key="password_input")
        st.button("Ingresar", on_click=password_entered)
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Credenciales incorrectas")
        return False
    return True

# ==========================================
# 2. MOTOR SQLITE (CACHÉ Y DB)
# ==========================================
DB_SQL = "tq_audit_final_v9.db"

def init_db():
    conn = sqlite3.connect(DB_SQL)
    conn.execute('''CREATE TABLE IF NOT EXISTS auditoria 
                 (Fecha TEXT, Nombre_Consumidor TEXT, Contacto TEXT, Ciudad_Residencia TEXT, 
                  Region TEXT, Canal TEXT, Satisfaccion REAL, Reclamos INTEGER, 
                  Motivo_PQRS TEXT, Observaciones TEXT)''')
    conn.commit()
    conn.close()

@st.cache_data(ttl=600)
def cargar_datos_sql():
    conn = sqlite3.connect(DB_SQL)
    df = pd.read_sql_query("SELECT * FROM auditoria", conn)
    conn.close()
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
    df.columns = ['Fecha', 'Nombre Consumidor', 'Contacto', 'Ciudad Residencia', 'Region', 'Canal', 'Satisfaccion', 'Reclamos', 'Motivo PQRS', 'Observaciones']
    return df

def guardar_dato_sql(datos):
    conn = sqlite3.connect(DB_SQL)
    conn.execute("INSERT INTO auditoria VALUES (?,?,?,?,?,?,?,?,?,?)", datos)
    conn.commit()
    conn.close()
    st.cache_data.clear()

init_db()

st.set_page_config(page_title="TQ BI v9.1", layout="wide")

# CONTROL DE ACCESO
if not check_password():
    st.stop()

# ==========================================
# 3. SIDEBAR (ORDEN CORREGIDO PARA LOGOUT)
# ==========================================
st.sidebar.title("🏢 Tecnoquímicas S.A.")

# Usamos .get() para evitar el error de la imagen si la llave no existe
usuario_display = st.session_state.get("usuario_actual", "Usuario")
rol_display = st.session_state.get("user_role", "Invitado")

st.sidebar.markdown(f"**Sesión:** {usuario_display}")
st.sidebar.markdown(f"**Rol:** {rol_display}")

if st.sidebar.button("🚪 Cerrar Sesión Segura"):
    st.session_state.clear()
    st.rerun() # Al reiniciar, volverá al login sin errores

# --- FORMULARIO ---
with st.sidebar.form("form_v9", clear_on_submit=True):
    st.subheader("📝 Registro Hallazgos")
    nombre = st.text_input("Nombre Consumidor")
    contacto = st.text_input("Contacto")
    ciudad_res = st.selectbox("Ciudad Residencia", ["Cali", "Bogotá", "Medellín", "Barranquilla", "Pereira", "Manizales"])
    region_sel = st.selectbox("Región", ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Eje Cafetero", "Santanderes"])
    canal_sel = st.selectbox("Canal", ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa"])
    sat_val = st.slider("Satisfacción (%)", 0, 100, 80)
    pqrs_val = st.number_input("Cantidad PQRS", 0, 100, 0)
    motivo_sel = st.selectbox("Falla ISO", ["Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención", "10. Otro"])
    obs_txt = st.text_area("Notas Auditor")
    
    if st.form_submit_button("💾 GUARDAR"):
        if nombre and contacto:
            fila = (str(date.today()), nombre, contacto, ciudad_res, region_sel, canal_sel, sat_val, pqrs_val, motivo_sel, obs_txt)
            guardar_dato_sql(fila)
            st.rerun()

# BORRADO SOLO PARA ADMIN
if st.session_state.get("user_role") == "Administrador":
    if st.sidebar.button("🗑️ Eliminar Último"):
        conn = sqlite3.connect(DB_SQL)
        conn.execute("DELETE FROM auditoria WHERE rowid = (SELECT MAX(rowid) FROM auditoria)")
        conn.commit()
        conn.close()
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 4. DASHBOARD (INSIGHTS Y BI)
# ==========================================
st.title("📊 TQ Intelligence: Suite de Auditoría")
db_actual = cargar_datos_sql()

if not db_actual.empty:
    f_reg = st.multiselect("📍 Filtro Regional", db_actual['Region'].unique(), default=db_actual['Region'].unique())
    df_f = db_actual[db_actual['Region'].isin(f_reg)]

    if not df_f.empty:
        st.subheader("💡 Insights Gerenciales")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            total_pqrs = db_actual['Reclamos'].sum()
            critico = df_f.groupby('Region')['Reclamos'].sum().idxmax()
            porc = (df_f.groupby('Region')['Reclamos'].sum().max() / total_pqrs * 100) if total_pqrs > 0 else 0
            st.error(f"⚠️ **Concentración:** {critico} ({porc:.1f}%)")
        
        with c2:
            riesgo = len(df_f[df_f['Satisfaccion'] < 60]) / len(df_f) * 100
            st.warning(f"📉 **Riesgo Churn:** {riesgo:.1f}% clientes críticos")
            
        with c3:
            peor_c = df_f.groupby('Canal')['Satisfaccion'].mean().idxmin()
            st.info(f"🔄 **Canal Crítico:** {peor_c}")

        # Gráficas
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Satisfacción", f"{df_f['Satisfaccion'].mean():.1f}%")
        m2.metric("Auditorías", len(df_f))
        m3.metric("PQRS", int(df_f['Reclamos'].sum()))

        g1, g2 = st.columns(2)
        with g1:
            st.write("**🏆 Top Ciudades (Satisfacción)**")
            st.bar_chart(df_f.groupby('Ciudad Residencia')['Satisfaccion'].mean().sort_values(ascending=False).head(5))
        with g2:
            st.write("**📈 Histórico Calidad**")
            st.line_chart(df_f.groupby('Fecha')['Satisfaccion'].mean().sort_index())

# ==========================================
# 5. TABLAS E ISO
# ==========================================
tab1, tab2 = st.tabs(["🗄️ Trazabilidad", "📑 Plan ISO"])
with tab1:
    st.dataframe(db_actual, use_container_width=True)
with tab2:
    st.info("Plan de mejora basado en hallazgos detectados (ISO 9001:2015)")

st.caption(f"Tecnoquímicas S.A. | v9.1 | {date.today()}")
