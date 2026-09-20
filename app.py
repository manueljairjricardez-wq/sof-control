# 1. Instalar dependencias para gráficos y PDF
# pip install -q gradio pandas matplotlib reportlab

import os
import json
import datetime
import base64
import pandas as pd
import matplotlib.pyplot as plt
import gradio as gr
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

INVENTORY_FILE = "sof_inventory.json"
ASSIGNMENTS_FILE = "sof_assignments.json"
LOGO_FILE = "logoSOF.jpeg"

DEFAULT_INVENTORY = {
    "Overol 2XS (2XCH - Talla 32)": {"stock": 10, "reemplazo_dias": 180, "minimo": 3},
    "Overol XS (XCH - Talla 34)": {"stock": 15, "reemplazo_dias": 180, "minimo": 3},
    "Overol S (CH - Talla 36)": {"stock": 20, "reemplazo_dias": 180, "minimo": 5},
    "Overol M (Mediana - Talla 38)": {"stock": 25, "reemplazo_dias": 180, "minimo": 5},
    "Overol L (Grande - Talla 40)": {"stock": 25, "reemplazo_dias": 180, "minimo": 5},
    "Overol XL (Extra Grande - Talla 42)": {"stock": 15, "reemplazo_dias": 180, "minimo": 3},
    "Overol 2XL/3XL/4XL (Tallas 44-50+)": {"stock": 10, "reemplazo_dias": 180, "minimo": 2},
    "Botas Industriales - Num 23": {"stock": 5, "reemplazo_dias": 180, "minimo": 2},
    "Botas Industriales - Num 24": {"stock": 8, "reemplazo_dias": 180, "minimo": 2},
    "Botas Industriales - Num 25": {"stock": 12, "reemplazo_dias": 180, "minimo": 3},
    "Botas Industriales - Num 26": {"stock": 15, "reemplazo_dias": 180, "minimo": 3},
    "Botas Industriales - Num 27": {"stock": 20, "reemplazo_dias": 180, "minimo": 5},
    "Botas Industriales - Num 28": {"stock": 15, "reemplazo_dias": 180, "minimo": 3},
    "Botas Industriales - Num 29": {"stock": 8, "reemplazo_dias": 180, "minimo": 2},
    "Botas Industriales - Num 30": {"stock": 5, "reemplazo_dias": 180, "minimo": 2},
    "Guantes de Cabritilla/Lona": {"stock": 120, "reemplazo_dias": 30, "minimo": 30},
    "Guantes de Soldador": {"stock": 40, "reemplazo_dias": 60, "minimo": 10},
    "Guantes de Eléctricista": {"stock": 25, "reemplazo_dias": 90, "minimo": 10},
    "Tapones Auditivos (pares)": {"stock": 300, "reemplazo_dias": 15, "minimo": 50},
    "Cascos de Seguridad": {"stock": 35, "reemplazo_dias": 365, "minimo": 10},
    "Barbiquejos": {"stock": 60, "reemplazo_dias": 90, "minimo": 15},
    "Lentes de Seguridad": {"stock": 150, "reemplazo_dias": 90, "minimo": 30},
    "Conos de Señalización": {"stock": 30, "reemplazo_dias": 365, "minimo": 10},
    "Cinta de Perimetraje (rollos)": {"stock": 50, "reemplazo_dias": 60, "minimo": 10},
    "Hieleras Portátiles": {"stock": 10, "reemplazo_dias": 730, "minimo": 3}
}

def load_data():
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, "r") as f:
            inv = json.load(f)
        for k in ["Overoles", "Botas Industriales"]:
            if k in inv: del inv[k]
        for k, default_vals in DEFAULT_INVENTORY.items():
            if k not in inv:
                inv[k] = default_vals
            else:
                if "minimo" not in inv[k]: inv[k]["minimo"] = default_vals.get("minimo", 10)
                if "reemplazo_dias" not in inv[k]: inv[k]["reemplazo_dias"] = default_vals.get("reemplazo_dias", 90)
    else:
        inv = DEFAULT_INVENTORY
        save_json(INVENTORY_FILE, inv)
        
    if os.path.exists(ASSIGNMENTS_FILE):
        with open(ASSIGNMENTS_FILE, "r") as f:
            asg = json.load(f)
    else:
        asg = []
    return inv, asg

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def obtener_dataframe_inventario():
    inv, _ = load_data()
    return pd.DataFrame([{
        "EPP / Talla": k, 
        "Stock": int(v.get("stock", 0)), 
        "Mínimo Sugerido": int(v.get("minimo", 10)), 
        "Estado": "⚠️ BAJO STOCK" if int(v.get("stock", 0)) <= int(v.get("minimo", 10)) else "Óptimo",
        "Reemplazo (Días)": int(v.get("reemplazo_dias", 90))
    } for k, v in inv.items()])

def obtener_directorio_trabajadores():
    _, asg = load_data()
    if not asg:
        return pd.DataFrame(columns=["Trabajador / Responsable", "Total Artículos Asignados", "Última Fecha"])
    df_asg = pd.DataFrame(asg)
    grouped = df_asg.groupby("Receptor").agg(
        Total_Asignaciones=("Cantidad", "sum"),
        Ultima_Fecha=("Fecha", "max")
    ).reset_index()
    grouped.columns = ["Trabajador / Responsable", "Total Artículos Asignados", "Última Fecha"]
    return grouped

def login(usuario, password):
    usuario = usuario.strip().lower()
    if usuario == "yadira" and password == "sof2026":
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), "🔓 Sesión iniciada como: KARELY YADIRA (Editor / Administrador)"
    elif usuario == "invitado" and password == "invitado123":
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), "👁️ Sesión iniciada como: INVITADO (Solo Lectura / Auditoría)"
    else:
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), "❌ Usuario o contraseña incorrectos."

def logout():
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), "Sesión cerrada."

def guardar_cambios_tabla(df_modificado):
    try:
        inv, _ = load_data()
        for _, row in df_modificado.iterrows():
            epp_nombre = row["EPP / Talla"]
            nuevo_stock = int(row["Stock"])
            if epp_nombre in inv:
                inv[epp_nombre]["stock"] = nuevo_stock
        save_json(INVENTORY_FILE, inv)
        return "¡Inventario actualizado correctamente!", obtener_dataframe_inventario()
    except Exception as e:
        return f"Error: {str(e)}", obtener_dataframe_inventario()

def registrar_asignacion(tipo_destino, receptor, item, cantidad):
    inv, asg = load_data()
    cantidad = int(cantidad)
    
    if not receptor.strip():
        return "Error: Ingrese el nombre del trabajador.", obtener_dataframe_inventario(), obtener_directorio_trabajadores()
    if item not in inv:
        return "El EPP seleccionado no existe.", obtener_dataframe_inventario(), obtener_directorio_trabajadores()
    if inv[item]["stock"] < cantidad:
        return f"¡Stock insuficiente! Quedan {inv[item]['stock']} unidades.", obtener_dataframe_inventario(), obtener_directorio_trabajadores()
    
    inv[item]["stock"] -= cantidad
    save_json(INVENTORY_FILE, inv)
    
    dias = inv[item]["reemplazo_dias"]
    f_asg = datetime.date.today()
    f_rem = f_asg + datetime.timedelta(days=dias)
    
    asg.append({
        "Destino": tipo_destino,
        "Receptor": receptor.strip().upper(),
        "Item": item,
        "Cantidad": cantidad,
        "Fecha": str(f_asg),
        "Reemplazo": str(f_rem)
    })
    save_json(ASSIGNMENTS_FILE, asg)
    
    mensaje = f"Asignación registrada para '{receptor.strip().upper()}'. Stock restante: {inv[item]['stock']}"
    return mensaje, obtener_dataframe_inventario(), obtener_directorio_trabajadores()

def consultar_trabajador(nombre_busqueda):
    _, asg = load_data()
    if not nombre_busqueda.strip():
        return pd.DataFrame(columns=["Receptor", "Item", "Cantidad", "Fecha de Asignación", "Fecha Próxima de Reemplazo"]), "Ingrese un nombre."
    nombre_busqueda = nombre_busqueda.strip().lower()
    filtradas = [a for a in asg if nombre_busqueda in a["Receptor"].lower()]
    if not filtradas:
        return pd.DataFrame(columns=["Receptor", "Item", "Cantidad", "Fecha de Asignación", "Fecha Próxima de Reemplazo"]), "No se encontraron registros."
    df = pd.DataFrame([{
        "Receptor": x["Receptor"], "Item": x["Item"], "Cantidad": x["Cantidad"],
        "Fecha de Asignación": x["Fecha"], "Fecha Próxima de Reemplazo": x["Reemplazo"]
    } for x in filtradas])
    return df, f"Se encontraron {len(filtradas)} registros."

def guardar_cambios_trabajador(nombre_busqueda, df_modificado_trabajador):
    try:
        _, asg = load_data()
        nombre_busqueda = nombre_busqueda.strip().upper()
        asg_restantes = [a for a in asg if a["Receptor"].upper() != nombre_busqueda]
        for _, row in df_modificado_trabajador.iterrows():
            asg_restantes.append({
                "Destino": "Trabajador Individual",
                "Receptor": str(row["Receptor"]).strip().upper(),
                "Item": str(row["Item"]),
                "Cantidad": int(row["Stock"] if "Stock" in row else row["Cantidad"]),
                "Fecha": str(row["Fecha de Asignación"]),
                "Reemplazo": str(row["Fecha Próxima de Reemplazo"])
            })
        save_json(ASSIGNMENTS_FILE, asg_restantes)
        return "¡Asignaciones actualizadas!", obtener_directorio_trabajadores()
    except Exception as e:
        return f"Error: {str(e)}", obtener_directorio_trabajadores()

def dar_de_baja_trabajador(nombre_busqueda):
    if not nombre_busqueda.strip():
        return "Ingrese el nombre.", pd.DataFrame(columns=["Receptor", "Item", "Cantidad", "Fecha de Asignación", "Fecha Próxima de Reemplazo"]), obtener_directorio_trabajadores()
    _, asg = load_data()
    nombre_target = nombre_busqueda.strip().upper()
    asg_filtradas = [a for a in asg if a["Receptor"].upper() != nombre_target]
    if len(asg_filtradas) == len(asg):
        return f"No se encontró a '{nombre_target}'.", pd.DataFrame(columns=["Receptor", "Item", "Cantidad", "Fecha de Asignación", "Fecha Próxima de Reemplazo"]), obtener_directorio_trabajadores()
    save_json(ASSIGNMENTS_FILE, asg_filtradas)
    return f"¡Trabajador '{nombre_target}' dado de baja!", pd.DataFrame(columns=["Receptor", "Item", "Cantidad", "Fecha de Asignación", "Fecha Próxima de Reemplazo"]), obtener_directorio_trabajadores()

def restaurar_desde_backup(file_obj):
    if file_obj is None: return "Cargue un archivo JSON.", obtener_dataframe_inventario(), obtener_directorio_trabajadores()
    try:
        file_path = file_obj.name if hasattr(file_obj, 'name') else file_obj
        with open(file_path, "r", encoding="utf-8") as f: data = json.load(f)
        if "inventario" in data and "asignaciones" in data:
            save_json(INVENTORY_FILE, data["inventario"])
            save_json(ASSIGNMENTS_FILE, data["asignaciones"])
            return "¡Respaldo restaurado!", obtener_dataframe_inventario(), obtener_directorio_trabajadores()
        else: return "Estructura inválida.", obtener_dataframe_inventario(), obtener_directorio_trabajadores()
    except Exception as e: return f"Error: {str(e)}", obtener_dataframe_inventario(), obtener_directorio_trabajadores()

def generar_pdf_reporte(periodo):
    inv, asg = load_data()
    hoy = datetime.date.today()
    f_inicio = hoy if periodo == "Diario" else (hoy - datetime.timedelta(days=7) if periodo == "Semanal" else hoy - datetime.timedelta(days=30))
    asg_filtradas = [a for a in asg if datetime.datetime.strptime(a["Fecha"], "%Y-%m-%d").date() >= f_inicio]

    plt.figure(figsize=(10, 4))
    plt.barh(list(inv.keys()), [v["stock"] for v in inv.values()], color='#1f77b4')
    plt.xlabel('Stock')
    plt.title(f'Inventario EPP - Reporte {periodo}')
    plt.tight_layout()
    chart_path = "inventory_chart.png"
    plt.savefig(chart_path)
    plt.close()

    pdf_path = f"Reporte_SOF_Control_{periodo}.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    if os.path.exists(LOGO_FILE):
        story.append(RLImage(LOGO_FILE, width=60, height=60))
        story.append(Spacer(1, 6))

    story.append(Paragraph("<b>SHARE OIL FLUIDS CONTROL (SOF CONTROL)</b>", styles['Title']))
    story.append(Paragraph(f"<b>Reporte {periodo}</b>", styles['Heading2']))
    story.append(Paragraph(f"Fecha: {hoy}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Alertas de Stock Bajo:</b>", styles['Heading3']))
    alertas = [f"- <b>{k}</b> tiene {v['stock']} pzs (Mínimo: {v['minimo']})" for k, v in inv.items() if v["stock"] <= v["minimo"]]
    for al in (alertas if alertas else ["Niveles óptimos"]): story.append(Paragraph(al, styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(RLImage(chart_path, width=450, height=180))
    story.append(Spacer(1, 12))

    data_tabla = [["Receptor", "Item", "Cantidad", "Fecha"]]
    for a in asg_filtradas: data_tabla.append([a["Receptor"], a["Item"], str(a["Cantidad"]), a["Fecha"]])
    t = Table(data_tabla, colWidths=[150, 150, 60, 100])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>KARELY YADIRA GARCIA OLAN</b><br/><b>COORDINADOR DE SEGURIDAD</b>", styles['Normal']))
    doc.build(story)

    backup_path = "Backup_SOF_Control.json"
    save_json(backup_path, {"inventario": inv, "asignaciones": asg})
    return pdf_path, backup_path, obtener_dataframe_inventario()

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode('utf-8')
    return ""

img_b64 = get_image_base64(LOGO_FILE)
logo_html = f'<img src="data:image/jpeg;base64,{img_b64}" width="65" style="vertical-align:middle; display:inline-block; margin-right:15px; border-radius:8px;">' if img_b64 else ''

with gr.Blocks() as app:
    gr.Markdown(f'<div style="display: flex; align-items: center; padding: 10px 0;">{logo_html}<div><h1 style="margin: 0; font-size: 26px; font-weight: bold;">SHARE OIL FLUIDS CONTROL (SOF CONTROL)</h1><h3 style="margin: 0; color: #a0a0a0; font-size: 14px;">Departamento de Seguridad Industrial - Control de EPP</h3></div></div>')

    with gr.Row() as login_row:
        with gr.Column(scale=1):
            gr.Markdown("### 🔐 Inicio de Sesión al Sistema")
            user_input = gr.Textbox(label="Usuario (yadira / invitado)")
            pass_input = gr.Textbox(label="Contraseña", type="password")
            btn_login = gr.Button("Iniciar Sesión", variant="primary")
            login_msg = gr.Textbox(label="Estado", interactive=False)

    with gr.Column(visible=False) as main_app_col:
        with gr.Row():
            lbl_sesion = gr.Markdown("Sesión Activa")
            btn_logout = gr.Button("🚪 Cerrar Sesión", variant="stop")

        with gr.Tabs():
            with gr.TabItem("📦 Inventario y Tallas"):
                gr.Markdown("### Inventario General Desglosado por Tallas y Artículos")
                tabla_inventario = gr.Dataframe(value=obtener_dataframe_inventario(), interactive=True, label="Inventario de EPP")
                btn_guardar_tabla = gr.Button("💾 Guardar Cambios de Inventario", variant="primary")
                out_msg = gr.Textbox(label="Estado del Sistema")
                btn_guardar_tabla.click(guardar_cambios_tabla, inputs=[tabla_inventario], outputs=[out_msg, tabla_inventario])
                
            with gr.TabItem("👷 Asignaciones y Consultas"):
                with gr.Row():
                    with gr.Column(scale=1) as col_asignar:
                        gr.Markdown("### 1. Registrar Nueva Asignación")
                        tipo_dest = gr.Radio(choices=["Trabajador Individual", "Colaborador / Lote de Área"], label="Tipo de Destino", value="Trabajador Individual")
                        receptor_input = gr.Textbox(label="Nombre del Trabajador")
                        item_asg = gr.Dropdown(choices=list(DEFAULT_INVENTORY.keys()), label="Elemento / Talla EPP", value="Overol M (Mediana - Talla 38)")
                        cant_asg = gr.Number(label="Cantidad Asignada", value=1)
                        btn_registrar = gr.Button("Registrar Asignación y Descontar", variant="primary")
                        out_reg = gr.Textbox(label="Resultado de Asignación")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📋 Directorio General de Personal")
                        tabla_directorio = gr.Dataframe(value=obtener_directorio_trabajadores(), label="Trabajadores con EPP Activo", interactive=False)
                
                gr.Markdown("---")
                gr.Markdown("### 2. Consultar Historial, Editar o Dar de Baja")
                with gr.Row():
                    input_buscar = gr.Textbox(label="Escriba el Nombre del Trabajador")
                    btn_buscar = gr.Button("🔍 Buscar Asignaciones", variant="secondary")
                
                tabla_resultado_busqueda = gr.Dataframe(label="EPP Asignado", interactive=True)
                
                with gr.Row() as row_botones_edicion:
                    btn_guardar_cambios_emp = gr.Button("💾 Guardar Cambios", variant="primary")
                    btn_dar_baja = gr.Button("🗑️ Dar de Baja / Eliminar Todo (Finiquito)", variant="stop")
                    
                out_busqueda_msg = gr.Textbox(label="Estado de Operación")
                
                btn_registrar.click(registrar_asignacion, inputs=[tipo_dest, receptor_input, item_asg, cant_asg], outputs=[out_reg, tabla_inventario, tabla_directorio])
                btn_buscar.click(consultar_trabajador, inputs=[input_buscar], outputs=[tabla_resultado_busqueda, out_busqueda_msg])
                btn_guardar_cambios_emp.click(guardar_cambios_trabajador, inputs=[input_buscar, tabla_resultado_busqueda], outputs=[out_busqueda_msg, tabla_directorio])
                btn_dar_baja.click(dar_de_baja_trabajador, inputs=[input_buscar], outputs=[out_busqueda_msg, tabla_resultado_busqueda, tabla_directorio])
                
            with gr.TabItem("📊 Reportes, Gráficas y PDF"):
                gr.Markdown("### Generación de Reportes Profesionales en PDF con Gráficas")
                periodo_radio = gr.Radio(choices=["Diario", "Semanal", "Mensual"], label="Periodo", value="Semanal")
                btn_generar_pdf = gr.Button("📄 Generar Reporte PDF", variant="primary")
                
                with gr.Row():
                    file_pdf = gr.File(label="Descargar Reporte PDF")
                    file_backup = gr.File(label="Descargar Respaldo JSON")
                    
                with gr.Column() as col_restaurar:
                    gr.Markdown("---")
                    gr.Markdown("### 🔄 Restaurar Sistema desde Respaldo")
                    file_input_backup = gr.File(label="Subir Backup_SOF_Control.json")
                    btn_restaurar = gr.Button("📂 Restaurar Datos", variant="secondary")
                    btn_restaurar.click(restaurar_desde_backup, inputs=[file_input_backup], outputs=[out_restaurar_msg := gr.Textbox(label="Estado"), tabla_rep_inv := gr.Dataframe(value=obtener_dataframe_inventario()), tabla_directorio])
                    
                tabla_rep_inv = gr.Dataframe(value=obtener_dataframe_inventario(), label="Estado Actual del Inventario")
                btn_generar_pdf.click(generar_pdf_reporte, inputs=[periodo_radio], outputs=[file_pdf, file_backup, tabla_rep_inv])

    btn_login.click(login, inputs=[user_input, pass_input], outputs=[login_row, main_app_col, lbl_sesion, login_msg]).then(
        lambda m: (gr.update(interactive="INVITADO" not in m), gr.update(visible="INVITADO" not in m), gr.update(visible="INVITADO" not in m), gr.update(visible="INVITADO" not in m), gr.update(visible="INVITADO" not in m)),
        inputs=[login_msg], outputs=[tabla_inventario, btn_guardar_tabla, col_asignar, row_botones_edicion, col_restaurar]
    )
    btn_logout.click(logout, outputs=[login_row, main_app_col, login_msg])

app.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)), share=False)
