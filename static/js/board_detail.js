document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. LÓGICA DE LOS MODALES (Lo que ya tenías) ---
    const taskModal = document.getElementById('taskModal');
    if (taskModal) {
        taskModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const listId = button.getAttribute('data-listid');
            const form = taskModal.querySelector('#taskForm');
            // Ajustamos la ruta para que apunte a la lista correcta
            form.action = `/boards/list/${listId}/add_task/`;
        });
    }

    // --- 2. LÓGICA DE DRAG & DROP (Lo nuevo) ---
    const containers = document.querySelectorAll('.tasks-container');

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