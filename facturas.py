from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import json

facturas_bp = Blueprint('facturas', __name__)

DB_FILE = "cotizaciones.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Crear tabla de facturas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut_receptor TEXT,
            receptor TEXT,
            tipo_documento TEXT,
            condiciones_pago TEXT,
            numero_factura TEXT UNIQUE,
            fecha TEXT,
            monto_total REAL,
            estado_pago TEXT,
            numero_cotizacion TEXT,
            numero_oc TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@facturas_bp.route('/facturas', methods=['GET', 'POST'])
def lista_facturas():
    search_query = request.form.get('search', '').lower().strip()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM facturas ORDER BY id DESC")
    facturas = cursor.fetchall()
    conn.close()

    # Filtrar resultados si hay búsqueda
    if search_query:
        facturas_filtradas = []
        for factura in facturas:
            # Convertir todos los valores a string para búsqueda
            valores = [str(valor).lower() for valor in factura if valor is not None]
            if any(search_query in valor for valor in valores):
                facturas_filtradas.append(factura)
        facturas = facturas_filtradas
    
    return render_template('facturas.html', facturas=facturas, search_query=search_query)

@facturas_bp.route('/facturas/editar/<string:numero_factura>', methods=['GET', 'POST'])
def editar_factura_por_numero(numero_factura):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Buscar la factura por número
    cursor.execute('SELECT * FROM facturas WHERE numero_factura = ?', (numero_factura,))
    factura = cursor.fetchone()
    
    if factura is None:
        conn.close()
        return render_template('crear_factura.html',
                           factura=None,
                           numero_factura_prellenado=numero_factura,
                           mensaje="No existe una factura con ese número. Puede crear una nueva.")
    
    if request.method == 'POST':
        rut_receptor = request.form['rut_receptor']
        receptor = request.form['receptor']
        tipo_documento = request.form['tipo_documento']
        condiciones_pago = request.form['condiciones_pago']
        numero_factura_nuevo = request.form['numero_factura']
        fecha = request.form['fecha']
        monto_total = float(request.form['monto_total'])
        estado_pago = request.form['estado_pago']
        numero_cotizacion = request.form.get('numero_cotizacion', '')
        numero_oc = request.form.get('numero_oc', '')
        
        # Si el número de factura cambió, verificar que el nuevo no exista
        if numero_factura_nuevo != numero_factura:
            cursor.execute('SELECT id FROM facturas WHERE numero_factura = ? AND id != ?', 
                         (numero_factura_nuevo, factura[0]))
            if cursor.fetchone() is not None:
                conn.close()
                return "Error: Ya existe una factura con ese número", 400

        cursor.execute('''
            UPDATE facturas 
            SET rut_receptor=?, receptor=?, tipo_documento=?, condiciones_pago=?,
                numero_factura=?, fecha=?, monto_total=?, estado_pago=?,
                numero_cotizacion=?, numero_oc=?
            WHERE id=?
        ''', (rut_receptor, receptor, tipo_documento, condiciones_pago,
              numero_factura_nuevo, fecha, monto_total, estado_pago,
              numero_cotizacion, numero_oc, factura[0]))
        
        # Actualizar cotización relacionada
        if numero_cotizacion:
            cursor.execute('''
                UPDATE cotizaciones 
                SET numero_factura=?, estado_pago=?
                WHERE numero_cotizacion=?
            ''', (numero_factura_nuevo, estado_pago, numero_cotizacion))
        
        # Actualizar orden de compra relacionada
        if numero_oc:
            cursor.execute('''
                UPDATE ordenes_compra 
                SET numero_factura=?, facturado=?, estado_pago=?
                WHERE numero_oc=?
            ''', (numero_factura_nuevo, True, estado_pago, numero_oc))
        
        conn.commit()
        conn.close()
        return redirect(url_for('facturas.lista_facturas'))
    
    return render_template('crear_factura.html', factura=factura, edit=True)

@facturas_bp.route('/facturas/eliminar/<string:numero_factura>')
def eliminar_factura_por_numero(numero_factura):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Obtener la factura antes de eliminarla
    cursor.execute('SELECT id, numero_cotizacion, numero_oc FROM facturas WHERE numero_factura=?', (numero_factura,))
    factura = cursor.fetchone()
    
    if factura:
        # Actualizar la cotización relacionada
        if factura[1]:  # numero_cotizacion
            cursor.execute('''
                UPDATE cotizaciones 
                SET numero_factura='' 
                WHERE numero_cotizacion=?
            ''', (factura[1],))
            
        # Actualizar la orden de compra relacionada
        if factura[2]:  # numero_oc
            cursor.execute('''
                UPDATE ordenes_compra 
                SET numero_factura='', facturado=0
                WHERE numero_oc=?
            ''', (factura[2],))
        
        # Eliminar la factura usando su ID
        cursor.execute('DELETE FROM facturas WHERE id=?', (factura[0],))
        conn.commit()
    
    conn.close()
    return redirect(url_for('facturas.lista_facturas'))

@facturas_bp.route('/facturas/nueva', methods=['GET', 'POST'])
def nueva_factura():
    if request.method == 'POST':
        rut_receptor = request.form['rut_receptor']
        receptor = request.form['receptor']
        tipo_documento = request.form['tipo_documento']
        condiciones_pago = request.form['condiciones_pago']
        numero_factura = request.form['numero_factura']
        
        # Validar que el número de factura solo contenga dígitos
        if not numero_factura.isdigit():
            return "Error: El número de factura debe contener solo números", 400
            
        fecha = request.form['fecha']
        monto_total = float(request.form['monto_total'])
        estado_pago = request.form['estado_pago']
        numero_cotizacion = request.form.get('numero_cotizacion', '')
        numero_oc = request.form.get('numero_oc', '')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Validar que la cotización existe si se proporciona un número
        if numero_cotizacion:
            cursor.execute('SELECT numero_cotizacion FROM cotizaciones WHERE numero_cotizacion = ?', (numero_cotizacion,))
            if not cursor.fetchone():
                conn.close()
                return "Error: La cotización especificada no existe", 400
                
        # Validar que la orden de compra existe si se proporciona un número
        if numero_oc:
            cursor.execute('SELECT numero_oc FROM ordenes_compra WHERE numero_oc = ?', (numero_oc,))
            if not cursor.fetchone():
                conn.close()
                return "Error: La orden de compra especificada no existe", 400
        
        # Insertar nueva factura
        cursor.execute('''
            INSERT INTO facturas (
                rut_receptor, receptor, tipo_documento, condiciones_pago,
                numero_factura, fecha, monto_total, estado_pago,
                numero_cotizacion, numero_oc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (rut_receptor, receptor, tipo_documento, condiciones_pago,
              numero_factura, fecha, monto_total, estado_pago,
              numero_cotizacion, numero_oc))
        
        # Actualizar la tabla de cotizaciones si hay número de cotización
        if numero_cotizacion:
            cursor.execute('''
                UPDATE cotizaciones 
                SET numero_factura = ?, estado_pago = ?
                WHERE numero_cotizacion = ?
            ''', (numero_factura, estado_pago, numero_cotizacion))
        
        # Actualizar la tabla de órdenes de compra si hay número de OC
        if numero_oc:
            cursor.execute('''
                UPDATE ordenes_compra 
                SET numero_factura = ?, facturado = ?, estado_pago = ?
                WHERE numero_oc = ?
            ''', (numero_factura, True, estado_pago, numero_oc))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('facturas.lista_facturas'))
    
    return render_template('crear_factura.html')
