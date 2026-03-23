import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import hashlib
from datetime import date

# PDF seguro
try:
    from fpdf import FPDF
    PDF_OK = True
except:
    PDF_OK = False

st.set_page_config(page_title="TQ BI Enterprise v16.3", layout="wide")

# ================= SEGURIDAD =================
def hash_pass(p):
    return hashlib.sha256(p.strip().encode()).hexdigest()

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

            if user.strip() in usuarios_db and hash_pass(password) == usuarios_db[user.strip()]["pass"]:
                st.session_state["password_correct"] = True
                st.session_state["usuario"] = user
                st.session_state["rol"] = usuarios_db[user.strip()]["role"]
                st.rerun()
            else:
                st.error("❌ Credenciales inválidas")
        return False
    return True

if not check_password():
    st.stop()

# ================= DB =================
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

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM auditoria", conn)
    conn.close()
    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
    return df

# ================= PDF =================
def generar_pdf(df, nps, avg, usuario):
    if not PDF_OK:
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(190,10,"INFORME TQ",ln=True,align="C")
    pdf.set_font("Arial","",10)
    pdf.cell(190,8,f"{usuario} - {date.today()}",ln=True)

    pdf.ln(5)
    pdf.cell(190,8,f"NPS: {nps:.1f}",ln=True)
    pdf.cell(190,8,f"Satisfaccion: {avg:.1f}%",ln=True)

    fallas = df[df["Motivo"]!="Ninguna"]
    pdf.ln(5)

    if not fallas.empty:
        for _,r in fallas.iterrows():
            pdf.multi_cell(0,6,f"{r['Ciudad']} - {r['Motivo']} - {str(r['Observaciones'])[:100]}")
    else:
        pdf.cell(190,8,"Sin fallas",ln=True)

    return pdf.output(dest="S").encode("latin-1")

# ================= SIDEBAR =================
st.sidebar.title("🏢 TQ BI PRO")
st.sidebar.write(f"👤 {st.session_state.usuario}")

CIUDADES = sorted([
    "Leticia","Medellín","Arauca","Barranquilla","Cartagena","Tunja","Manizales",
    "Florencia","Yopal","Popayán","Valledupar","Quibdó","Montería","Bogotá",
    "Inírida","San José del Guaviare","Neiva","Riohacha","Santa Marta",
    "Villavicencio","Pasto","Cúcuta","Mocoa","Armenia","Pereira","San Andrés",
    "Bucaramanga","Sincelejo","Ibagué","Cali","Mitú","Puerto Carreño","Soacha",
    "Bello","Soledad","Buenaventura","Palmira","Tuluá","Ipiales","Barrancabermeja"
])

# 🔥 REGIONES REALES (CAMBIO)
REGIONES = ["Antioquia","Bogotá","Valle del Cauca","Atlántico","Santander","Cundinamarca","Bolívar","Nariño"]

with st.sidebar.form("form"):
    nombre = st.text_input("Nombre")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad", CIUDADES)
    region = st.selectbox("Zona", REGIONES)
    canal = st.selectbox("Canal", ["Ventas","Digital","Farma","Institucional"])
    sat = st.slider("Satisfacción",0,100,80)
    pqrs = st.number_input("Reclamos",0,100,0)
    motivo = st.selectbox("Falla",["Ninguna","Calidad","Precios","Logística","Agotados","Atención"])
    obs = st.text_area("Observaciones")

    if st.form_submit_button("Guardar"):
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO auditoria VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
                     (str(date.today()),nombre,contacto,ciudad,region,canal,sat,pqrs,motivo,obs))
        conn.commit()
        conn.close()
        st.success("Guardado")
        st.rerun()

    # 🔴 BORRAR TODO
    if st.form_submit_button("🗑️ Borrar Todo"):
        conn = sqlite3.connect(DB)
        conn.execute("DELETE FROM auditoria")
        conn.commit()
        conn.close()
        st.success("Base eliminada")
        st.rerun()

# ================= DASHBOARD =================
st.title("📊 Dashboard TQ")

df = load_data()

f1,f2 = st.columns(2)
reg_sel = f1.multiselect("Zona", REGIONES, default=REGIONES)
can_sel = f2.multiselect("Canal", ["Ventas","Digital","Farma","Institucional"], default=["Ventas","Digital","Farma","Institucional"])

df_f = df[(df["Region"].isin(reg_sel)) & (df["Canal"].isin(can_sel))] if not df.empty else pd.DataFrame()

nps = 0
avg_sat = 0

if not df_f.empty:
    prom = len(df_f[df_f["Satisfaccion"]>=90])
    detr = len(df_f[df_f["Satisfaccion"]<70])
    nps = ((prom-detr)/len(df_f))*100
    avg_sat = df_f["Satisfaccion"].mean()

    st.metric("NPS",f"{nps:.1f}")
    st.metric("Satisfacción",f"{avg_sat:.1f}%")

    st.plotly_chart(px.bar(df_f,x="Region",y="Satisfaccion"))

# ================= TABS =================
tab1,tab2 = st.tabs(["Gestión","ISO"])

with tab1:
    if not df.empty:
        for i,row in df.iterrows():
            col1,col2 = st.columns([4,1])
            col1.write(row.to_dict())

            # 🔴 BORRAR INDIVIDUAL
            if col2.button("🗑️", key=row["id"]):
                conn = sqlite3.connect(DB)
                conn.execute("DELETE FROM auditoria WHERE id=?", (row["id"],))
                conn.commit()
                conn.close()
                st.rerun()

with tab2:
    st.subheader("ISO 9001 PRO")

    if PDF_OK:
        pdf = generar_pdf(df_f,nps,avg_sat,st.session_state.usuario)
        st.download_button("PDF",pdf)

    # 🔥 MATRIZ ISO REAL
    acciones = {
        "Calidad":"Aplicar control de producto no conforme (ISO 9001:2015 8.7), análisis causa raíz y plan de acción.",
        "Precios":"Revisión de política comercial y transparencia (8.2.1 comunicación con cliente).",
        "Logística":"Evaluar proveedores externos y tiempos de entrega (8.4 control externo).",
        "Agotados":"Planificación de inventarios y demanda (8.1 control operacional).",
        "Atención":"Capacitación del personal y mejora en servicio (7.2 competencia)."
    }

    if not df_f.empty:
        fallas = df_f[df_f["Motivo"]!="Ninguna"]
        for f,c in fallas["Motivo"].value_counts().items():
            st.error(f"{f} ({c} casos)")
            st.info(acciones.get(f,"Acción general ISO"))

st.caption("TQ BI NIVEL DIOS 🚀")
