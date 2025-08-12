import sqlite3

DB_FILE = "cotizaciones.db"

def add_observaciones_column():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(facturas)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'observaciones' not in columns:
            # Agregar la columna si no existe
            cursor.execute('ALTER TABLE facturas ADD COLUMN observaciones TEXT')
            print("Columna 'observaciones' agregada exitosamente")
        else:
            print("La columna 'observaciones' ya existe")
            
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_observaciones_column()
