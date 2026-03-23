import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import hashlib
import io
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
# CONFIGURACIÓN Y ESTILO UI
# ================================
st.set_page_config(page_title="Auditoría de Calidad TQ", layout="wide", page_icon="💊")

# 📊 MATRIZ TÉCNICA ISO 9001 AMPLIADA (15 Motivos de Campo)
MATRIZ_ISO = {
    "Producto Vencido": {
        "numeral": "8.7 Control de las salidas no conformes",
        "hallazgo": "Hallazgo de lotes con fecha caducada en estantería.",
        "solucion": "Retiro inmediato del producto, bloqueo de lote y envío a destrucción.",
        "riesgo": "ALTO 🔴",
        "causa": "Falla grave en la rotación FIFO en el punto de venta.",
        "responsable": "Mercaderista / Supervisor",
        "sla": "Inmediato"
    },
    "Empaque Dañado": {
        "numeral": "8.5.4 Preservación",
        "hallazgo": "Cajas abolladas, sellos rotos o etiquetas sucias.",
        "solucion": "Retiro de la exhibición y gestión de avería/cambio.",
        "riesgo": "MEDIO 🟡",
        "causa": "Mala manipulación logística o de bodega en el PDV.",
        "responsable": "Mercaderista",
        "sla": "24 Horas"
    },
    "Agotado en Góndola": {
        "numeral": "8.5.1 Control de la producción y prestación del servicio",
        "hallazgo": "El producto está en bodega pero no está exhibido.",
        "solucion": "Surtido inmediato desde la bodega del punto de venta.",
        "riesgo": "MEDIO 🟡",
        "causa": "Falta de frecuencia de surtido por parte del personal.",
        "responsable": "Mercaderista / Auxiliar PDV",
        "sla": "Inmediato"
    },
    "Agotado en PDV": {
        "numeral": "8.1 Planificación y control operacional",
        "hallazgo": "No hay existencia física del producto (quiebre de stock).",
        "solucion": "Generar pedido urgente y revisar mínimos en el sistema.",
        "riesgo": "ALTO 🔴",
        "causa": "Falla en el pronóstico de demanda o retraso de entrega.",
        "responsable": "Comercial / Compras PDV",
        "sla": "48 Horas"
    },
    "Precio Incorrecto": {
        "numeral": "8.2.1 Comunicación con el cliente",
        "hallazgo": "El precio en etiqueta no coincide con el sistema (caja).",
        "solucion": "Actualización inmediata de la cenefa o viñeta de precio.",
        "riesgo": "ALTO 🔴",
        "causa": "Desincronización de bases de datos de precios.",
        "responsable": "Administrador PDV",
        "sla": "24 Horas"
    },
    "Falta Marcación Precio": {
        "numeral": "8.2.1 Comunicación con el cliente",
        "hallazgo": "El producto no tiene visibilidad de precio para el cliente.",
        "solucion": "Imprimir y colocar la etiqueta de precio faltante.",
        "riesgo": "MEDIO 🟡",
        "causa": "Omisión en el protocolo de exhibición.",
        "responsable": "Mercaderista",
        "sla": "Inmediato"
    },
    "Exhibición Deficiente": {
        "numeral": "8.5.1 Control de la producción y prestación del servicio",
        "hallazgo": "El producto no cumple con el planograma o está escondido.",
        "solucion": "Ajustar la cara del producto según planograma oficial TQ.",
        "riesgo": "MEDIO 🟡",
        "causa": "Desconocimiento o no aplicación del estándar visual.",
        "responsable": "Mercaderista / Supervisor",
        "sla": "24 Horas"
    },
    "Material POP Ausente": {
        "numeral": "8.2.1 Comunicación con el cliente",
        "hallazgo": "Rompetráficos, saltarines sucios, rotos o inexistentes.",
        "solucion": "Instalación de material publicitario nuevo y retiro del dañado.",
        "riesgo": "BAJO 🟢",
        "causa": "Falta de dotación o daño por terceros en la tienda.",
        "responsable": "Trade Marketing / Mercaderista",
        "sla": "72 Horas"
    },
    "Invasión Competencia": {
        "numeral": "8.2.2 Determinación de requisitos para los productos",
        "hallazgo": "Invasión de productos de la competencia en el espacio negociado de TQ.",
        "solucion": "Recuperar el espacio (Share of Shelf) y notificar al administrador.",
        "riesgo": "ALTO 🔴",
        "causa": "Prácticas agresivas de la competencia o descuido del espacio.",
        "responsable": "Supervisor Comercial",
        "sla": "24 Horas"
    },
    "Producto Mal Ubicado": {
        "numeral": "8.5.1 Control de la producción y prestación del servicio",
        "hallazgo": "Productos de una categoría en otra (ej. pañales en farmacia).",
        "solucion": "Reubicación inmediata a la zona y bloque correspondiente.",
        "riesgo": "MEDIO 🟡",
        "causa": "Desorden en el punto o reubicación por parte del cliente.",
        "responsable": "Mercaderista",
        "sla": "Inmediato"
    },
    "Promoción No Aplicada": {
        "numeral": "8.2.1 Comunicación con el cliente",
        "hallazgo": "La promoción (ej. pague 2 lleve 3) no está armada o señalizada.",
        "solucion": "Armar la dinámica, colocar el POP promocional y verificar en caja.",
        "riesgo": "ALTO 🔴",
        "causa": "Falla en la comunicación de la actividad promocional al PDV.",
        "responsable": "Trade Marketing / Comercial",
        "sla": "24 Horas"
    },
    "Suciedad Estantería": {
        "numeral": "7.1.3 Infraestructura",
        "hallazgo": "Falta de aseo en el entrepaño donde se ubica el producto.",
        "solucion": "Limpieza profunda del módulo, góndola y productos.",
        "riesgo": "BAJO 🟢",
        "causa": "Falta de rutina de mantenimiento y aseo.",
        "responsable": "Mercaderista / Auxiliar PDV",
        "sla": "Inmediato"
    },
    "Falla Rotación (FIFO)": {
        "numeral": "8.5.4 Preservación",
        "hallazgo": "Producto nuevo puesto adelante y el viejo atrás.",
        "solucion": "Reorganizar el inventario poniendo fechas próximas al frente.",
        "riesgo": "MEDIO 🟡",
        "causa": "Surtido rápido sin revisar fechas de caducidad.",
        "responsable": "Mercaderista",
        "sla": "Inmediato"
    },
    "Error Inventario": {
        "numeral": "8.5.1 Control de la producción y prestación del servicio",
        "hallazgo": "Sistema indica existencia pero físicamente hay cero.",
        "solucion": "Solicitar ajuste o conteo cíclico al inventarista del PDV.",
        "riesgo": "ALTO 🔴",
        "causa": "Robo, merma no reportada o error de facturación.",
        "responsable": "Administrador PDV / Auditor",
        "sla": "72 Horas"
    },
    "Mala Atención": {
        "numeral": "7.2 Competencia",
        "hallazgo": "Queja directa del consumidor sobre el servicio o asesoría en punto.",
        "solucion": "Retroalimentación al dependiente y refuerzo en capacitaciones TQ.",
        "riesgo": "ALTO 🔴",
        "causa": "Falta de empatía o conocimiento técnico del vendedor.",
        "responsable": "Entrenamiento / Supervisor",
        "sla": "1 Semana"
    }
}

# ================================
# SEGURIDAD (LOGIN)
# ================================
def hash_pass(p):
    return hashlib.sha256(p.strip().encode()).hexdigest()

def check_password():
    if not st.session_state.get("password_correct", False):
        st.title("🔐 Acceso Empresarial TQ")
        with st.container():
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.button("Ingresar Sistema de Auditoría"):
                usuarios_db = {
                    "equipotq": {"pass": hash_pass("tqcalidad2024"), "role": "Equipo Auditor"}
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
# FUNCION EXPORTAR EXCEL
# ================================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Auditoría TQ')
    processed_data = output.getvalue()
    return processed_data

# ================================
# PDF EJECUTIVO MEJORADO (CON CORRECCIÓN UNICODE)
# ================================
def limpiar_texto(t):
    """Limpia caracteres no compatibles con latin-1 para evitar UnicodeEncodeError"""
    if not isinstance(t, str): return str(t)
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N", "🔴": "(ALTO)", "🟡": "(MEDIO)", "🟢": "(BAJO)"
    }
    for char, rep in replacements.items():
        t = t.replace(char, rep)
    return t

def generar_pdf(df, nps, avg, usuario):
    if not PDF_OK: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(190, 15, limpiar_texto("TECNOQUIMICAS S.A - REPORTE EJECUTIVO DE CALIDAD"), ln=True, align="C")
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, limpiar_texto(f"Auditor Responsable: {usuario} | Fecha de Emision: {date.today()}"), ln=True, align="C")
    pdf.ln(10)
    
    # KPIs
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "1. RESUMEN ESTRATEGICO (KPIs)", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(95, 10, f"Net Promoter Score (NPS): {nps:.1f}%")
    pdf.cell(95, 10, limpiar_texto(f"Indice de Satisfaccion: {avg:.1f}%"), ln=True)
    pdf.ln(5)

    # Auditoria
    fallas = df[df["Motivo"] != "Ninguna"] if "Motivo" in df.columns else pd.DataFrame()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "2. ANALISIS DE NO CONFORMIDADES ISO 9001", ln=True)
    
    if not fallas.empty:
        pdf.set_font("Arial", "", 9)
        for _, r in fallas.iterrows():
            info = MATRIZ_ISO.get(r['Motivo'], {})
            txt = (f"ID: {r['id']} | CIUDAD: {limpiar_texto(r['Ciudad'])} | RIESGO: {limpiar_texto(info.get('riesgo',''))}\n"
                   f"NUMERAL: {limpiar_texto(info.get('numeral',''))}\n"
                   f"ACCION: {limpiar_texto(info.get('solucion',''))}\n"
                   f"RESPONSABLE: {limpiar_texto(info.get('responsable',''))} | SLA: {info.get('sla','')}\n")
            pdf.multi_cell(0, 5, txt)
            pdf.ln(3)
            
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "3. CONCLUSION EJECUTIVA", ln=True)
    pdf.set_font("Arial", "I", 10)
    conclusion = "Operacion estable" if nps > 50 else "Se requiere intervencion inmediata en procesos de calidad."
    pdf.multi_cell(0, 8, limpiar_texto(f"Basado en los datos analizados: {conclusion}"))
    
    # En fpdf2, .output() ya devuelve un bytearray, solo lo pasamos a bytes para Streamlit
    return bytes(pdf.output())

# ================================
# SIDEBAR (GESTIÓN Y REGISTRO)
# ================================
st.sidebar.title("🏢 Auditoría de Calidad TQ")
st.sidebar.markdown(f"**Usuario:** `{st.session_state.usuario}`")
st.sidebar.markdown(f"**Rol:** `{st.session_state.rol}`")
st.sidebar.markdown("---")

# Diccionario maestro para asignación automática Ciudad -> Zona
MAPEO_CIUDAD_ZONA = {
    "Leticia": "Llanos/Amazonía", "Medellín": "Antioquia", "Arauca": "Llanos/Amazonía",
    "Barranquilla": "Costa Norte", "Cartagena": "Costa Norte", "Tunja": "Centro (Bogotá/Boyacá)",
    "Manizales": "Eje Cafetero", "Florencia": "Llanos/Amazonía", "Yopal": "Llanos/Amazonía",
    "Popayán": "Valle y Cauca", "Valledupar": "Costa Norte", "Quibdó": "Antioquia",
    "Montería": "Costa Norte", "Bogotá": "Centro (Bogotá/Boyacá)", "Inírida": "Llanos/Amazonía",
    "San José del Guaviare": "Llanos/Amazonía", "Neiva": "Sur (Huila/Nariño)", "Riohacha": "Costa Norte",
    "Santa Marta": "Costa Norte", "Villavicencio": "Llanos/Amazonía", "Pasto": "Sur (Huila/Nariño)",
    "Cúcuta": "Santanderes", "Mocoa": "Sur (Huila/Nariño)", "Armenia": "Eje Cafetero",
    "Pereira": "Eje Cafetero", "San Andrés": "Costa Norte", "Bucaramanga": "Santanderes",
    "Sincelejo": "Costa Norte", "Ibagué": "Centro (Bogotá/Boyacá)", "Cali": "Valle y Cauca",
    "Mitú": "Llanos/Amazonía", "Puerto Carreño": "Llanos/Amazonía", "Soacha": "Centro (Bogotá/Boyacá)",
    "Bello": "Antioquia", "Soledad": "Costa Norte", "Buenaventura": "Valle y Cauca",
    "Palmira": "Valle y Cauca", "Tuluá": "Valle y Cauca", "Ipiales": "Sur (Huila/Nariño)",
    "Barrancabermeja": "Santanderes"
}

CIUDADES = sorted(list(MAPEO_CIUDAD_ZONA.keys()))
ZONAS = ["Antioquia", "Valle y Cauca", "Centro (Bogotá/Boyacá)", "Costa Norte", "Santanderes", "Eje Cafetero", "Sur (Huila/Nariño)", "Llanos/Amazonía"]

with st.sidebar.form("form"):
    st.subheader("📝 Captura de Datos")
    nombre = st.text_input("Punto / Cliente")
    contacto = st.text_input("Contacto")
    ciudad = st.selectbox("Ciudad", CIUDADES)
    canal = st.selectbox("Canal", ["Ventas","Digital","Farma","Institucional"])
    sat = st.slider("Satisfacción (%)", 0, 100, 80)
    pqrs = st.number_input("Reclamos", 0, 100, 0)
    
    motivo = st.selectbox("Motivo No Conformidad", [
        "Ninguna", "Producto Vencido", "Empaque Dañado", "Agotado en Góndola", 
        "Agotado en PDV", "Precio Incorrecto", "Falta Marcación Precio", 
        "Exhibición Deficiente", "Material POP Ausente", "Invasión Competencia",
        "Producto Mal Ubicado", "Promoción No Aplicada", "Suciedad Estantería",
        "Falla Rotación (FIFO)", "Error Inventario", "Mala Atención"
    ])
    
    obs = st.text_area("Observaciones Técnicas")

    if st.form_submit_button("💾 Guardar en Base de Datos"):
        zona_automatica = MAPEO_CIUDAD_ZONA[ciudad] 
        conn = sqlite3.connect(DB)
        conn.execute("INSERT INTO auditoria VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
                     (str(date.today()), nombre, contacto, ciudad, zona_automatica, canal, sat, pqrs, motivo, obs))
        conn.commit(); conn.close()
        st.cache_data.clear(); st.success(f"✅ Registro almacenado en {zona_automatica}"); st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🗑️ Zona de Peligro")

if st.sidebar.button("🗑️ Borrar Último"):
    st.sidebar.warning("¿Está seguro? Esta acción es irreversible.")
    if st.sidebar.button("Confirmar Borrado Último"):
        conn = sqlite3.connect(DB)
        conn.execute("DELETE FROM auditoria WHERE id = (SELECT MAX(id) FROM auditoria)")
        conn.commit(); conn.close()
        st.cache_data.clear(); st.success("Registro eliminado"); st.rerun()

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.clear(); st.rerun()

# ================================
# DASHBOARD EJECUTIVO
# ================================
st.title("🏢 Sistema de Auditoría de Calidad TQ")
st.markdown("---")

df = load_data()

with st.container():
    f1, f2 = st.columns(2)
    zona_sel = f1.multiselect("📍 Zona Operativa", ZONAS, default=ZONAS)
    can_sel = f2.multiselect("📦 Canal de Distribución", ["Ventas","Digital","Farma","Institucional"], default=["Ventas","Digital","Farma","Institucional"])

df_f = df[(df["Region"].isin(zona_sel)) & (df["Canal"].isin(can_sel))] if not df.empty else pd.DataFrame()

nps, avg_sat = 0, 0

if not df_f.empty:
    prom = len(df_f[df_f["Satisfaccion"]>=90])
    detr = len(df_f[df_f["Satisfaccion"]<70])
    nps = ((prom-detr)/len(df_f))*100
    avg_sat = df_f["Satisfaccion"].mean()
    total_pqrs = int(df_f["Reclamos"].sum())
    # === MEJORA: CÁLCULO DE CUMPLIMIENTO ISO ===
    cumplimiento_iso = (len(df_f[df_f["Motivo"] == "Ninguna"]) / len(df_f)) * 100

    if nps < 50: st.error(f"🔴 **ALERTA CRÍTICA NPS:** El índice actual ({nps:.1f}%) está por debajo del umbral corporativo.")
    if avg_sat < 70: st.warning(f"🟡 **ALERTA SATISFACCIÓN:** La media de satisfacción ({avg_sat:.1f}%) requiere atención inmediata.")
    if total_pqrs > 10: st.error(f"🚨 **RIESGO OPERATIVO:** Alto volumen de reclamos detectado ({total_pqrs} PQRS).")

    st.markdown("### 📈 Indicadores Clave de Gestión")
    # === MEJORA: AÑADIDA COLUMNA 5 PARA CUMPLIMIENTO ISO ===
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Loyalty NPS", f"{nps:.1f}%", delta=f"{nps-50:.1f}% vs Goal")
    k2.metric("Customer Sat", f"{avg_sat:.1f}%")
    k3.metric("Total Reclamos", total_pqrs)
    k4.metric("Tasa de Falla", f"{(total_pqrs/len(df_f)):.2f}")
    k5.metric("Cumplimiento ISO", f"{cumplimiento_iso:.1f}%")

    st.markdown("---")
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        fig = px.bar(
            df_f.groupby("Region")["Satisfaccion"].mean().reset_index().sort_values("Satisfaccion", ascending=False),
            x="Region", y="Satisfaccion", color="Satisfaccion",
            color_continuous_scale="RdYlGn", text_auto=".1f",
            title="🎯 Ranking de Desempeño por Zona"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.markdown("#### 🚦 Semáforo de Calidad")
        for z in zona_sel:
            df_zona = df_f[df_f["Region"]==z]
            if not df_zona.empty:
                sat_z = df_zona["Satisfaccion"].mean()
                ciudades = ", ".join(df_zona["Ciudad"].unique())
                if sat_z >= 85: st.success(f"🟢 {z} ({ciudades}): {sat_z:.1f}%")
                elif sat_z >= 70: st.warning(f"🟡 {z} ({ciudades}): {sat_z:.1f}%")
                else: st.error(f"🔴 {z} ({ciudades}): {sat_z:.1f}%")

    # === MEJORA: GRÁFICA DE TENDENCIA AÑADIDA DEBAJO ===
    st.markdown("---")
    st.markdown("#### 📉 Evolución de Satisfacción en el Tiempo")
    df_trend = df_f.groupby("Fecha")["Satisfaccion"].mean().reset_index()
    fig_line = px.line(df_trend, x="Fecha", y="Satisfaccion", markers=True, title="Tendencia Histórica de Satisfacción")
    st.plotly_chart(fig_line, use_container_width=True)

else:
    st.info("💡 Bienvenido. No hay datos en el filtro actual. Por favor, registre hallazgos en el panel lateral.")

# ================================
# TABS PROFESIONALES
# ================================
st.markdown("---")
tab1, tab2 = st.tabs(["🛠️ Gestión de Datos e Histórico","📑 Auditoría ISO 9001 PRO"])

with tab1:
    st.subheader("⚙️ Panel de Control de Datos")
    if not df.empty:
        with st.expander("🗑️ Herramientas de Eliminación"):
            col_del1, col_del2 = st.columns([1,3])
            
            ids_disponibles = df["id"].tolist() if not df.empty else []
            id_borrar = col_del1.selectbox("ID del Registro", options=ids_disponibles)
            
            if col_del2.button("⚠️ ELIMINAR REGISTRO POR ID"):
                if ids_disponibles:
                    conn = sqlite3.connect(DB)
                    conn.execute(f"DELETE FROM auditoria WHERE id = {id_borrar}")
                    conn.commit(); conn.close()
                    st.cache_data.clear()
                    st.success(f"Registro {id_borrar} eliminado permanentemente.")
                    st.rerun()

        st.markdown("#### Tabla Maestra de Auditoría")
        edit = st.data_editor(df, use_container_width=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Sincronizar Cambios"):
                conn = sqlite3.connect(DB)
                for _,r in edit.iterrows():
                    conn.execute("""UPDATE auditoria SET Fecha=?,Nombre=?,Contacto=?,Ciudad=?,Region=?,Canal=?,Satisfaccion=?,Reclamos=?,Motivo=?,Observaciones=? WHERE id=?""",
                                (str(r["Fecha"]),r["Nombre"],r["Contacto"],r["Ciudad"],r["Region"],r["Canal"],r["Satisfaccion"],r["Reclamos"],r["Motivo"],r["Observaciones"],r["id"]))
                conn.commit(); conn.close()
                st.success("✅ Base de Datos Sincronizada"); st.rerun()
        
        with col_btn2:
            excel_data = to_excel(df)
            st.download_button(
                label="📥 Descargar Histórico en Excel",
                data=excel_data,
                file_name=f"Auditoria_TQ_Completa_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.write("Esperando datos para mostrar historial...")

with tab2:
   st.subheader("📑 Auditoría ISO 9001:2015 - Inteligencia de Riesgo")
   
   if PDF_OK:
       try:
           pdf_file = generar_pdf(df_f, nps, avg_sat, st.session_state.usuario)
           st.download_button("📥 Descargar Reporte Ejecutivo PDF", pdf_file, f"TQ_Executive_Report_{date.today()}.pdf")
       except Exception as e:
           st.error(f"Error al generar PDF: {e}")

   if not df_f.empty:
       st.markdown("---")
       fallas = df_f[df_f["Motivo"]!="Ninguna"]
       if not fallas.empty:
           top_falla = fallas["Motivo"].value_counts().idxmax()
           st.error(f"📌 **HALLAZGO CRÍTICO:** La falla más recurrente es **{top_falla}**.")
           
           # === MEJORA: INSIGHTS AUTOMÁTICOS AÑADIDOS ===
           if top_falla == "Producto Vencido":
               st.error("🚨 Riesgo sanitario y legal ALTO. Se requiere retiro de lote inmediato.")
           elif top_falla == "Precio Incorrecto":
               st.warning("⚠️ Riesgo de Peticiones y Quejas (PQRS). Actualizar flejes urgente en el PDV.")
           elif top_falla == "Agotado en PDV" or top_falla == "Agotado en Góndola":
               st.warning("📉 Riesgo de pérdida de ventas. Revisar inventarios y cadena de suministro.")
           else:
               st.info(f"💡 Sugerencia Ejecutiva: Planificar una capacitación rápida enfocada en evitar: {top_falla}.")

           for f, c in fallas["Motivo"].value_counts().items():
               info = MATRIZ_ISO.get(f, {})
               with st.expander(f"📌 {f.upper()} | {c} Incidentes | Riesgo: {info.get('riesgo')}"):
                   c_iso1, c_iso2 = st.columns(2)
                   with c_iso1:
                       st.markdown(f"**🔍 Causa Raíz Sugerida:**\n{info.get('causa')}")
                       st.markdown(f"**⚖️ Numeral ISO:**\n{info.get('numeral')}")
                   with c_iso2:
                        st.markdown(f"**👤 Responsable:**\n{info.get('responsable')}")
                        st.markdown(f"**⏱️ SLA de Solución:**\n{info.get('sla')}")
                   st.info(f"**🎯 Acción Correctiva Proyectada:**\n{info.get('solucion')}")
       else:
           st.success("✅ **CUMPLIMIENTO TOTAL:** La operación cumple con el 100% de los estándares ISO en el filtro seleccionado.")

st.caption(f"Auditoría de Calidad TQ | © {date.today().year} Tecnoquímicas S.A. | Auditoría Senior")
