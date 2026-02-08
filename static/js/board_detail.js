document.addEventListener('DOMContentLoaded', function() {
    const updateProgressBar = () => {
        const total = document.querySelectorAll('.task-card').length;
        const done = document.querySelectorAll('.kanban-column[data-is-done="true"] .task-card').length;
        const percent = total > 0 ? Math.round((done / total) * 100) : 0;
        const bar = document.getElementById('main-progress-bar');
        const txt = document.getElementById('progress-text');
        if (bar) bar.style.width = percent + '%';
        if (txt) txt.textContent = percent + '%';
    };

    updateProgressBar();

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
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.task-card').forEach(card => {
                const text = (card.getAttribute('data-title') + card.getAttribute('data-desc')).toLowerCase();
                card.style.display = text.includes(term) ? "block" : "none";
            });
        });
    }
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
