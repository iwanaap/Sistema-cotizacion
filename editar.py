from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
import json

editar_bp = Blueprint('editar', __name__, url_prefix='/editar')

DB_FILE = "cotizaciones.db"

# Ruta para editar una cotización por ID (mantener por compatibilidad)
@editar_bp.route('/<string:id>', methods=['GET', 'POST'])
def editar_cotizacion(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Obtener el número de cotización y redirigir a la nueva ruta
    cursor.execute("SELECT numero_cotizacion FROM cotizaciones WHERE id = ?", (id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return redirect(url_for('editar.editar_cotizacion_por_numero', numero_cotizacion=result[0]))
    return "Cotización no encontrada", 404

# Nueva ruta para editar por número de cotización
@editar_bp.route('/cotizacion/<string:numero_cotizacion>', methods=['GET', 'POST'])
def editar_cotizacion_por_numero(numero_cotizacion):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Primero obtener el ID usando el número de cotización como texto
    cursor.execute("SELECT id FROM cotizaciones WHERE numero_cotizacion = ?", (str(numero_cotizacion),))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return "Cotización no encontrada", 404
    
    id = result[0]  # El ID sigue siendo un entero en la base de datos
    
    if request.method == 'POST':
        try:
            # Capturar los datos editados del formulario
            numero_cotizacion = request.form['numeroCotizacion']
            empresa = request.form['empresa']
            rut = request.form['rut']
            contacto = request.form['contacto']
            telefono = request.form['telefono']
            email = request.form['email']
            fechaCotizacion = request.form['fechaCotizacion']
            productos_json = request.form['productos']
            
            # Capturar los campos adicionales del formulario
            plazo_entrega = request.form.get('plazo_entrega', '')
            forma_pago = request.form.get('forma_pago', '')
            creador = request.form.get('creador', '')

            # Validar que los campos requeridos no estén vacíos
            if not plazo_entrega or not forma_pago or not creador:
                conn.close()
                return "Error: Los campos Plazo de Entrega, Forma de Pago y Creador son requeridos", 400

            # Convertir la cadena JSON de productos en lista para calcular el total
            try:
                productos = json.loads(productos_json)
            except Exception:
                productos = []

            monto_total = sum(float(p.get("cantidad", 0)) * float(p.get("precio", 0)) for p in productos)

            # Crear el JSON con toda la información
            datos_cotizacion = {
                "numero_cotizacion": numero_cotizacion,
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

            # Actualizar la cotización con todos los campos
            cursor.execute("""
                UPDATE cotizaciones
                SET empresa = ?, rut = ?, contacto = ?, telefono = ?, email = ?, fecha = ?, 
                    productos = ?, monto = ?, creador = ?, datos_cotizacion = ?, numero_cotizacion = ?
                WHERE id = ?
            """, (empresa, rut, contacto, telefono, email, fechaCotizacion, 
                  productos_json, monto_total, creador, datos_json, numero_cotizacion, id))
            
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return f"Error al guardar los cambios: {str(e)}", 400

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
