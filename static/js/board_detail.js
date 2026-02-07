/**
 * Lógica para el Tablero Kanban de Task Master
 */
document.addEventListener('DOMContentLoaded', function() {
    const taskModal = document.getElementById('taskModal');
    
    if (taskModal) {
        taskModal.addEventListener('show.bs.modal', function(event) {
            // Botón que disparó el modal
            const button = event.relatedTarget;
            
            // Extraer la información de los atributos data-
            const listId = button.getAttribute('data-listid');
            const form = document.getElementById('taskForm');
            
            // Actualizar la acción del formulario dinámicamente
            // Importante: Asegúrate de que esta ruta coincida con tu urls.py
            form.action = `/boards/list/${listId}/add-task/`;
            
            console.log(`Abriendo modal para la lista ID: ${listId}`);
        });
    }
});