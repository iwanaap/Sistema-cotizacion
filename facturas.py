from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
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
    # Obtener y validar el término de búsqueda
    search_query = request.args.get('search', '').strip().lower()
    print(f"\nTérmino de búsqueda: '{search_query}'")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Obtener todas las facturas primero
        cursor.execute("SELECT * FROM facturas ORDER BY id DESC")
        facturas = cursor.fetchall()

        if search_query:
            # Filtrar las facturas basado en el término de búsqueda
            facturas_filtradas = []
            today = datetime.now().date()
            
            for factura in facturas:
                # Convertir valores a string para búsqueda
                valores_busqueda = [
                    str(factura[5]),  # numero_factura
                    str(factura[1]),  # rut_receptor
                    str(factura[2]),  # receptor
                    str(factura[3]),  # tipo_documento
                    str(factura[4]),  # condiciones_pago
                    str(factura[8]),  # estado_pago
                    str(factura[9]),  # numero_cotizacion
                    str(factura[10])  # numero_oc
                ]

                # Calcular fecha de vencimiento si aplica
                es_vencida = False
                dias_restantes = None
                if factura[4] == "30 días" and factura[6]:  # condiciones_pago y fecha
                    fecha_factura = datetime.strptime(factura[6], '%Y-%m-%d').date()
                    fecha_vencimiento = fecha_factura + timedelta(days=30)
                    es_vencida = fecha_vencimiento < today
                    dias_restantes = (fecha_vencimiento - today).days

                # Agregar términos relacionados con vencimiento
                if es_vencida and "vencid" in search_query:
                    facturas_filtradas.append(factura)
                    continue
                
                if not es_vencida and "vigente" in search_query:
                    facturas_filtradas.append(factura)
                    continue

                if "prox" in search_query and dias_restantes is not None and 0 <= dias_restantes <= 5:
                    facturas_filtradas.append(factura)
                    continue

                # Búsqueda normal en los campos
                if any(search_query in valor.lower() for valor in valores_busqueda if valor):
                    facturas_filtradas.append(factura)

            facturas = facturas_filtradas

    except Exception as e:
        print(f"\nERROR en la consulta: {str(e)}")
        facturas = []
    finally:
        conn.close()
    
    return render_template('facturas.html', 
                         facturas=facturas,
                         search_query=search_query,
                         today=datetime.now().date(),
                         timedelta=timedelta,
                         abs=abs)

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

        observaciones = request.form.get('observaciones', '')
        
        cursor.execute('''
            UPDATE facturas 
            SET rut_receptor=?, receptor=?, tipo_documento=?, condiciones_pago=?,
                numero_factura=?, fecha=?, monto_total=?, estado_pago=?,
                numero_cotizacion=?, numero_oc=?, observaciones=?
            WHERE id=?
        ''', (rut_receptor, receptor, tipo_documento, condiciones_pago,
              numero_factura_nuevo, fecha, monto_total, estado_pago,
              numero_cotizacion, numero_oc, observaciones, factura[0]))
        
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
        
        # Ya no validamos el formato del número de factura
        if not numero_factura:
            return "Error: El número de factura no puede estar vacío", 400
            
        fecha = request.form['fecha']
        monto_total = float(request.form['monto_total'])
        estado_pago = request.form['estado_pago']
        numero_cotizacion = request.form.get('numero_cotizacion', '')
        numero_oc = request.form.get('numero_oc', '')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Validar que la cotización existe si se proporciona
        if numero_cotizacion:
            cursor.execute('SELECT numero_cotizacion FROM cotizaciones WHERE numero_cotizacion = ?', (numero_cotizacion,))
            if not cursor.fetchone():
                conn.close()
                return "Error: La cotización especificada no existe", 400
                
        # Validar que la orden de compra existe si se proporciona
        if numero_oc:
            cursor.execute('SELECT numero_oc FROM ordenes_compra WHERE numero_oc = ?', (numero_oc,))
            if not cursor.fetchone():
                conn.close()
                return "Error: La orden de compra especificada no existe", 400
        
        # Insertar nueva factura
        observaciones = request.form.get('observaciones', '')
        
        cursor.execute('''
            INSERT INTO facturas (
                rut_receptor, receptor, tipo_documento, condiciones_pago,
                numero_factura, fecha, monto_total, estado_pago,
                numero_cotizacion, numero_oc, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (rut_receptor, receptor, tipo_documento, condiciones_pago,
              numero_factura, fecha, monto_total, estado_pago,
              numero_cotizacion, numero_oc, observaciones))
        
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
