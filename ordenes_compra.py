from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import json
import os

ordenes_compra_bp = Blueprint('ordenes_compra', __name__)

DB_FILE = "cotizaciones.db"
UPLOAD_FOLDER = os.path.join('static', 'pdfs', 'ordenes_compra')

# Crear el directorio para PDFs si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Crear tabla de órdenes de compra
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordenes_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_oc TEXT UNIQUE,
            cliente TEXT,
            fecha TEXT,
            contacto TEXT,
            monto_total REAL,
            facturado BOOLEAN,
            numero_factura TEXT,
            estado_pago TEXT,
            numero_cotizacion TEXT,
            pdf_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@ordenes_compra_bp.route('/ordenes_compra', methods=['GET', 'POST'])
def lista_ordenes():
    search_query = request.form.get('search', '').lower().strip()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM ordenes_compra ORDER BY id DESC")
    ordenes = cursor.fetchall()
    conn.close()

    # Filtrar resultados si hay búsqueda
    if search_query:
        ordenes_filtradas = []
        for orden in ordenes:
            # Convertir todos los valores a string para búsqueda
            valores = [str(valor).lower() for valor in orden if valor is not None]
            if any(search_query in valor for valor in valores):
                ordenes_filtradas.append(orden)
        ordenes = ordenes_filtradas
    
    return render_template('ordenes_compra.html', ordenes=ordenes, search_query=search_query)

@ordenes_compra_bp.route('/ordenes_compra/editar/<string:numero_oc>', methods=['GET', 'POST'])
def editar_orden_por_numero(numero_oc):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Buscar la orden por número
    cursor.execute('SELECT * FROM ordenes_compra WHERE numero_oc = ?', (numero_oc,))
    orden = cursor.fetchone()
    
    if orden is None:
        conn.close()
        return render_template('crear_orden_compra.html',
                           orden=None,
                           numero_oc_prellenado=numero_oc,
                           mensaje="No existe una orden de compra con ese número. Puede crear una nueva.")
    
    if request.method == 'POST':
        numero_oc_nuevo = request.form['numero_oc']
        cliente = request.form['cliente']
        fecha = request.form['fecha']
        contacto = request.form['contacto']
        monto_total = float(request.form['monto_total'])
        facturado = 'facturado' in request.form
        numero_factura = request.form.get('numero_factura', '')
        estado_pago = request.form['estado_pago']
        numero_cotizacion = request.form.get('numero_cotizacion', '')
        
        # Si el número de OC cambió, verificar que el nuevo no exista
        if numero_oc_nuevo != numero_oc:
            cursor.execute('SELECT id FROM ordenes_compra WHERE numero_oc = ? AND id != ?', 
                         (numero_oc_nuevo, orden[0]))
            if cursor.fetchone() is not None:
                conn.close()
                return "Error: Ya existe una orden de compra con ese número", 400
                
        # Manejo del archivo PDF
        pdf_file = request.files.get('pdf_documento')
        pdf_path = orden[10]  # Mantener el path actual si no hay nuevo archivo
        if pdf_file:
            # Si hay un PDF anterior, eliminarlo
            if pdf_path and os.path.exists(os.path.join('static', pdf_path)):
                os.remove(os.path.join('static', pdf_path))
            # Guardar el nuevo PDF
            filename = f"oc_{numero_oc_nuevo}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            pdf_file.save(save_path)
            pdf_path = os.path.join('pdfs', 'ordenes_compra', filename)
        
        cursor.execute('''
            UPDATE ordenes_compra 
            SET numero_oc=?, cliente=?, fecha=?, contacto=?, monto_total=?,
                facturado=?, numero_factura=?, estado_pago=?, numero_cotizacion=?, pdf_path=?
            WHERE id=?
        ''', (numero_oc_nuevo, cliente, fecha, contacto, monto_total,
              facturado, numero_factura, estado_pago, numero_cotizacion, pdf_path, orden[0]))
        
        if numero_cotizacion:
            cursor.execute('''
                UPDATE cotizaciones 
                SET numero_oc=?, estado_pago=?
                WHERE numero_cotizacion=?
            ''', (numero_oc_nuevo, estado_pago, numero_cotizacion))
        
        conn.commit()
        conn.close()
        return redirect(url_for('ordenes_compra.lista_ordenes'))
    
    return render_template('crear_orden_compra.html', orden=orden, edit=True)

@ordenes_compra_bp.route('/ordenes_compra/eliminar/<string:numero_oc>')
def eliminar_orden_por_numero(numero_oc):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Obtener la orden antes de eliminarla para actualizar la cotización
    cursor.execute('SELECT id, numero_cotizacion, pdf_path FROM ordenes_compra WHERE numero_oc=?', (numero_oc,))
    orden = cursor.fetchone()
    
    if orden:
        # Actualizar la cotización relacionada
        if orden[1]:  # numero_cotizacion
            cursor.execute('''
                UPDATE cotizaciones 
                SET numero_oc=NULL 
                WHERE numero_cotizacion=?
            ''', (orden[1],))
        
        # Eliminar el archivo PDF si existe
        if orden[2] and os.path.exists(orden[2]):
            os.remove(orden[2])
        
        # Eliminar la orden usando su ID
        cursor.execute('DELETE FROM ordenes_compra WHERE id=?', (orden[0],))
        conn.commit()
    
    conn.close()
    return redirect(url_for('ordenes_compra.lista_ordenes'))

@ordenes_compra_bp.route('/ordenes_compra/nueva', methods=['GET', 'POST'])
def nueva_orden():
    if request.method == 'POST':
        numero_oc = request.form['numero_oc']
        cliente = request.form['cliente']
        fecha = request.form['fecha']
        contacto = request.form['contacto']
        monto_total = float(request.form['monto_total'])
        facturado = 'facturado' in request.form
        numero_factura = request.form.get('numero_factura', '')
        estado_pago = request.form['estado_pago']
        numero_cotizacion = request.form.get('numero_cotizacion', '')
        
        # Manejo del archivo PDF
        pdf_file = request.files.get('pdf_documento')
        pdf_path = ''
        if pdf_file:
            # Guardar el archivo PDF
            filename = f"oc_{numero_oc}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf_path = os.path.join(UPLOAD_FOLDER, filename)
            pdf_file.save(pdf_path)
            # Convertir la ruta para almacenar en la base de datos
            pdf_path = os.path.join('pdfs', 'ordenes_compra', filename)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ordenes_compra (
                numero_oc, cliente, fecha, contacto, monto_total,
                facturado, numero_factura, estado_pago, numero_cotizacion, pdf_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (numero_oc, cliente, fecha, contacto, monto_total,
              facturado, numero_factura, estado_pago, numero_cotizacion, pdf_path))
        
        # Si hay número de cotización, actualizar la tabla de cotizaciones
        if numero_cotizacion:
            cursor.execute('''
                UPDATE cotizaciones 
                SET numero_oc = ?, estado_pago = ?
                WHERE numero_cotizacion = ?
            ''', (numero_oc, estado_pago, numero_cotizacion))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('ordenes_compra.lista_ordenes'))
    
    return render_template('crear_orden_compra.html')
