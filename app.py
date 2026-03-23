import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import hashlib
from datetime import date

# ================================
# IMPORT PDF SEGURO
# ================================
try:
    from fpdf import FPDF
    PDF_OK = True
except:
    PDF_OK = False

# ================================
# CONFIG
# ================================
st.set_page_config(page_title="TQ BI Enterprise v17.0 Gold", layout="wide", page_icon="💊")

# MATRIZ TÉCNICA ISO 9001 (Información Verídica)
MATRIZ_ISO = {
    "Calidad": {
        "numeral": "8.7 Control de las salidas no conformes",
        "hallazgo": "Desviación en los estándares técnicos del producto o empaque.",
        "solucion": "Bloqueo inmediato de lote, análisis de causa raíz (Ishikawa) y disposición final según protocolo de calidad TQ."
    },
    "Precios": {
        "numeral": "8.2.1 Comunicación con el cliente",
        "hallazgo": "Inconsistencia entre precio facturado y precio exhibido/pactado.",
        "solucion": "Auditoría de lista de precios en SAP, ajuste de notas crédito y actualización de POP en punto de venta."
    },
    "Logística": {
        "numeral": "8.4 Control de procesos externos (Transporte)",
        "hallazgo": "Incumplimiento en tiempos de entrega o averías en tránsito.",
        "solucion": "Re-evaluación del transportador (KPI de entrega), optimización de ruta y refuerzo en estiba de carga."
    },
    "Agotados": {
        "numeral": "8.1 Planificación y control operacional",
        "hallazgo": "Ruptura de stock que afecta la continuidad del servicio.",
        "solucion": "Ajuste de pronóstico de demanda (Forecasting), revisión de stock de seguridad y aceleración de orden de reposición."
    },
    "Atención": {
        "numeral": "7.2 Competencia",
        "hallazgo": "Falta de conocimiento técnico o protocolo de servicio por parte del personal.",
        "solucion": "Plan de re-entrenamiento en Universidad TQ, evaluación de competencias y seguimiento de protocolo de visita."
    }
}

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
            if user.strip() in usuarios_db and hash_pass(password) == usuarios_db[user.strip()]["pass"]:
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

def load_data():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM auditoria", conn)
    conn.close()
    if not df.empty:
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
    return df

# ================================
# PDF PROFESIONAL
# ================================
def generar_pdf(df, nps, avg, usuario):
    if not PDF_OK: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "TECNOQUIMICAS S.A - REPORTE DE AUDITORIA ISO 9001", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 8, f"Auditor: {usuario} | Fecha: {date.today()}", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "RESUMEN EJECUTIVO", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f"NPS: {nps:.1f}%")
    pdf.cell(95, 8, f"Satisfaccion: {avg:.1f}%", ln=True)
    pdf.ln(5)

    fallas = df[df["Motivo"] != "Ninguna"]
    if not fallas.empty:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "HALLAZGOS Y ACCIONES CORRECTIVAS", ln=True)
        pdf.set_font("Arial", "", 9)
        for _, r in fallas.iterrows():
            info = MATRIZ_ISO.get(r['Motivo'], {})
            txt = f"CIUDAD: {r['Ciudad']} | FALLA: {r['Motivo']} | ISO: {info.get('numeral','')}\nACCION: {info.get('solucion','')}\nOBS: {r['Observaciones']}\n"
            pdf.multi_cell(0, 5, txt)
            pdf.ln(2)
    return pdf.output(dest="S").encode("latin-1")

# ================================
# SIDEBAR
# ================================
st.sidebar.title("🏢 TQ BI PRO v17.0")
st.sidebar.write(f"👤 {st.session_state.usuario} ({st.session_state.rol})")

CIUDADES = sorted([
    "Leticia","Medellín","Arauca","Barranquilla","Cartagena","Tunja","Manizales","Florencia","Yopal","Popayán","Valledupar","Quibdó","Montería","Bogotá","Inírida","San José del Guaviare","Neiva","Riohacha","Santa Marta","Villavicencio","Pasto","Cúcuta","Mocoa","Armenia","Pereira","San Andrés","Bucaramanga","Sincelejo","Ibagué","Cali","Mitú","Puerto Carreño","Soacha","Bello","Soledad","Buenaventura","Palmira","Tuluá","Ipiales","Barrancabermeja"
])

ZONAS = ["Antioquia", "Valle y Cauca", "Centro (Bogotá/Boyacá)", "Costa Norte", "Santanderes", "Eje Cafetero", "Sur (Huila/Nariño)", "Llanos/Amazonía"]

with st.sidebar.form("form"):
    st.subheader("📝 Nuevo Registro")
    nombre = st.text_input("Nombre del Punto")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad", CIUDADES)
    zona = st.selectbox("Zona Operativa", ZONAS)
    canal = st.selectbox("Canal", ["Ventas","Digital","Farma","Institucional"])
    sat = st.slider("Satisfacción",0,100,80)
    pqrs = st.number_input("Reclamos",0,100,0)
    motivo = st.selectbox("Falla",["Ninguna","Calidad","Precios","Logística","Agotados","Atención"])
    obs = st.text_area("Observaciones")

    if st.form_submit_button("💾 Guardar"):
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO auditoria VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
                     (str(date.today()),nombre,contacto,ciudad,zona,canal,sat,pqrs,motivo,obs))
        conn.commit(); conn.close()
        st.cache_data.clear(); st.success("✅ Guardado"); st.rerun()

# OPCIÓN BORRAR ÚLTIMO (SIDEBAR)
if st.sidebar.button("🗑️ Borrar Último Registro"):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM auditoria WHERE id = (SELECT MAX(id) FROM auditoria)")
    conn.commit(); conn.close()
    st.cache_data.clear(); st.warning("Registro eliminado"); st.rerun()

if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear(); st.rerun()

# ================================
# DASHBOARD
# ================================
st.title("📊 Dashboard TQ Calidad Estratégica")
df = load_data()

f1, f2 = st.columns(2)
zona_sel = f1.multiselect("Filtrar Zona", ZONAS, default=ZONAS)
can_sel = f2.multiselect("Filtrar Canal", ["Ventas","Digital","Farma","Institucional"], default=["Ventas","Digital","Farma","Institucional"])

df_f = df[(df["Region"].isin(zona_sel)) & (df["Canal"].isin(can_sel))] if not df.empty else pd.DataFrame()

nps, avg_sat = 0, 0

if not df_f.empty:
    prom = len(df_f[df_f["Satisfaccion"]>=90])
    detr = len(df_f[df_f["Satisfaccion"]<70])
    nps = ((prom-detr)/len(df_f))*100
    avg_sat = df_f["Satisfaccion"].mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("NPS (Loyalty)", f"{nps:.1f}%")
    k2.metric("Satisfacción Avg", f"{avg_sat:.1f}%")
    k3.metric("PQRS Totales", int(df_f["Reclamos"].sum()))
    k4.metric("Tasa Falla", f"{(df_f['Reclamos'].sum()/len(df_f)):.2f}")

    fig = px.bar(
        df_f.groupby("Region")["Satisfaccion"].mean().reset_index(),
        x="Region", y="Satisfaccion", color="Satisfaccion",
        color_continuous_scale="RdYlGn", text_auto=".1f",
        title="Nivel de Satisfacción por Zona Operativa"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos registrados aún.")

# ================================
# TABS PRO
# ================================
st.markdown("---")
tab1, tab2 = st.tabs(["🛠️ Gestión e Histórico","📑 Auditoría ISO 9001 PRO"])

with tab1:
    st.subheader("Histórico de Auditorías")
    if not df.empty:
        # Buscador por ID para borrar
        col_del1, col_del2 = st.columns([1,3])
        id_borrar = col_del1.number_input("ID a borrar", min_value=0, step=1)
        if col_del2.button("🗑️ Eliminar Registro Permanente"):
            conn = sqlite3.connect(DB)
            conn.execute(f"DELETE FROM auditoria WHERE id = {id_borrar}")
            conn.commit(); conn.close()
            st.cache_data.clear(); st.success(f"ID {id_borrar} borrado"); st.rerun()

        edit = st.data_editor(df, use_container_width=True)
        if st.button("Actualizar Cambios"):
            conn = sqlite3.connect(DB)
            for _,r in edit.iterrows():
                conn.execute("""UPDATE auditoria SET Fecha=?,Nombre=?,Contacto=?,Ciudad=?,Region=?,Canal=?,Satisfaccion=?,Reclamos=?,Motivo=?,Observaciones=? WHERE id=?""",
                             (str(r["Fecha"]),r["Nombre"],r["Contacto"],r["Ciudad"],r["Region"],r["Canal"],r["Satisfaccion"],r["Reclamos"],r["Motivo"],r["Observaciones"],r["id"]))
            conn.commit(); conn.close()
            st.success("Base de datos sincronizada"); st.rerun()
    else:
        st.write("Sin datos")

with tab2:
    st.subheader("Análisis de No Conformidades ISO 9001:2015")
    
    if PDF_OK:
        pdf_file = generar_pdf(df_f, nps, avg_sat, st.session_state.usuario)
        st.download_button("📥 Descargar Informe Técnico PDF", pdf_file, f"Reporte_ISO_{date.today()}.pdf")

    if not df_f.empty:
        fallas = df_f[df_f["Motivo"]!="Ninguna"]
        if not fallas.empty:
            for f, c in fallas["Motivo"].value_counts().items():
                info = MATRIZ_ISO.get(f, {})
                with st.expander(f"🔴 {f.upper()}: {c} CASOS DETECTADOS"):
                    st.error(f"**Numeral ISO:** {info.get('numeral')}")
                    st.write(f"**Hallazgo Técnico:** {info.get('hallazgo')}")
                    st.success(f"**Acción Correctiva Sugerida:** {info.get('solucion')}")
        else:
            st.success("✅ La operación cumple con todos los estándares ISO 9001 en este filtro.")

st.caption("TQ BI Enterprise v17.0 FINAL | Sistema de Gestión de Calidad 🚀")
