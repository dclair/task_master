document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. LÓGICA DE LOS MODALES (creación y edición) ---
    const taskModal = document.getElementById('taskModal');
    

    // --- 2. LÓGICA DE DRAG & DROP (Lo nuevo) ---
    const containers = document.querySelectorAll('.tasks-container');
    if (taskModal) {
        taskModal.addEventListener('show.bs.modal', function (event) {
            const trigger = event.relatedTarget; // El elemento que abrió el modal
            const form = document.getElementById('taskForm');
            const modalTitle = taskModal.querySelector('.modal-title') || taskModal.querySelector('h5');
            const submitBtn = form.querySelector('button[type="submit"]');

            if (trigger.classList.contains('task-card')) {
                // --- MODO EDICIÓN ---
                modalTitle.textContent = 'Editar Tarea';
                submitBtn.textContent = 'Guardar Cambios';
                submitBtn.className = 'btn btn-primary rounded-pill w-100 fw-bold';

                // Rellenar campos con seguridad (si existen)
                const fields = ['title', 'description', 'priority', 'due_date'];
                const dataMap = {
                    'title': 'data-title',
                    'description': 'data-desc',
                    'priority': 'data-prio',
                    'due_date': 'data-date'
                };

                fields.forEach(field => {
                    const input = form.querySelector(`[name="${field}"]`);
                    if (input) {
                        input.value = trigger.getAttribute(dataMap[field]) || '';
                    }
                });

                const taskId = trigger.getAttribute('data-taskid');
                form.action = `/boards/task/${taskId}/edit/`;

            } else {
                // --- MODO CREACIÓN ---
                modalTitle.textContent = 'Nueva Tarea';
                submitBtn.textContent = 'Crear Tarea';
                submitBtn.className = 'btn btn-success rounded-pill w-100 fw-bold';
                
                form.reset();
                const listId = trigger.getAttribute('data-listid');
                form.action = `/boards/list/${listId}/add_task/`;
            }
        });
    }
    containers.forEach(container => {
        new Sortable(container, {
            group: 'kanban', // Permite mover entre diferentes columnas
            animation: 150,
            ghostClass: 'sortable-ghost', // La clase para el hueco
            dragClass: 'sortable-drag',   // La clase para la tarjeta que vuela
            handle: '.task-card',        // Toda la tarjeta sirve para arrastrar
            
            onEnd: function (evt) {
                const taskId = evt.item.getAttribute('data-taskid');
                // Buscamos el ID de la lista destino a través del botón "Añadir tarea"
                const newListId = evt.to.closest('.kanban-column').querySelector('.open-task-modal').getAttribute('data-listid');

                // Enviamos el cambio a Django vía AJAX
                fetch('/boards/task/move/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        task_id: taskId,
                        new_list_id: newListId
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        alert('Error al mover la tarea. Inténtalo de nuevo.');
                        location.reload(); // Recarga si algo falla para evitar desajustes visuales
                    }
                });
            }
        });
    });
});

// --- 3. FUNCIÓN AUXILIAR PARA EL TOKEN CSRF ---
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}