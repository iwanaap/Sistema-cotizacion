from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
import sqlite3
from datetime import datetime
import json
import pdfkit
import os
from clientes import clientes_bp  # Importar el Blueprint de clientes
from editar import editar_bp  # Importar el Blueprint de edición
from ordenes_compra import ordenes_compra_bp  # Importar el Blueprint de órdenes de compra
from facturas import facturas_bp  # Importar el Blueprint de facturas

app = Flask(__name__)

# Registrar los Blueprints
app.register_blueprint(clientes_bp)
app.register_blueprint(editar_bp)
app.register_blueprint(ordenes_compra_bp)
app.register_blueprint(facturas_bp)

@app.route('/buscar_cotizaciones')
def buscar_cotizaciones():
    cliente = request.args.get('cliente', '')
    monto = request.args.get('monto', '')
    
    # Conectar a la base de datos
    conn = sqlite3.connect('cotizaciones.db')
    cursor = conn.cursor()
    
    # Construir la consulta base
    query = """
    SELECT id, numero_cotizacion, empresa, fecha, monto, 
           ROUND(monto * 1.19) as monto_con_iva 
    FROM cotizaciones 
    WHERE 1=1
    """
    params = []
    
    # Agregar filtros si se proporcionan
    if cliente:
        query += " AND empresa LIKE ?"
        params.append(f"%{cliente}%")
    
    if monto and monto.strip():
        try:
            monto_float = float(monto)
            margen = monto_float * 0.10  # 10% de margen
            query += " AND ROUND(monto * 1.19) BETWEEN ? AND ?"
            params.extend([monto_float - margen, monto_float + margen])
        except ValueError:
            pass
    
    # Ordenar por fecha descendente y limitar a 10 resultados
    query += " ORDER BY fecha DESC LIMIT 10"
    
    # Ejecutar la consulta
    cursor.execute(query, params)
    cotizaciones = cursor.fetchall()
    
    # Formatear los resultados
    resultados = []
    for cot in cotizaciones:
        resultados.append({
            'id': cot[0],
            'numero': cot[1],
            'empresa': cot[2],
            'fecha': cot[3],
            'monto_total': cot[5]  # Usamos el monto_con_iva calculado
        })
    
    conn.close()
    return jsonify(resultados)

# Archivo de la base de datos
DB_FILE = "cotizaciones.db"

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Modificar la tabla de cotizaciones para agregar los nuevos campos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT,
            rut TEXT,
            contacto TEXT,
            telefono TEXT,
            email TEXT,
            fecha TEXT,
            productos TEXT,
            monto REAL,
            creador TEXT,
            numero_cotizacion TEXT UNIQUE,
            datos_cotizacion TEXT,
            estado_cotizacion TEXT DEFAULT 'Pendiente',
            numero_oc TEXT,
            numero_factura TEXT,
            estado_pago TEXT DEFAULT 'Pendiente'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.form.get('search', '').lower().strip()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Siempre se traen todas las cotizaciones sin filtrar en la consulta SQL
    cursor.execute("SELECT * FROM cotizaciones ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    cotizaciones_list = []
    for row in rows:
        try:
            productos_list = json.loads(row[7]) if row[7] else []
        except Exception:
            productos_list = []

        # Calcular el total en Python
        neto = sum(float(p.get("cantidad", 0)) * float(p.get("precio", 0)) for p in productos_list)
        iva = neto * 0.19
        total = neto + iva

        # Formatear el total para que sea comparable con la búsqueda
        total_str = str(int(total))
        total_formatted = f"{int(total):,}".replace(",", ".")
        
        cotizacion_dict = {
            "id": row[0],
            "numero_cotizacion": row[10],
            "empresa": row[1],
            "rut": row[2],
            "contacto": row[3],
            "telefono": row[4],
            "email": row[5],
            "fecha": row[6],
            "productos": productos_list,
            "total": total,
            "total_str": total_str,
            "total_formatted": total_formatted,
            "creador": row[9],
            "estado_cotizacion": row[12],
            "numero_oc": row[13],
            "numero_factura": row[14],
            "estado_pago": row[15]
        }

        # Filtrar en Python, incluyendo también el monto total en distintos formatos
        if search_query:
            valores_comparables = [str(value).lower() for value in cotizacion_dict.values()]
            valores_comparables.append(total_str)
            valores_comparables.append(total_formatted)
            if any(search_query in value for value in valores_comparables):
                cotizaciones_list.append(cotizacion_dict)
        else:
            cotizaciones_list.append(cotizacion_dict)
    
    return render_template("index.html", cotizaciones=cotizaciones_list, search_query=search_query)

@app.route('/actualizar_estado_cotizacion', methods=['POST'])
def actualizar_estado_cotizacion():
    if request.method == 'POST':
        cotizacion_id = request.form.get('id')
        nuevo_estado = request.form.get('estado')
        
        if cotizacion_id and nuevo_estado:
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE cotizaciones 
                    SET estado_cotizacion = ? 
                    WHERE id = ?
                ''', (nuevo_estado, cotizacion_id))
                conn.commit()
                conn.close()
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Datos inválidos'})





@app.route('/pdfs/<int:id>')
def generar_pdf(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cotizaciones WHERE id = ?", (id,))
    cotizacion = cursor.fetchone()
    conn.close()

    if not cotizacion:
        return "Cotización no encontrada", 404

    try:
        productos = json.loads(cotizacion[7]) if cotizacion[7] else []
    except Exception:
        productos = []

    datos_extra = {}
    if cotizacion[11]:
        try:
            datos_extra = json.loads(cotizacion[11])
        except Exception:
            datos_extra = {}

    # Obtener la ruta absoluta de las imágenes
    img_logo_izquierdo = os.path.abspath("static/img/logo-empresa-1.png")
    img_logo_derecho = os.path.abspath("static/img/logo-empresa-2.png")

    # Asegurarse de que las imágenes existen
    if not os.path.exists(img_logo_izquierdo) or not os.path.exists(img_logo_derecho):
        return "Error: Las imágenes no se encontraron en la ruta especificada.", 404

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
        "plazo_entrega": datos_extra.get("plazo_entrega", ""),
        "forma_pago": datos_extra.get("forma_pago", ""),
        "img_logo_izquierdo": f"file://{img_logo_izquierdo}",
        "img_logo_derecho": f"file://{img_logo_derecho}"
    }

    # Renderizar el template a HTML
    rendered = render_template("pdf.html", cotizacion=cotizacion_dict)

    # Configurar la ruta de wkhtmltopdf
    config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')

    # Opciones para permitir acceso a archivos locales
    options = {'enable-local-file-access': ''}

    # Convertir el HTML a PDF usando pdfkit
    pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Cotización {cotizacion[10]}.pdf'
    return response


# Ruta para crear una cotización
@app.route('/crear', methods=['GET', 'POST'])
def crear():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Obtener la lista de clientes
    cursor.execute("SELECT nombre FROM clientes ORDER BY nombre ASC")
    clientes = [row[0] for row in cursor.fetchall()]

    # Definir la fecha actual como predeterminada
    default_date = datetime.now().strftime('%Y-%m-%d')

    # Obtener el último número de cotización y sumarle 1 (empezando en 5050)
    cursor.execute("SELECT numero_cotizacion FROM cotizaciones")
    filas = cursor.fetchall()
    max_num = 5049
    for fila in filas:
        try:
            num = int(fila[0])
            if num > max_num:
                max_num = num
        except ValueError:
            pass
    next_num = max_num + 1

    conn.close()

    if request.method == 'POST':
        # Capturar los datos del formulario
        empresa = request.form['empresa']
        rut = request.form['rut']
        contacto = request.form['contacto']
        telefono = request.form['telefono']
        email = request.form['email']
        fechaCotizacion = request.form.get('fechaCotizacion', default_date)
        numeroCotizacion = request.form.get('numeroCotizacion', str(next_num))
        creador = request.form['creador']
        plazo_entrega = request.form['plazo_entrega']
        forma_pago = request.form['forma_pago']

        # Capturar y procesar los productos
        try:
            productos = json.loads(request.form['productos'])  # Convertir JSON string a lista
        except Exception:
            productos = []

        # Calcular el monto total
        monto_total = sum(float(p.get("cantidad", 0)) * float(p.get("precio", 0)) for p in productos)

        # Guardar los datos en un JSON para mantener toda la información
        datos_cotizacion = {
            "numero_cotizacion": numeroCotizacion,
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

        # Guardar en la base de datos respetando el orden correcto de los campos
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cotizaciones (
                empresa, rut, contacto, telefono, email, fecha, productos, monto, creador, numero_cotizacion, datos_cotizacion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            empresa, rut, contacto, telefono, email, fechaCotizacion, json.dumps(productos),
            monto_total, creador, numeroCotizacion, datos_json
        ))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))

    return render_template("crear.html", clientes=clientes, default_date=default_date, next_num=next_num)


# Ruta para eliminar una cotización
@app.route('/eliminar/<int:id>', methods=['GET'])
def eliminar(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cotizaciones WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
