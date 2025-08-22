// tasks.js

document.addEventListener('DOMContentLoaded', function() {
    loadTasks();
    setupDragAndDrop();

    // Evento para limpiar el formulario cuando se abre el modal
    document.getElementById('addTaskModal').addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        // Solo limpiar si es una nueva tarea (no edición)
        if (!button || !button.closest('.task-card')) {
            document.getElementById('taskForm').reset();
            document.getElementById('taskId').value = '';
            document.getElementById('taskTitle').value = '';
            document.getElementById('taskDescription').value = '';
            document.getElementById('taskPriority').value = 'medium';
            document.getElementById('taskDueDate').value = '';
        }
    });

    document.getElementById('saveTask').addEventListener('click', saveTask);
});

function loadTasks() {
    fetch('/api/tasks')
        .then(res => res.json())
        .then(tasks => {
            ['pending', 'in-progress', 'completed'].forEach(status => {
                const container = document.querySelector(`#${status} .tasks-container`);
                container.innerHTML = '';
                tasks.filter(t => t.status === status).forEach(task => {
                    container.appendChild(createTaskCard(task));
                });
            });
        });
}

function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = 'task-card';
    card.dataset.id = task.id;
    card.dataset.status = task.status;
    
    // Iconos según el estado
    const statusIcon = {
        'pending': '⭕',
        'in-progress': '⏳',
        'completed': '✅'
    };

    card.innerHTML = `
        <div class="d-flex justify-content-between align-items-start mb-2">
            <strong>${task.title}</strong>
            <span>${statusIcon[task.status] || ''}</span>
        </div>
        <p class="mb-2">${task.description || ''}</p>
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <span class="badge bg-${priorityColor(task.priority)}">${task.priority}</span>
                ${task.due_date ? `<small class="ms-2 text-muted">Vence: ${task.due_date}</small>` : ''}
            </div>
            <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">🗑️</button>
        </div>
    `;
    
    card.onclick = function(e) {
        if (e.target.tagName === 'BUTTON') return;
        editTask(task);
    };
    
    return card;
}

function priorityColor(priority) {
    if (priority === 'high') return 'danger';
    if (priority === 'medium') return 'warning';
    return 'secondary';
}

function saveTask() {
    const id = document.getElementById('taskId').value;
    const title = document.getElementById('taskTitle').value;
    const description = document.getElementById('taskDescription').value;
    const priority = document.getElementById('taskPriority').value;
    const due_date = document.getElementById('taskDueDate').value;
    const data = { 
        title, 
        description, 
        priority, 
        due_date,
        status: id ? undefined : 'pending' // Solo asignar estado 'pending' para nuevas tareas
    };
    let method = 'POST', url = '/api/tasks';
    if (id) {
        method = 'PUT';
        url = `/api/tasks/${id}`;
    }
    fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(() => {
        document.getElementById('taskForm').reset();
        var modal = bootstrap.Modal.getInstance(document.getElementById('addTaskModal'));
        modal.hide();
        loadTasks();
    });
}

function editTask(task) {
    // Asegurarnos de que tenemos todos los datos de la tarea
    fetch(`/api/tasks/${task.id}`)
        .then(res => res.json())
        .then(taskData => {
            document.getElementById('taskId').value = taskData.id;
            document.getElementById('taskTitle').value = taskData.title || '';
            document.getElementById('taskDescription').value = taskData.description || '';
            document.getElementById('taskPriority').value = taskData.priority || 'medium';
            document.getElementById('taskDueDate').value = taskData.due_date || '';
            
            var modal = new bootstrap.Modal(document.getElementById('addTaskModal'));
            modal.show();
        });
}

function deleteTask(id) {
    if (!confirm('¿Eliminar esta tarea?')) return;
    fetch(`/api/tasks/${id}`, { method: 'DELETE' })
        .then(() => loadTasks());
}

function setupDragAndDrop() {
    // Asegurarnos de que dragula esté disponible
    if (typeof dragula === 'undefined') {
        console.error('Dragula no está cargado');
        return;
    }

    // Obtener los contenedores
    const drake = dragula({
        isContainer: function (el) {
            return el.classList.contains('tasks-container');
        },
        moves: function (el, container, handle) {
            return !handle.classList.contains('btn'); // No arrastrar si se hace clic en botones
        },
        accepts: function (el, target, source, sibling) {
            return true; // Aceptar en cualquier contenedor
        },
        invalid: function (el, target) {
            return false; // No hay elementos inválidos
        }
    });

    // Manejar el evento drop
    drake.on('drop', function(el, target, source) {
        console.log('Drop event triggered');
        console.log('Element:', el);
        console.log('Target:', target);
        console.log('Source:', source);
        
        if (!target) {
            console.error('No target container found');
            return;
        }
        
        const taskId = el.dataset.id;
        // Buscamos el contenedor padre más cercano que tenga el ID de estado
        const columnElement = target.closest('.task-column');
        if (!columnElement) {
            console.error('No se encontró el contenedor de columna');
            return;
        }
        
        const newStatus = columnElement.id;
        console.log('New status:', newStatus);
        
        if (!taskId || !newStatus) {
            console.error('Error: No se pudo determinar el ID de la tarea o el nuevo estado');
            console.log('TaskId:', taskId);
            console.log('NewStatus:', newStatus);
            loadTasks();
            return;
        }

        // Actualizar el estado en el servidor
        fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al actualizar la tarea');
            }
            return response.json();
        })
        .then(() => {
            // Recargar todas las tareas para asegurar la sincronización
            loadTasks();
        })
        .catch(error => {
            console.error('Error:', error);
            loadTasks(); // Recargar para revertir cualquier cambio visual
        });
    });

    // Agregar clases durante el arrastre
    drake.on('drag', function(el) {
        el.classList.add('is-dragging');
    });

    drake.on('dragend', function(el) {
        el.classList.remove('is-dragging');
    });
}
