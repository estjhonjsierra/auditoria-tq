import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import hashlib
from datetime import date
from fpdf import FPDF

st.set_page_config(page_title="TQ BI Enterprise FINAL", layout="wide")

# =========================
# SEGURIDAD
# =========================
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
                "jhonmarin": {"pass": hash_pass("Jhonmarin31."), "role": "Auditor Senior"}
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

# =========================
# BASE DE DATOS
# =========================
DB = "tq_pro.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Fecha TEXT, Nombre TEXT, Contacto TEXT, Ciudad TEXT,
        Region TEXT, Canal TEXT, Satisfaccion REAL,
        Reclamos INTEGER, Motivo TEXT, Observaciones TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM auditoria", conn)
    conn.close()
    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
    return df

# =========================
# PDF PRO
# =========================
def generar_pdf_ejecutivo(df_filtrado, nps, avg_sat, usuario):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "TECNOQUIMICAS S.A. - INFORME ESTRATEGICO", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Emitido por: {usuario} | Fecha: {date.today()}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_fill_color(0, 74, 173)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "KPIs", ln=True, fill=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    pdf.cell(95, 10, f"NPS: {nps:.1f}")
    pdf.cell(95, 10, f"Satisfacción: {avg_sat:.1f}%", ln=True)

    pdf.ln(5)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "No Conformidades", ln=True, fill=True)

    pdf.set_font("Arial", "", 9)
    fallas = df_filtrado[df_filtrado["Motivo"] != "Ninguna"]

    if not fallas.empty:
        for _, row in fallas.iterrows():
            obs = str(row["Observaciones"])[:150]
            txt = f"ID {row['id']} | {row['Ciudad']} | {row['Motivo']} | {obs}"
            pdf.multi_cell(0, 8, txt)
    else:
        pdf.cell(0, 10, "Sin hallazgos.", ln=True)

    return pdf.output(dest="S").encode("latin-1")

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🏢 TQ BI PRO")
st.sidebar.write(f"{st.session_state.usuario} | {st.session_state.rol}")

if st.sidebar.button("Cerrar sesión"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

with st.sidebar.form("form"):
    nombre = st.text_input("Nombre")
    contacto = st.text_input("Contacto")
    ciudad = st.text_input("Ciudad")
    region = st.selectbox("Región", ["Andina","Caribe","Pacífica"])
    canal = st.selectbox("Canal", ["Ventas","Digital"])
    sat = st.slider("Satisfacción",0,100,80)
    pqrs = st.number_input("Reclamos",0,100,0)
    motivo = st.selectbox("Falla",["Ninguna","Calidad","Precios","Logística"])
    obs = st.text_area("Observaciones")

    if st.form_submit_button("Guardar"):
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO auditoria VALUES (NULL,?,?,?,?,?,?,?,?,?)",
                     (str(date.today()),nombre,contacto,ciudad,region,canal,sat,pqrs,motivo,obs))
        conn.commit()
        conn.close()
        st.cache_data.clear()
        st.rerun()

# =========================
# DASHBOARD
# =========================
st.title("📊 Dashboard")

df = load_data()

if df.empty:
    st.info("Sin datos")
else:
    df_f = df.copy()

    prom = len(df_f[df_f["Satisfaccion"]>=90])
    detr = len(df_f[df_f["Satisfaccion"]<70])
    nps = ((prom-detr)/len(df_f))*100
    avg_sat = df_f["Satisfaccion"].mean()

    col1,col2,col3 = st.columns(3)
    col1.metric("NPS", round(nps,1))
    col2.metric("Satisfacción", round(avg_sat,1))
    col3.metric("PQRS", int(df_f["Reclamos"].sum()))

    # 🔥 NUEVO: gráfico fallas
    fallas = df_f[df_f["Motivo"]!="Ninguna"]
    if not fallas.empty:
        st.plotly_chart(px.pie(fallas, names="Motivo", values="Reclamos"), use_container_width=True)

# =========================
# GESTIÓN
# =========================
st.markdown("---")
tab1, tab2 = st.tabs(["Gestión","ISO"])

with tab1:
    edited = st.data_editor(df, use_container_width=True)

    if st.button("Actualizar"):
        conn = sqlite3.connect(DB)
        for _, row in edited.iterrows():
            conn.execute("UPDATE auditoria SET Nombre=? WHERE id=?",
                         (row["Nombre"], row["id"]))
        conn.commit()
        conn.close()
        st.success("Actualizado")
        st.rerun()

    # 🔥 NUEVO: eliminar
    id_del = st.number_input("ID a eliminar",0,1000,0)
    if st.button("Eliminar"):
        conn = sqlite3.connect(DB)
        conn.execute("DELETE FROM auditoria WHERE id=?", (id_del,))
        conn.commit()
        conn.close()
        st.success("Eliminado")
        st.rerun()

with tab2:
    pdf_data = generar_pdf_ejecutivo(df_f, nps, avg_sat, st.session_state.usuario)
    st.download_button("Descargar PDF", pdf_data, "reporte.pdf")

st.caption("TQ BI FINAL 🚀")
