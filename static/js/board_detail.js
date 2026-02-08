document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. LÓGICA DE LOS MODALES (Creación y Edición) ---
    const taskModal = document.getElementById('taskModal');
    
    if (taskModal) {
        taskModal.addEventListener('show.bs.modal', function (event) {
            const trigger = event.relatedTarget;
            const form = document.getElementById('taskForm');
            const modalTitle = taskModal.querySelector('.modal-title') || taskModal.querySelector('h5');
            const submitBtn = form.querySelector('button[type="submit"]');

            // Limpiar checkboxes de etiquetas siempre al abrir
            form.querySelectorAll('[name="tags"]').forEach(cb => cb.checked = false);

            if (trigger.classList.contains('task-card')) {
                // MODO EDICIÓN
                modalTitle.textContent = 'Editar Tarea';
                submitBtn.textContent = 'Guardar Cambios';
                submitBtn.className = 'btn btn-primary rounded-pill w-100 fw-bold';

                const fields = ['title', 'description', 'priority', 'due_date'];
                const dataMap = {
                    'title': 'data-title', 
                    'description': 'data-desc', 
                    'priority': 'data-prio', 
                    'due_date': 'data-date'
                };

                fields.forEach(field => {
                    const input = form.querySelector(`[name="${field}"]`);
                    if (input) input.value = trigger.getAttribute(dataMap[field]) || '';
                });

                // Marcar etiquetas existentes
                const tagIds = (trigger.getAttribute('data-tags') || '').split(',').filter(id => id);
                tagIds.forEach(id => {
                    const cb = form.querySelector(`[name="tags"][value="${id}"]`);
                    if (cb) cb.checked = true;
                });

                const taskId = trigger.getAttribute('data-taskid');
                form.action = `/boards/task/${taskId}/edit/`;

            } else {
                // MODO CREACIÓN
                modalTitle.textContent = 'Nueva Tarea';
                submitBtn.textContent = 'Crear Tarea';
                submitBtn.className = 'btn btn-success rounded-pill w-100 fw-bold';
                
                form.reset();
                const listId = trigger.getAttribute('data-listid');
                form.action = `/boards/list/${listId}/add-task/`;
            }
        });
    }

    // --- 2. LÓGICA DE DRAG & DROP (Con actualización de progreso) ---
    const containers = document.querySelectorAll('.tasks-container');
    const isFiltered = new URLSearchParams(window.location.search).has('tag');

    if (!isFiltered) {
        containers.forEach(container => {
            new Sortable(container, {
                group: 'kanban',
                animation: 150,
                handle: '.task-card',
                ghostClass: 'sortable-ghost',
                
                onEnd: function (evt) {
                    const taskId = evt.item.getAttribute('data-taskid');
                    const column = evt.to.closest('.kanban-column');
                    const newListId = column.querySelector('.open-task-modal').getAttribute('data-listid');

                    fetch('/boards/task/move/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({ task_id: taskId, new_list_id: newListId })
                    })
                    .then(response => {
                        if (response.ok) {
                            // Actualización visual inmediata
                            updateProgressBar();
                        } else {
                            alert('Error al mover la tarea.');
                            location.reload();
                        }
                    });
                }
            });
        });
    }

    // --- 3. BUSCADOR EN TIEMPO REAL ---
    const searchInput = document.getElementById('taskSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.task-card');

            cards.forEach(card => {
                const title = (card.getAttribute('data-title') || '').toLowerCase();
                const desc = (card.getAttribute('data-desc') || '').toLowerCase();

                if (title.includes(searchTerm) || desc.includes(searchTerm)) {
                    card.style.display = "block";
                } else {
                    card.style.display = "none";
                }
            });
        });
    }

    // --- 4. EVITAR CONFLICTO CLIC (Borrar vs Editar) ---
    document.querySelectorAll('.btn-delete-task').forEach(btn => {
        btn.addEventListener('click', e => e.stopPropagation());
    });

});

// --- FUNCIONES AUXILIARES (Fuera del DOMContentLoaded para ser accesibles) ---

/**
 * Recalcula el progreso basándose en las columnas marcadas con data-is-done
 */
function updateProgressBar() {
    const allTasks = document.querySelectorAll('.task-card').length;
    const doneTasks = document.querySelectorAll('.kanban-column[data-is-done="true"] .task-card').length;
    
    const percentage = allTasks > 0 ? Math.round((doneTasks / allTasks) * 100) : 0;

    const progressBar = document.getElementById('main-progress-bar');
    const progressText = document.getElementById('progress-text');

    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
    }
    if (progressText) {
        progressText.textContent = percentage + '%';
    }
}

/**
 * Obtiene el token CSRF de las cookies
 */
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