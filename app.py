import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.express as px
import hashlib
from datetime import date
from fpdf import FPDF 

# ==========================================
# 0. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="TQ BI Enterprise v16", layout="wide")

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ==========================================
# 1. SEGURIDAD Y ACCESO (INTACTO)
# ==========================================
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

# ==========================================
# 2. BASE DE DATOS
# ==========================================
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
# 3. EXPORTACIÓN PDF EJECUTIVA (CON PROTECCIÓN DE NULOS)
# ==========================================
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
    pdf.cell(190, 10, " 1. INDICADORES CLAVE DE DESEMPENO (KPIs)", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    pdf.cell(95, 10, f"Net Promoter Score (NPS): {nps:.1f}")
    pdf.cell(95, 10, f"Satisfaccion Promedio: {avg_sat:.1f}%", ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, " 2. DESGLOSE DE NO CONFORMIDADES FILTRADAS", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Arial", "", 9)
    
    fallas_pdf = df_filtrado[df_filtrado['Motivo'] != 'Ninguna']
    if not fallas_pdf.empty:
        for _, row in fallas_pdf.iterrows():
            # ✅ MICRO DETALLE: str() para evitar error en nulos
            obs_clean = str(row['Observaciones'])[:50]
            txt = f"ID {row['id']} | Ciudad: {row['Ciudad']} | Falla: {row['Motivo']} | Obs: {obs_clean}..."
            pdf.cell(0, 8, txt, ln=True)
    else:
        pdf.cell(0, 10, "No se registran hallazgos en este periodo/filtro.", ln=True)
        
    return pdf.output(dest="S").encode("latin-1")

# ==========================================
# 4. SIDEBAR (CIUDADES Y REGIONES COMPLETAS)
# ==========================================
st.sidebar.title("🏢 TQ BI PRO")
st.sidebar.write(f"👤 {st.session_state.usuario} | {st.session_state.rol}")

if st.sidebar.button("🚪 Cerrar sesión"):
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()

CIUDADES_COL = sorted([
    "Leticia", "Medellín", "Arauca", "Barranquilla", "Cartagena", "Tunja", "Manizales", "Florencia", "Yopal", "Popayán", 
    "Valledupar", "Quibdó", "Montería", "Bogotá", "Inírida", "San José del Guaviare", "Neiva", "Riohacha", "Santa Marta", 
    "Villavicencio", "Pasto", "Cúcuta", "Mocoa", "Armenia", "Pereira", "San Andrés", "Bucaramanga", "Sincelejo", "Ibagué", 
    "Cali", "Mitú", "Puerto Carreño", "Soacha", "Bello", "Soledad", "Buenaventura", "Palmira", "Tuluá", "Ipiales", "Barrancabermeja"
])

REGIONES_COL = sorted(["Amazonía", "Andina", "Caribe", "Insular", "Orinoquía", "Pacífica"])

with st.sidebar.form("form"):
    nombre = st.text_input("Nombre")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad", CIUDADES_COL)
    region = st.selectbox("Región", REGIONES_COL)
    canal = st.selectbox("Canal", ["Ventas", "Digital", "Farma", "Institucional"])
    sat = st.slider("Satisfacción", 0, 100, 80)
    pqrs = st.number_input("Reclamos", 0, 100, 0)
    motivo = st.selectbox("Falla", ["Ninguna","Calidad","Precios","Logística","Agotados","Atención"])
    obs = st.text_area("Observaciones")

    if st.form_submit_button("Guardar Registro"):
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO auditoria (Fecha,Nombre,Contacto,Ciudad,Region,Canal,Satisfaccion,Reclamos,Motivo,Observaciones) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (str(date.today()),nombre,contacto,ciudad,region,canal,sat,pqrs,motivo,obs))
        conn.commit(); conn.close()
        st.cache_data.clear(); st.rerun()

# ==========================================
# 5. DASHBOARD
# ==========================================
st.title("📊 TQ Dashboard de Calidad")
df = load_data()

if df.empty:
    st.info("No hay datos registrados aún.")
else:
    f1, f2 = st.columns(2)
    reg_sel = f1.multiselect("Filtrar Región", df["Region"].unique(), default=df["Region"].unique())
    can_sel = f2.multiselect("Filtrar Canal", df["Canal"].unique(), default=df["Canal"].unique())
    df_f = df[(df["Region"].isin(reg_sel)) & (df["Canal"].isin(can_sel))]

    if not df_f.empty:
        fallas_data = df_f[df_f["Motivo"] != "Ninguna"]
        if not fallas_data.empty and fallas_data["Reclamos"].sum() > 0:
            top_falla = fallas_data.groupby("Motivo")["Reclamos"].sum().idxmax()
            st.error(f"🚨 **INSIGHT CRÍTICO:** El principal problema de reclamos es: **{top_falla}**.")

        prom = len(df_f[df_f["Satisfaccion"]>=90]); detr = len(df_f[df_f["Satisfaccion"]<70])
        nps = ((prom-detr)/len(df_f))*100 if len(df_f)>0 else 0
        avg_sat = df_f['Satisfaccion'].mean()

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("NPS", f"{nps:.1f}")
        k2.metric("Satisfacción Avg", f"{avg_sat:.1f}%")
        k3.metric("Total PQRS", int(df_f["Reclamos"].sum()))
        
        tasa = (df_f['Reclamos'].sum()/len(df_f)) if len(df_f)>0 else 0
        k4.metric("Tasa Falla", f"{tasa:.2f}")

        st.plotly_chart(px.bar(df_f.groupby("Region")["Satisfaccion"].mean().reset_index(), x="Region", y="Satisfaccion", color="Satisfaccion", color_continuous_scale='RdYlGn'), use_container_width=True)
    else:
        st.warning("Ajuste los filtros.")

# ==========================================
# 6. GESTIÓN E ISO PRO
# ==========================================
st.markdown("---")
tab1, tab2 = st.tabs(["🛠️ Gestión de Datos", "📑 Auditoría ISO 9001 PRO"])

with tab1:
    edited = st.data_editor(df, use_container_width=True)
    if st.button("Sincronizar Cambios"):
        conn = sqlite3.connect(DB)
        for _, row in edited.iterrows():
            conn.execute("UPDATE auditoria SET Fecha=?, Nombre=?, Contacto=?, Ciudad=?, Region=?, Canal=?, Satisfaccion=?, Reclamos=?, Motivo=?, Observaciones=? WHERE id=?", 
                         (str(row["Fecha"]), row["Nombre"], row["Contacto"], row["Ciudad"], row["Region"], row["Canal"], row["Satisfaccion"], row["Reclamos"], row["Motivo"], row["Observaciones"], row["id"]))
        conn.commit(); conn.close(); st.success("Base de datos actualizada"); st.rerun()

with tab2:
    st.subheader("Análisis Consultor ISO 9001:2015")
    fallas_audit = df_f[df_f["Motivo"] != "Ninguna"] if not df_f.empty else pd.DataFrame()

    if not fallas_audit.empty:
        pdf_data = generar_pdf_ejecutivo(df_f, nps if 'nps' in locals() else 0, avg_sat if 'avg_sat' in locals() else 0, st.session_state.usuario)
        st.download_button("📥 DESCARGAR INFORME EJECUTIVO PDF", pdf_data, f"Informe_Auditoria_TQ_{date.today()}.pdf", "application/pdf")
        
        MATRIZ_PRO = {
            "Calidad": ("8.7", "Control de producto no conforme", "Bloqueo preventivo de lote + Análisis de causa raíz.", "Gerente de Planta", "24h"),
            "Precios": ("8.2.1", "Comunicación con el cliente", "Auditoría de márgenes + Ajuste de política comercial.", "Dir. Comercial", "48h"),
            "Logística": ("8.4", "Control de procesos externos", "Re-evaluación del transportador + Rediseño de ruta.", "Jefe Logística", "72h"),
            "Agotados": ("8.1", "Planificación y control operativo", "Ajuste de stock de seguridad + Revisión de demanda.", "Planeación", "48h"),
            "Atención": ("7.2", "Competencia y toma de conciencia", "Capacitación en Protocolos TQ + Plan de incentivos.", "Recursos Humanos", "1 semana")
        }
        
        conteo = fallas_audit["Motivo"].value_counts()
        for f, c in conteo.items():
            info = MATRIZ_PRO.get(f, ("ISO", "Hallazgo General", "Acción Correctiva", "Responsable", "Tiempo"))
            st.markdown(f"""
            <div style="padding:15px; border-radius:10px; border-left: 5px solid #d32f2f; background-color:#fff5f5; margin-bottom:10px">
                <h4 style="margin:0; color:#d32f2f;">{f} (Numeral {info[0]})</h4>
                <b>Impacto ISO:</b> {info[1]} | <b>Acción:</b> {info[2]}<br>
                <b>Responsable:</b> {info[3]} | <b>Tiempo de Respuesta:</b> {info[4]} | <b>Casos:</b> {c}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No se detectan fallas ISO en la selección actual.")

st.caption("TQ BI Enterprise v16 | Proyecto Jhon Marin 🚀")
