import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.express as px
import hashlib
from datetime import date

# ==========================================
# 0. CONFIG
# ==========================================
st.set_page_config(page_title="TQ BI v14 PRO", layout="wide")

# ==========================================
# 1. SEGURIDAD (HASH REAL)
# ==========================================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def check_password():
    if not st.session_state.get("password_correct", False):
        st.title("🔐 Acceso Empresarial TQ")

        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")

        if st.button("Ingresar"):
            usuarios_db = {
                "admin": {"pass": hash_pass("tq2026"), "role": "Administrador"},
                "jhon.marin": {"pass": hash_pass("auditoria2026"), "role": "Auditor"}
            }

            if user in usuarios_db and hash_pass(password) == usuarios_db[user]["pass"]:
                st.session_state["password_correct"] = True
                st.session_state["usuario"] = user
                st.session_state["rol"] = usuarios_db[user]["role"]
                st.rerun()
            else:
                st.error("Credenciales inválidas")

        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 2. BASE DE DATOS
# ==========================================
DB = "tq_pro.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Fecha TEXT,
        Nombre TEXT,
        Contacto TEXT,
        Ciudad TEXT,
        Region TEXT,
        Canal TEXT,
        Satisfaccion REAL,
        Reclamos INTEGER,
        Motivo TEXT,
        Observaciones TEXT
    )
    """)
    conn.commit()
    conn.close()

@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM auditoria", conn)
    conn.close()
    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
    return df

init_db()

# ==========================================
# 3. CIUDADES DINÁMICAS (PRO)
# ==========================================
try:
    ciudades_df = pd.read_csv("ciudades_colombia.csv")
    CIUDADES = ciudades_df["ciudad"].unique()
except:
    CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla"]

REGIONES = ["Andina", "Caribe", "Pacífica", "Orinoquía", "Amazonía"]

# ==========================================
# 4. SIDEBAR
# ==========================================
st.sidebar.title("🏢 TQ BI PRO")
st.sidebar.write(f"👤 {st.session_state.usuario} | {st.session_state.rol}")

if st.sidebar.button("🚪 Cerrar sesión"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# FORMULARIO
with st.sidebar.form("form"):
    nombre = st.text_input("Nombre")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad", CIUDADES)
    region = st.selectbox("Región", REGIONES)
    canal = st.selectbox("Canal", ["Ventas", "Digital", "Farma"])
    sat = st.slider("Satisfacción", 0, 100, 80)
    pqrs = st.number_input("Reclamos", 0, 100, 0)
    motivo = st.selectbox("Falla", ["Ninguna","Calidad","Precios","Logística","Agotados","Atención"])
    obs = st.text_area("Observaciones")

    if st.form_submit_button("Guardar"):
        conn = sqlite3.connect(DB)
        conn.execute("""
        INSERT INTO auditoria (Fecha,Nombre,Contacto,Ciudad,Region,Canal,Satisfaccion,Reclamos,Motivo,Observaciones)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,(str(date.today()),nombre,contacto,ciudad,region,canal,sat,pqrs,motivo,obs))
        conn.commit()
        conn.close()
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. DASHBOARD
# ==========================================
st.title("📊 TQ BI Dashboard")

df = load_data()

if df.empty:
    st.info("No hay datos")
else:
    f1,f2 = st.columns(2)
    reg = f1.multiselect("Región", df["Region"].unique(), default=df["Region"].unique())
    can = f2.multiselect("Canal", df["Canal"].unique(), default=df["Canal"].unique())

    df_f = df[(df["Region"].isin(reg)) & (df["Canal"].isin(can))]

    if not df_f.empty:
        # KPI
        prom = len(df_f[df_f["Satisfaccion"]>=90])
        detr = len(df_f[df_f["Satisfaccion"]<70])
        nps = ((prom-detr)/len(df_f))*100 if len(df_f)>0 else 0

        k1,k2,k3,k4 = st.columns(4)

        k1.metric("NPS", f"{nps:.1f}")
        k2.metric("Satisfacción", f"{df_f['Satisfaccion'].mean():.1f}%")
        k3.metric("PQRS", int(df_f["Reclamos"].sum()))
        k4.metric("Tasa Falla", f"{(df_f['Reclamos'].sum()/len(df_f)):.2f}")

        # INSIGHT AUTOMÁTICO
        if df_f["Reclamos"].sum()>0:
            top = df_f.groupby("Region")["Reclamos"].sum().idxmax()
            st.error(f"Zona crítica: {top}")

        # GRÁFICOS
        st.plotly_chart(px.bar(df_f.groupby("Region")["Satisfaccion"].mean().reset_index(),
                               x="Region",y="Satisfaccion",color="Satisfaccion"))

# ==========================================
# 6. CRUD SEGURO
# ==========================================
st.markdown("---")
tab1,tab2 = st.tabs(["Gestión","ISO"])

with tab1:
    edited = st.data_editor(df)

    if st.button("Guardar cambios"):
        conn = sqlite3.connect(DB)

        for _,row in edited.iterrows():
            conn.execute("""
            UPDATE auditoria SET
            Fecha=?,Nombre=?,Contacto=?,Ciudad=?,Region=?,Canal=?,
            Satisfaccion=?,Reclamos=?,Motivo=?,Observaciones=?
            WHERE id=?
            """,(str(row["Fecha"]),row["Nombre"],row["Contacto"],row["Ciudad"],
                 row["Region"],row["Canal"],row["Satisfaccion"],row["Reclamos"],
                 row["Motivo"],row["Observaciones"],row["id"]))

        conn.commit()
        conn.close()
        st.success("Actualizado")
        st.rerun()

# ==========================================
# 7. ISO INTELIGENTE
# ==========================================
with tab2:
    st.subheader("📑 Análisis ISO Inteligente")

    fallas = df[df["Motivo"]!="Ninguna"]

    if fallas.empty:
        st.success("Sin fallas")
    else:
        conteo = fallas["Motivo"].value_counts()

        SOL = {
            "Calidad": "Revisión de lote",
            "Precios": "Auditoría comercial",
            "Logística": "Evaluar transporte",
            "Agotados": "Aumentar stock",
            "Atención": "Capacitación"
        }

        for falla,cantidad in conteo.items():

            if cantidad > 20:
                prioridad = "🔴 ALTA"
            elif cantidad > 10:
                prioridad = "🟠 MEDIA"
            else:
                prioridad = "🟢 BAJA"

            st.markdown(f"""
            ### {falla}
            - Casos: {cantidad}
            - Prioridad: {prioridad}
            - Acción: {SOL.get(falla,"Análisis")}
            """)

# ==========================================
st.caption("TQ BI PRO v14 | Nivel Empresa Real 🚀")
