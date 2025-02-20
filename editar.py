from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
import json

editar_bp = Blueprint('editar', __name__, url_prefix='/editar')

DB_FILE = "cotizaciones.db"

# Ruta para editar una cotización
@editar_bp.route('/<int:id>', methods=['GET', 'POST'])
def editar_cotizacion(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if request.method == 'POST':
        # Capturar los datos editados del formulario
        empresa = request.form['empresa']
        rut = request.form['rut']
        contacto = request.form['contacto']
        telefono = request.form['telefono']
        email = request.form['email']
        fechaCotizacion = request.form['fechaCotizacion']
        productos_json = request.form['productos']
        creador = request.form['creador']
        plazo_entrega = request.form['plazo_entrega']
        forma_pago = request.form['forma_pago']

        # Convertir la cadena JSON de productos en lista para calcular el total
        try:
            productos = json.loads(productos_json)
        except Exception:
            productos = []

        monto_total = sum(float(p.get("cantidad", 0)) * float(p.get("precio", 0)) for p in productos)

        # Crear el JSON con toda la información, incluidos los nuevos campos
        datos_cotizacion = {
            "numero_cotizacion": request.form.get("numeroCotizacion"),
            "empresa": empresa,
            "rut": rut,
            "contacto": contacto,
            "telefono": telefono,
            "email": email,
            "fecha": fechaCotizacion,
            "productos": productos,
            "monto": monto_total,
            "creador": creador,
            "plazo_entrega": plazo_entrega,
            "forma_pago": forma_pago
        }
        datos_json = json.dumps(datos_cotizacion)

        # Actualizamos la cotización en la base de datos (actualizando también el JSON completo)
        cursor.execute("""
            UPDATE cotizaciones
            SET empresa = ?, rut = ?, contacto = ?, telefono = ?, email = ?, fecha = ?, productos = ?, monto = ?, creador = ?, datos_cotizacion = ?
            WHERE id = ?
        """, (empresa, rut, contacto, telefono, email, fechaCotizacion, productos_json, monto_total, creador, datos_json, id))

        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    # Bloque GET: Obtener la cotización actual de la base de datos
    cursor.execute("SELECT * FROM cotizaciones WHERE id = ?", (id,))
    cotizacion = cursor.fetchone()
    conn.close()

    if not cotizacion:
        return "Cotización no encontrada", 404

    # Convertir la cadena JSON de productos en lista para mostrar en la tabla de edición
    productos = json.loads(cotizacion[7]) if cotizacion[7] else []

    # Extraer los datos extra de la columna datos_cotizacion (índice 11)
    datos_extra = {}
    if cotizacion[11]:
        try:
            datos_extra = json.loads(cotizacion[11])
        except Exception:
            datos_extra = {}

    # Construir el diccionario para pasar al template, incorporando los nuevos campos
    cotizacion_dict = {
        "id": cotizacion[0],
        "numero_cotizacion": cotizacion[10],
        "empresa": cotizacion[1],
        "rut": cotizacion[2],
        "contacto": cotizacion[3],
        "telefono": cotizacion[4],
        "email": cotizacion[5],
        "fecha": cotizacion[6],
        "productos": productos,
        "creador": cotizacion[9],
        "plazo_entrega": datos_extra.get("plazo_entrega", ""),
        "forma_pago": datos_extra.get("forma_pago", "")
    }


    return render_template("editar.html", cotizacion=cotizacion_dict, format_money=format_money)

def format_money(value):
    """Formatea valores numéricos en formato de moneda chilena: $1.000.000"""
    try:
        value = float(value)
        return "${:,.0f}".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return "$0"
