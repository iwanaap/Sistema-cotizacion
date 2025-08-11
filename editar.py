from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
import json
import os
from werkzeug.utils import secure_filename
import uuid

editar_bp = Blueprint('editar', __name__, url_prefix='/editar')

DB_FILE = "cotizaciones.db"
UPLOAD_FOLDER = os.path.join('static', 'img', 'productos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(file):
    if file and file.filename and allowed_file(file.filename):
        try:
            # Asegurarse de que el directorio existe
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            # Generar nombre único para el archivo
            filename = secure_filename(file.filename)
            unique_filename = f"{str(uuid.uuid4())}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            # Guardar el archivo
            file.save(file_path)
            
            # Verificar que el archivo se guardó correctamente
            if os.path.exists(file_path):
                print(f"Imagen guardada exitosamente: {file_path}")
                return unique_filename
            else:
                print(f"Error: El archivo no se guardó correctamente en {file_path}")
                return None
        except Exception as e:
            print(f"Error al guardar la imagen: {str(e)}")
            return None
    return None

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
            
            # Procesar las imágenes de los productos
            try:
                productos = json.loads(productos_json)
                print("\nProcesando productos y sus imágenes...")
                for i, producto in enumerate(productos):
                    print(f"\nProcesando producto {i}: {producto.get('producto', 'Sin nombre')}")
                    
                    # 1. Verificar si hay una nueva imagen en el request
                    file_key = f'producto_imagen_{i}'
                    nueva_imagen = request.files.get(file_key)
                    
                    # 2. Obtener la imagen actual del producto
                    imagen_actual = producto.get('imagen', '')
                    print(f"Imagen actual: {imagen_actual}")
                    
                    # 3. Procesar según el caso
                    if nueva_imagen and nueva_imagen.filename:
                        print(f"Procesando nueva imagen: {nueva_imagen.filename}")
                        # Guardar nueva imagen
                        filename = save_product_image(nueva_imagen)
                        if filename:
                            print(f"Nueva imagen guardada como: {filename}")
                            # Eliminar imagen anterior si existe
                            if imagen_actual:
                                old_path = os.path.join(UPLOAD_FOLDER, imagen_actual)
                                if os.path.exists(old_path):
                                    try:
                                        os.remove(old_path)
                                        print(f"Imagen anterior eliminada: {imagen_actual}")
                                    except Exception as e:
                                        print(f"Error al eliminar imagen anterior: {str(e)}")
                            producto['imagen'] = filename
                        else:
                            print("Error al guardar la nueva imagen")
                            producto['imagen'] = imagen_actual  # Mantener la imagen actual si falla
                    
                    elif f'imagen_eliminada_{i}' in request.form:
                        print(f"Eliminando imagen actual: {imagen_actual}")
                        if imagen_actual:
                            old_path = os.path.join(UPLOAD_FOLDER, imagen_actual)
                            if os.path.exists(old_path):
                                try:
                                    os.remove(old_path)
                                    print("Imagen eliminada del sistema de archivos")
                                except Exception as e:
                                    print(f"Error al eliminar archivo: {str(e)}")
                        producto['imagen'] = ''
                    
                    elif not imagen_actual:
                        print("No hay imagen para este producto")
                        producto['imagen'] = ''
                    
                    else:
                        print(f"Manteniendo imagen actual: {imagen_actual}")
                        # Verificar que la imagen existe
                        img_path = os.path.join(UPLOAD_FOLDER, imagen_actual)
                        if not os.path.exists(img_path):
                            print(f"Advertencia: Archivo de imagen no encontrado en: {img_path}")
                            producto['imagen'] = ''
                
                print("\nProcesamiento de imágenes completado")
                productos_json = json.dumps(productos)
            except Exception as e:
                print(f"Error procesando imágenes: {str(e)}")
            
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
