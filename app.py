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

        # Diccionario de usuarios con ROLES (Admin vs Auditor)

        usuarios_db = {

            "admin": {"pass": "tq2026", "role": "Administrador"},

            "jhon.marin": {"pass": "auditoria2026", "role": "Auditor Senior"}

        }

        

        user = st.session_state["username"]

        password = st.session_state["password"]

        

        if user in usuarios_db and password == usuarios_db[user]["pass"]:

            st.session_state["password_correct"] = True

            st.session_state["user_role"] = usuarios_db[user]["role"]

            del st.session_state["password"] 

        else:

            st.session_state["password_correct"] = False



    if "password_correct" not in st.session_state:

        st.title("🔐 TQ Enterprise: Business Intelligence")

        st.text_input("Usuario Corporativo", key="username")

        st.text_input("Contraseña", type="password", key="password")

        st.button("Acceder al Ecosistema", on_click=password_entered)

        return False

    elif not st.session_state["password_correct"]:

        st.error("❌ Credenciales inválidas. Acceso denegado.")

        return False

    return True



# ==========================================

# 2. MOTOR SQLITE CON CACHÉ (RENDIMIENTO ⚡)

# ==========================================

DB_SQL = "tq_audit_final_v9.db"



def init_db():

    conn = sqlite3.connect(DB_SQL)

    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS auditoria 

                 (Fecha TEXT, Nombre_Consumidor TEXT, Contacto TEXT, Ciudad_Residencia TEXT, 

                  Region TEXT, Canal TEXT, Satisfaccion REAL, Reclamos INTEGER, 

                  Motivo_PQRS TEXT, Observaciones TEXT)''')

    conn.commit()

    conn.close()



@st.cache_data(ttl=600) # CACHÉ DE 10 MINUTOS (OPTIMIZACIÓN REAL)

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

    c = conn.cursor()

    c.execute("INSERT INTO auditoria VALUES (?,?,?,?,?,?,?,?,?,?)", datos)

    conn.commit()

    conn.close()

    st.cache_data.clear() # Limpiar caché para ver el dato nuevo



init_db()



st.set_page_config(page_title="TQ BI v9.0 - Plan de Mejora", layout="wide")



if not check_password():

    st.stop()



# ==========================================

# 3. SIDEBAR: REGISTRO Y CERRAR SESIÓN

# ==========================================

st.sidebar.title("🏢 Tecnoquímicas S.A.")

st.sidebar.markdown(f"**Usuario:** {st.session_state.username}")

st.sidebar.markdown(f"**Rol:** {st.session_state.user_role}")



if st.sidebar.button("🚪 Cerrar Sesión Segura"):

    st.session_state.clear()

    st.rerun()



with st.sidebar.form("form_v9", clear_on_submit=True):

    st.subheader("📝 Registro de Hallazgos")

    nombre = st.text_input("Nombre Consumidor")

    contacto = st.text_input("Contacto")

    ciudad_res = st.selectbox("Ciudad Residencia", ["Cali", "Bogotá", "Medellín", "Barranquilla", "Pereira", "Manizales"])

    region_sel = st.selectbox("Región", ["Antioquia", "Bogotá D.C.", "Valle del Cauca", "Costa Caribe", "Eje Cafetero", "Santanderes"])

    canal_sel = st.selectbox("Canal", ["Ventas Directas", "Mercadeo", "Digital", "Comunicación Directa"])

    sat_val = st.slider("Nivel Satisfacción (%)", 0, 100, 80)

    pqrs_val = st.number_input("Cantidad PQRS", 0, 100, 0)

    motivo_sel = st.selectbox("Clasificación ISO", ["Ninguna (0 PQRS)", "1. Calidad", "2. Precios", "3. Logística", "4. Agotados", "5. Atención", "10. Otro"])

    obs_txt = st.text_area("Observaciones del Auditor")

    

    if st.form_submit_button("💾 GUARDAR AUDITORÍA"):

        if nombre and contacto:

            fila = (str(date.today()), nombre, contacto, ciudad_res, region_sel, canal_sel, sat_val, pqrs_val, motivo_sel, obs_txt)

            guardar_dato_sql(fila)

            st.sidebar.success("✅ Almacenado en SQL")

            st.rerun()



# VALIDACIÓN DE BORRADO (SOLO PARA ADMIN)

if st.session_state.user_role == "Administrador":

    if st.sidebar.button("🗑️ Eliminar Último Registro"):

        conn = sqlite3.connect(DB_SQL)

        conn.execute("DELETE FROM auditoria WHERE rowid = (SELECT MAX(rowid) FROM auditoria)")

        conn.commit()

        conn.close()

        st.cache_data.clear()

        st.rerun()



# ==========================================

# 4. DASHBOARD: ANALÍTICA WOW & IMPACTO

# ==========================================

st.title("📊 TQ Intelligence: Plan de Mejora Continua")

db_actual = cargar_datos_sql()



if not db_actual.empty:

    f_reg = st.multiselect("📍 Segmentación Regional", db_actual['Region'].unique(), default=db_actual['Region'].unique())

    df_f = db_actual[db_actual['Region'].isin(f_reg)]



    # --- 🧠 INSIGHTS WOW (PROTEGIDOS CONTRA VACÍOS) ---

    st.subheader("💡 Insights de Impacto Estratégico")

    

    if not df_f.empty: # VALIDACIÓN DE VACÍOS (ANTI-CRASH)

        c_i1, c_i2, c_i3 = st.columns(3)

        

        with c_i1:

            # INSIGHT 1: CONCENTRACIÓN

            total_pqrs = db_actual['Reclamos'].sum()

            if total_pqrs > 0:

                critico = df_f.groupby('Region')['Reclamos'].sum().idxmax()

                porc = (df_f.groupby('Region')['Reclamos'].sum().max() / total_pqrs) * 100

                st.error(f"⚠️ **Fuga de Calidad:** {critico} concentra el **{porc:.1f}%** de PQRS.")

        

        with c_i2:

            # INSIGHT 2: IMPACTO FINANCIERO (NUEVO WOW)

            # Clientes con satisfacción < 60% que tienen reclamos

            riesgo_ch = df_f[(df_f['Satisfaccion'] < 60) & (df_f['Reclamos'] > 0)]

            porc_riesgo = (len(riesgo_ch) / len(df_f)) * 100 if len(df_f) > 0 else 0

            st.warning(f"📉 **Impacto Financiero:** El **{porc_riesgo:.1f}%** de clientes están en riesgo crítico de abandono.")



        with c_i3:

            # INSIGHT 3: PEOR CANAL

            peor_c = df_f.groupby('Canal')['Satisfaccion'].mean().idxmin()

            st.info(f"🔄 **Canal Crítico:** El canal **{peor_c}** requiere rediseño de procesos.")



    # --- MÉTRICAS Y GRÁFICAS ---

    st.markdown("---")

    m1, m2, m3 = st.columns(3)

    if not df_f.empty:

        m1.metric("Satisfacción Promedio", f"{df_f['Satisfaccion'].mean():.1f}%")

        m2.metric("Auditorías", len(df_f))

        m3.metric("PQRS Registradas", int(df_f['Reclamos'].sum()))



    g1, g2 = st.columns(2)

    with g1:

        st.write("**🏆 Top Ciudades (Satisfacción)**")

        # CORRECCIÓN DE BUG: 'Ciudad Residencia'

        if not df_f.empty:

            chart_data = df_f.groupby('Ciudad Residencia')['Satisfaccion'].mean().sort_values(ascending=False).head(5)

            st.bar_chart(chart_data)

            

    with g2:

        st.write("**📈 Histórico de Calidad**")

        if not df_f.empty:

            df_ev = df_f.groupby('Fecha')['Satisfaccion'].mean().sort_index()

            st.line_chart(df_ev)



# ==========================================

# 5. TRAZABILIDAD E ISO

# ==========================================

st.markdown("---")

tab1, tab2 = st.tabs(["🗄️ Trazabilidad de Auditoría", "📑 Plan ISO 9001"])



with tab1:

    st.subheader("Base de Datos Maestra (SQL)")

    st.dataframe(db_actual, use_container_width=True)



with tab2:

    st.subheader("Numerales ISO y Planes de Acción")

    df_err = db_actual[db_actual['Motivo PQRS'] != "Ninguna (0 PQRS)"]

    if not df_err.empty:

        top_f = df_err['Motivo PQRS'].mode()[0]

        st.error(f"🚩 **Hallazgo Recurrente:** {top_f}")

        st.markdown(f"**Plan Sugerido:** Revisión inmediata del proceso bajo norma ISO 9001:2015.")



st.caption(f"Tecnoquímicas S.A. | Auditoría BI Gold v9.0 | {date.today()}")     
