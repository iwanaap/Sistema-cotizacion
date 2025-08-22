from flask import Blueprint, jsonify, request, render_template
import sqlite3
from datetime import datetime
import os

tasks_bp = Blueprint('tasks', __name__)
TASKS_DB = 'tasks.db'

@tasks_bp.route('/tasks')
def tasks_view():
    """Vista principal de tareas"""
    return render_template('tasks.html')

def init_db():
    if not os.path.exists(TASKS_DB):
        conn = sqlite3.connect(TASKS_DB)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                due_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(TASKS_DB)
    conn.row_factory = sqlite3.Row
    return conn

@tasks_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(task) for task in tasks])

@tasks_bp.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data.get('title'):
        return jsonify({'error': 'El título es requerido'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (title, description, priority, status, due_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data.get('title'),
        data.get('description', ''),
        data.get('priority', 'medium'),
        data.get('status', 'pending'),
        data.get('due_date')
    ))
    conn.commit()
    task_id = cursor.lastrowid
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()
    return jsonify(dict(task)), 201

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if task is None:
        conn.close()
        return jsonify({'error': 'Tarea no encontrada'}), 404
    updates = []
    values = []
    valid_fields = ['title', 'description', 'priority', 'status', 'due_date']
    for field in valid_fields:
        if field in data:
            updates.append(f"{field} = ?")
            values.append(data[field])
    if updates:
        values.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
    updated_task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()
    return jsonify(dict(updated_task))

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if task is None:
        conn.close()
        return jsonify({'error': 'Tarea no encontrada'}), 404
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Tarea eliminada correctamente'})
