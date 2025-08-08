from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import sqlite3
from contextlib import closing  # Importar closing para manejo seguro de conexiones

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')

DB_FILE = "cotizaciones.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=20)  # Aumentar timeout
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

# Inicializar la tabla de clientes si no existe
def init_db_clientes():
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            empresa TEXT,
            rut TEXT,
            telefono TEXT,
            email TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db_clientes()

# Página para gestionar clientes
@clientes_bp.route('/', methods=['GET', 'POST'])
def gestionar_clientes():
    if request.method == 'POST':
        # Usar with para manejar la conexión de forma segura
        with closing(get_db_connection()) as conn:
            cursor = conn.cursor()
            try:
                nombre = request.form['nombre']
                empresa = request.form['empresa']
                rut = request.form['rut']
                telefono = request.form['telefono']
                email = request.form['email']
                
                cursor.execute("""
                    INSERT INTO clientes (nombre, empresa, rut, telefono, email)
                    VALUES (?, ?, ?, ?, ?)
                """, (nombre, empresa, rut, telefono, email))
                conn.commit()
            except sqlite3.OperationalError as e:
                print(f"Error SQLite: {e}")
    
    # Obtener clientes usando una conexión separada
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes ORDER BY nombre ASC")
        clientes = cursor.fetchall()
    
    return render_template("clientes.html", clientes=clientes)

@clientes_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_cliente(id):
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
        conn.commit()
    return redirect(url_for('clientes.gestionar_clientes'))

# Ruta para buscar y autocompletar clientes
@clientes_bp.route('/buscar_cliente', methods=['GET'])
def buscar_cliente():
    nombre = request.args.get('nombre', '').strip()
    
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        
        # Buscar cliente por nombre (búsqueda parcial, case-insensitive)
        cursor.execute("""
            SELECT nombre, rut, empresa, telefono, email
            FROM clientes 
            WHERE LOWER(nombre) LIKE LOWER(?) 
            ORDER BY nombre
            LIMIT 10
        """, (f"%{nombre}%",))
        
        clientes = []
        for row in cursor.fetchall():
            clientes.append({
                "nombre": row[0],
                "rut": row[1],
                "empresa": row[2],
                "telefono": row[3],
                "email": row[4]
            })
    
    return jsonify(clientes)
