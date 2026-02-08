document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. LÓGICA DE LOS MODALES (Creación y Edición) ---
    const taskModal = document.getElementById('taskModal');
    
    if (taskModal) {
        taskModal.addEventListener('show.bs.modal', function (event) {
            const trigger = event.relatedTarget; // El botón que abrió el modal
            const form = document.getElementById('taskForm');
            const modalTitle = taskModal.querySelector('.modal-title');
            const submitBtn = form.querySelector('button[type="submit"]');

            // Limpieza total antes de empezar
            form.reset();
            form.querySelectorAll('[name="tags"]').forEach(cb => cb.checked = false);

            if (trigger.classList.contains('btn-edit-task')) {
                // MODO EDICIÓN
                const card = trigger.closest('.task-card');
                const taskId = card.getAttribute('data-taskid');
                
                modalTitle.textContent = 'Editar Tarea';
                submitBtn.textContent = 'Guardar Cambios';

                // Rellenar datos desde los atributos data- de la tarjeta
                form.querySelector('[name="title"]').value = card.getAttribute('data-title') || '';
                form.querySelector('[name="description"]').value = card.getAttribute('data-desc') || '';
                form.querySelector('[name="priority"]').value = card.getAttribute('data-prio') || 'medium';
                form.querySelector('[name="due_date"]').value = card.getAttribute('data-date') || '';

                // Marcar etiquetas
                const tagIds = (card.getAttribute('data-tags') || '').split(',').filter(id => id);
                tagIds.forEach(id => {
                    const cb = form.querySelector(`[name="tags"][value="${id}"]`);
                    if (cb) cb.checked = true;
                });

                // URL de Edición (Evita el error 405)
                form.action = `/boards/task/${taskId}/edit/`;

            } else {
                // MODO CREACIÓN
                modalTitle.textContent = 'Nueva Tarea';
                submitBtn.textContent = 'Crear Tarea';
                
                const listId = trigger.getAttribute('data-listid');
                // URL de Creación (Evita el error 405)
                form.action = `/boards/list/${listId}/add-task/`;
            }
        });
    }

    // --- 2. LÓGICA DE DRAG & DROP (SortableJS) ---
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
            document.querySelectorAll('.task-card').forEach(card => {
                const title = (card.getAttribute('data-title') || '').toLowerCase();
                const desc = (card.getAttribute('data-desc') || '').toLowerCase();
                card.style.display = (title.includes(searchTerm) || desc.includes(searchTerm)) ? "block" : "none";
            });
        });
    }

    // --- 4. PREVENIR BURBUJEO EN BORRADO ---
    document.querySelectorAll('.btn-delete-task').forEach(btn => {
        btn.addEventListener('click', e => e.stopPropagation());
    });

});

// --- FUNCIONES AUXILIARES ---

function updateProgressBar() {
    const allTasks = document.querySelectorAll('.task-card').length;
    const doneTasks = document.querySelectorAll('.kanban-column[data-is-done="true"] .task-card').length;
    const percentage = allTasks > 0 ? Math.round((doneTasks / allTasks) * 100) : 0;
    const progressBar = document.getElementById('main-progress-bar');
    const progressText = document.getElementById('progress-text');

    if (progressBar) progressBar.style.width = percentage + '%';
    if (progressText) progressText.textContent = percentage + '%';
}

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