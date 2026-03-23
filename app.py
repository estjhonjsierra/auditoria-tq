import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import hashlib
from datetime import date

# ================================
# IMPORT PDF SEGURO (NO ROMPE APP)
# ================================
try:
    from fpdf import FPDF
    PDF_OK = True
except:
    PDF_OK = False

# ================================
# CONFIG
# ================================
st.set_page_config(page_title="TQ BI Enterprise v16.3", layout="wide")

# ================================
# SEGURIDAD
# ================================
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

            user = user.strip()
            password_hash = hash_pass(password)

            if user in usuarios_db and password_hash == usuarios_db[user]["pass"]:
                st.session_state["password_correct"] = True
                st.session_state["usuario"] = user
                st.session_state["rol"] = usuarios_db[user]["role"]
                st.rerun()
            else:
                st.error("❌ Credenciales inválidas")

        return False
    return True

if not check_password():
    st.stop()

# ================================
# BASE DE DATOS
# ================================
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

# ================================
# PDF
# ================================
def generar_pdf(df, nps, avg, usuario):
    if not PDF_OK:
        return None

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "TECNOQUIMICAS S.A - INFORME ESTRATEGICO", ln=True, align="C")

    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 8, f"Usuario: {usuario} | Fecha: {date.today()}", ln=True)

    pdf.ln(5)

    pdf.cell(190, 8, f"NPS: {nps:.1f}", ln=True)
    pdf.cell(190, 8, f"Satisfaccion: {avg:.1f}%", ln=True)

    pdf.ln(5)

    fallas = df[df["Motivo"] != "Ninguna"] if not df.empty else pd.DataFrame()

    if not fallas.empty:
        for _, r in fallas.iterrows():
            txt = f"{r['Ciudad']} - {r['Motivo']} - {str(r['Observaciones'])[:120]}"
            pdf.multi_cell(0, 6, txt)
    else:
        pdf.cell(190, 8, "Sin hallazgos", ln=True)

    return pdf.output(dest="S").encode("latin-1")

# ================================
# SIDEBAR
# ================================
st.sidebar.title("🏢 TQ BI PRO")
st.sidebar.write(f"👤 {st.session_state.usuario}")
st.sidebar.write(f"Rol: {st.session_state.rol}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

CIUDADES = sorted([
    "Leticia","Medellín","Arauca","Barranquilla","Cartagena","Tunja","Manizales",
    "Florencia","Yopal","Popayán","Valledupar","Quibdó","Montería","Bogotá",
    "Inírida","San José del Guaviare","Neiva","Riohacha","Santa Marta",
    "Villavicencio","Pasto","Cúcuta","Mocoa","Armenia","Pereira","San Andrés",
    "Bucaramanga","Sincelejo","Ibagué","Cali","Mitú","Puerto Carreño","Soacha",
    "Bello","Soledad","Buenaventura","Palmira","Tuluá","Ipiales","Barrancabermeja"
])

REGIONES = ["Amazonía","Andina","Caribe","Insular","Orinoquía","Pacífica"]

with st.sidebar.form("form"):
    nombre = st.text_input("Nombre")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad", CIUDADES)
    region = st.selectbox("Región", REGIONES)
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
        st.cache_data.clear()
        st.success("Registro guardado")
        st.rerun()

# ================================
# DASHBOARD
# ================================
st.title("📊 Dashboard TQ Calidad")

df = load_data()

# Filtros SIEMPRE visibles
f1,f2 = st.columns(2)
reg_sel = f1.multiselect("Filtrar Región", REGIONES, default=REGIONES)
can_sel = f2.multiselect("Filtrar Canal", ["Ventas","Digital","Farma","Institucional"], default=["Ventas","Digital","Farma","Institucional"])

df_f = df[(df["Region"].isin(reg_sel)) & (df["Canal"].isin(can_sel))] if not df.empty else pd.DataFrame()

# Variables seguras (NO MÁS ERRORES)
nps = 0
avg_sat = 0

if not df_f.empty:

    prom = len(df_f[df_f["Satisfaccion"]>=90])
    detr = len(df_f[df_f["Satisfaccion"]<70])

    nps = ((prom-detr)/len(df_f))*100
    avg_sat = df_f["Satisfaccion"].mean()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("NPS", f"{nps:.1f}")
    k2.metric("Satisfacción", f"{avg_sat:.1f}%")
    k3.metric("PQRS", int(df_f["Reclamos"].sum()))
    k4.metric("Tasa Falla", f"{(df_f['Reclamos'].sum()/len(df_f)):.2f}")

    # 🔥 GRÁFICO NIVEL DIOS
    fig = px.bar(
        df_f.groupby("Region")["Satisfaccion"].mean().reset_index(),
        x="Region",
        y="Satisfaccion",
        color="Satisfaccion",
        color_continuous_scale="RdYlGn",
        text_auto=".2f",
        title="Nivel de Satisfacción por Región"
    )

    fig.update_layout(
        title_x=0.5,
        xaxis_title="Región",
        yaxis_title="Satisfacción (%)"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No hay datos registrados aún.")

# ================================
# TABS
# ================================
st.markdown("---")
tab1,tab2 = st.tabs(["🛠️ Gestión","📑 ISO 9001"])

with tab1:
    if not df.empty:
        edit = st.data_editor(df, use_container_width=True)
        if st.button("Actualizar"):
            conn = sqlite3.connect(DB)
            for _,r in edit.iterrows():
                conn.execute("""UPDATE auditoria SET Fecha=?,Nombre=?,Contacto=?,Ciudad=?,Region=?,Canal=?,Satisfaccion=?,Reclamos=?,Motivo=?,Observaciones=? WHERE id=?""",
                             (str(r["Fecha"]),r["Nombre"],r["Contacto"],r["Ciudad"],r["Region"],r["Canal"],r["Satisfaccion"],r["Reclamos"],r["Motivo"],r["Observaciones"],r["id"]))
            conn.commit()
            conn.close()
            st.success("Base de datos actualizada")
            st.rerun()
    else:
        st.write("Sin datos para gestionar")

with tab2:
    st.subheader("Auditoría ISO 9001")

    if PDF_OK:
        pdf = generar_pdf(df_f, nps, avg_sat, st.session_state.usuario)
        st.download_button("📥 Descargar Informe PDF", pdf, "Reporte_TQ.pdf")
    else:
        st.warning("⚠️ Instala 'fpdf' en requirements.txt")

    if not df_f.empty:
        fallas = df_f[df_f["Motivo"]!="Ninguna"]
        if not fallas.empty:
            for f,c in fallas["Motivo"].value_counts().items():
                st.warning(f"{f}: {c} casos")
        else:
            st.success("Sin hallazgos ISO")

st.caption("TQ BI Enterprise v16.3 FINAL 🚀")
