// Inicializa comportamiento interactivo del detalle de tablero (Kanban).
document.addEventListener('DOMContentLoaded', function() {
    // Activa tooltips de Bootstrap en botones/acciones con atributo data-bs-toggle.
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });

    // Helper para mostrar spinner y evitar doble submit en formularios inline.
    const bindSpinner = (form, labelText, hideLabel) => {
        if (!form) return;
        form.addEventListener('submit', () => {
            const btn = form.querySelector('button[type="submit"]');
            if (!btn) return;
            btn.disabled = true;
            const spinner = btn.querySelector('.spinner-border');
            const label = btn.querySelector('.label');
            if (spinner) spinner.classList.remove('d-none');
            if (label && !hideLabel) label.textContent = labelText;
        });
    };

    bindSpinner(document.querySelector('.invite-form'), 'Enviando...');
    bindSpinner(document.querySelector('.member-form'), 'Guardando...');
    bindSpinner(document.querySelector('.task-form'), 'Guardando...');
    document.querySelectorAll('.role-form').forEach(form => bindSpinner(form, '', true));

    // Recalcula progreso según tareas en columnas marcadas como "done".
    const updateProgressBar = () => {
        const total = document.querySelectorAll('.task-card').length;
        const done = document.querySelectorAll('.kanban-column[data-is-done="true"] .task-card').length;
        const percent = total > 0 ? Math.round((done / total) * 100) : 0;
        const bar = document.getElementById('main-progress-bar');
        const txt = document.getElementById('progress-text');
        if (bar) bar.style.width = percent + '%';
        if (txt) txt.textContent = percent + '%';
    };

    let activePriority = null;
    let activeStatus = null;
    let searchTerm = '';
    const TASKS_PAGE_SIZE = 10;

    // Paginación cliente por columna para no renderizar listas largas de una vez.
    const updatePagination = (column) => {
        if (!column) return;
        const allCards = Array.from(column.querySelectorAll('.task-card'));
        const filteredCards = allCards.filter(card => !card.classList.contains('filter-hidden'));
        const totalPages = Math.max(1, Math.ceil(filteredCards.length / TASKS_PAGE_SIZE));
        let page = parseInt(column.getAttribute('data-page') || '1', 10);
        if (page > totalPages) page = totalPages;
        if (page < 1) page = 1;
        column.setAttribute('data-page', page);

        filteredCards.forEach((card, idx) => {
            const pageIndex = Math.floor(idx / TASKS_PAGE_SIZE) + 1;
            card.classList.toggle('page-hidden', pageIndex !== page);
        });

        const pagination = column.querySelector('.task-pagination');
        if (pagination) {
            const prevBtn = pagination.querySelector('.task-page-prev');
            const nextBtn = pagination.querySelector('.task-page-next');
            const info = pagination.querySelector('.task-page-info');
            pagination.classList.toggle('d-none', filteredCards.length <= TASKS_PAGE_SIZE);
            if (info) info.textContent = `${page}/${totalPages}`;
            if (prevBtn) prevBtn.disabled = page <= 1;
            if (nextBtn) nextBtn.disabled = page >= totalPages;
        }
    };

    // Filtros combinados por estado de columna, prioridad y texto de búsqueda.
    const applyFilters = () => {
        const columns = document.querySelectorAll('.kanban-column');
        columns.forEach(column => {
            const status = column.getAttribute('data-status') || 'other';
            const matchesStatus = !activeStatus || status === activeStatus;
            column.classList.toggle('d-none', !matchesStatus);
            if (!matchesStatus) return;

            const cards = column.querySelectorAll('.task-card');
            cards.forEach(card => {
                const title = card.getAttribute('data-title') || '';
                const desc = card.getAttribute('data-desc') || '';
                const text = (title + desc).toLowerCase();
                const prio = (card.getAttribute('data-prio') || '').toLowerCase();

                const matchesSearch = !searchTerm || text.includes(searchTerm);
                const matchesPriority = !activePriority || prio.includes(activePriority);
                card.classList.toggle('filter-hidden', !(matchesSearch && matchesPriority));
            });
            column.setAttribute('data-page', '1');
            updatePagination(column);
        });
        updateStatusSummary();
    };

    // Resumen de prioridades (alta/media/baja) mostrado en la barra superior.
    const updatePrioritySummary = () => {
        const cards = document.querySelectorAll('.task-card');
        let high = 0, medium = 0, low = 0;
        cards.forEach(card => {
            const prio = (card.getAttribute('data-prio') || '').toLowerCase();
            if (prio.includes('high') || prio.includes('alta')) high += 1;
            else if (prio.includes('medium') || prio.includes('media')) medium += 1;
            else if (prio.includes('low') || prio.includes('baja')) low += 1;
        });
        const highEl = document.getElementById('prio-high-count');
        const mediumEl = document.getElementById('prio-medium-count');
        const lowEl = document.getElementById('prio-low-count');
        if (highEl) highEl.textContent = high;
        if (mediumEl) mediumEl.textContent = medium;
        if (lowEl) lowEl.textContent = low;
    };

    // Resumen de estados visibles (todo/doing/done) según filtros activos.
    const updateStatusSummary = () => {
        const columns = document.querySelectorAll('.kanban-column');
        let todo = 0, doing = 0, done = 0;
        columns.forEach(column => {
            const status = column.getAttribute('data-status') || 'other';
            const visibleCards = column.querySelectorAll('.task-card:not(.filter-hidden)').length;
            if (status === 'todo') todo += visibleCards;
            else if (status === 'doing') doing += visibleCards;
            else if (status === 'done') done += visibleCards;
        });
        const todoEl = document.getElementById('status-todo-count');
        const doingEl = document.getElementById('status-doing-count');
        const doneEl = document.getElementById('status-done-count');
        if (todoEl) todoEl.textContent = todo;
        if (doingEl) doingEl.textContent = doing;
        if (doneEl) doneEl.textContent = done;
    };

    updateProgressBar();
    updatePrioritySummary();
    updateStatusSummary();
    applyFilters();

    // Configura modal para crear o editar tarea según botón que lo abre.
    const taskModal = document.getElementById('taskModal');
    if (taskModal) {
        taskModal.addEventListener('show.bs.modal', function (event) {
            const trigger = event.relatedTarget;
            const form = document.getElementById('taskForm');
            form.reset();
            form.querySelectorAll('[name="tags"]').forEach(cb => cb.checked = false);
            form.querySelectorAll('[name="assigned_to"]').forEach(cb => cb.checked = false);

            if (trigger.classList.contains('btn-edit-task')) {
                const card = trigger.closest('.task-card');
                form.querySelector('[name="title"]').value = card.getAttribute('data-title');
                form.querySelector('[name="description"]').value = card.getAttribute('data-desc');
                form.querySelector('[name="priority"]').value = card.getAttribute('data-prio');
                form.querySelector('[name="due_date"]').value = card.getAttribute('data-date');
                const createdBy = card.getAttribute('data-created-by') || '';
                const createdByInput = form.querySelector('[name="created_by_readonly"]');
                if (createdByInput) createdByInput.value = createdBy;
                const assigned = (card.getAttribute('data-assigned') || '').split(',').filter(Boolean);
                form.querySelectorAll('[name="assigned_to"]').forEach(cb => {
                    cb.checked = assigned.includes(cb.value);
                });
                const tagIds = (card.getAttribute('data-tags') || '').split(',');
                tagIds.forEach(id => {
                    const cb = form.querySelector(`[name="tags"][value="${id}"]`);
                    if (cb) cb.checked = true;
                });
                form.action = `/boards/task/${card.getAttribute('data-taskid')}/edit/`;
            } else {
                form.action = `/boards/list/${trigger.getAttribute('data-listid')}/add-task/`;
            }
        });
    }

    // Habilita drag & drop entre columnas y sincroniza movimiento por API.
    const containers = document.querySelectorAll('.tasks-container');
    containers.forEach(container => {
        new Sortable(container, {
            group: 'kanban', animation: 150, handle: '.task-grip, .task-title',
            onEnd: function (evt) {
                updateProgressBar();
                updatePrioritySummary();
                applyFilters();
                const taskId = evt.item.getAttribute('data-taskid');
                const column = evt.to.closest('.kanban-column');
                const newListId = column.querySelector('.open-task-modal').getAttribute('data-listid');
                // Movimiento persistido en backend; la UI ya refleja el cambio local.
                fetch('/boards/task/move/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
                    body: JSON.stringify({ task_id: taskId, new_list_id: newListId })
                });
            }
        });
    });

    // Controles de paginación por columna.
    document.querySelectorAll('.task-pagination').forEach(pagination => {
        const column = pagination.closest('.kanban-column');
        const prevBtn = pagination.querySelector('.task-page-prev');
        const nextBtn = pagination.querySelector('.task-page-next');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                const current = parseInt(column.getAttribute('data-page') || '1', 10);
                column.setAttribute('data-page', String(current - 1));
                updatePagination(column);
            });
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                const current = parseInt(column.getAttribute('data-page') || '1', 10);
                column.setAttribute('data-page', String(current + 1));
                updatePagination(column);
            });
        }
    });

    // Búsqueda instantánea por título + descripción.
    const searchInput = document.getElementById('taskSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchTerm = e.target.value.toLowerCase();
            applyFilters();
        });
    }

    // Filtro por prioridad (con soporte teclado para accesibilidad).
    document.querySelectorAll('.priority-filter').forEach(badge => {
        const activate = () => {
            const prio = badge.getAttribute('data-priority');
            activePriority = (activePriority === prio) ? null : prio;
            document.querySelectorAll('.priority-filter').forEach(b => {
                const isActive = activePriority && b.getAttribute('data-priority') === activePriority;
                b.classList.toggle('active', !!isActive);
                b.setAttribute('aria-pressed', isActive ? 'true' : 'false');
            });
            applyFilters();
            updateStatusSummary();
        };
        badge.addEventListener('click', activate);
        badge.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                activate();
            }
        });
    });

    // Filtro por estado de columna (con soporte teclado para accesibilidad).
    document.querySelectorAll('.status-filter').forEach(badge => {
        const activate = () => {
            const status = badge.getAttribute('data-status');
            activeStatus = (activeStatus === status) ? null : status;
            document.querySelectorAll('.status-filter').forEach(b => {
                const isActive = activeStatus && b.getAttribute('data-status') === activeStatus;
                b.classList.toggle('active', !!isActive);
                b.setAttribute('aria-pressed', isActive ? 'true' : 'false');
            });
            applyFilters();
            updateStatusSummary();
        };
        badge.addEventListener('click', activate);
        badge.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                activate();
            }
        });
    });

    // Redimensiona panel de actividad mediante arrastre (desktop y touch).
    const resizer = document.querySelector('.board-resizer');
    const boardLayout = document.querySelector('.board-layout');
    if (resizer && boardLayout) {
        let isDragging = false;
        const minWidth = 200;
        const maxWidth = 480;

        const onMove = (e) => {
            if (!isDragging) return;
            const rect = boardLayout.getBoundingClientRect();
            const x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
            const next = Math.max(minWidth, Math.min(maxWidth, x));
            boardLayout.style.setProperty('--activity-panel-width', `${next}px`);
        };

        const onUp = () => {
            if (!isDragging) return;
            isDragging = false;
            document.body.classList.remove('user-select-none');
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            document.removeEventListener('touchmove', onMove);
            document.removeEventListener('touchend', onUp);
        };

        const onDown = (e) => {
            isDragging = true;
            document.body.classList.add('user-select-none');
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
            document.addEventListener('touchmove', onMove, { passive: true });
            document.addEventListener('touchend', onUp);
        };

        resizer.addEventListener('mousedown', onDown);
        resizer.addEventListener('touchstart', onDown, { passive: true });
    }
});

// Helper clásico de CSRF para peticiones fetch POST en Django.
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
