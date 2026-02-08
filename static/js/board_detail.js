document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });

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
    document.querySelectorAll('.role-form').forEach(form => bindSpinner(form, '', true));
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
    let searchTerm = '';

    const applyFilters = () => {
        const cards = document.querySelectorAll('.task-card');
        cards.forEach(card => {
            const title = card.getAttribute('data-title') || '';
            const desc = card.getAttribute('data-desc') || '';
            const text = (title + desc).toLowerCase();
            const prio = (card.getAttribute('data-prio') || '').toLowerCase();

            const matchesSearch = !searchTerm || text.includes(searchTerm);
            const matchesPriority = !activePriority || prio.includes(activePriority);
            card.style.display = (matchesSearch && matchesPriority) ? 'block' : 'none';
        });
    };

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

    updateProgressBar();
    updatePrioritySummary();
    applyFilters();

    const taskModal = document.getElementById('taskModal');
    if (taskModal) {
        taskModal.addEventListener('show.bs.modal', function (event) {
            const trigger = event.relatedTarget;
            const form = document.getElementById('taskForm');
            form.reset();
            form.querySelectorAll('[name="tags"]').forEach(cb => cb.checked = false);

            if (trigger.classList.contains('btn-edit-task')) {
                const card = trigger.closest('.task-card');
                form.querySelector('[name="title"]').value = card.getAttribute('data-title');
                form.querySelector('[name="description"]').value = card.getAttribute('data-desc');
                form.querySelector('[name="priority"]').value = card.getAttribute('data-prio');
                form.querySelector('[name="due_date"]').value = card.getAttribute('data-date');
                const assigned = card.getAttribute('data-assigned') || '';
                const assignedSelect = form.querySelector('[name="assigned_to"]');
                if (assignedSelect) assignedSelect.value = assigned;
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

    const containers = document.querySelectorAll('.tasks-container');
    containers.forEach(container => {
        new Sortable(container, {
            group: 'kanban', animation: 150, handle: '.task-grip, .task-title',
            onEnd: function (evt) {
                updateProgressBar();
                updatePrioritySummary();
                const taskId = evt.item.getAttribute('data-taskid');
                const column = evt.to.closest('.kanban-column');
                const newListId = column.querySelector('.open-task-modal').getAttribute('data-listid');
                fetch('/boards/task/move/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
                    body: JSON.stringify({ task_id: taskId, new_list_id: newListId })
                });
            }
        });
    });

    const searchInput = document.getElementById('taskSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchTerm = e.target.value.toLowerCase();
            applyFilters();
        });
    }

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
        };
        badge.addEventListener('click', activate);
        badge.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                activate();
            }
        });
    });
});

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
