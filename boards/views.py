from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.db.models import Count, Q, Prefetch
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import BoardForm, SignUpForm
from django.shortcuts import get_object_or_404, redirect
from .models import Board, TaskList, Task, Tag
from .forms import TaskListForm, TaskForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse


# Vista para el Registro de Usuarios
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Cuenta creada. Ya puedes iniciar sesión.",
        )
        return response


# Vista para listar los Tableros del usuario
class BoardListView(LoginRequiredMixin, ListView):
    model = Board
    template_name = "boards/home.html"
    context_object_name = "boards"

    def get_queryset(self):
        # Solo mostramos los tableros que pertenecen al usuario activo
        return Board.objects.filter(owner=self.request.user)


# Vista para crear un Tablero
class BoardCreateView(LoginRequiredMixin, CreateView):
    model = Board
    form_class = BoardForm
    template_name = "boards/board_form.html"
    success_url = reverse_lazy("boards:board_list")

    def form_valid(self, form):
        # Asignamos el usuario actual como dueño del tablero
        form.instance = form.save(commit=False)
        form.instance.owner = self.request.user
        return super().form_valid(form)


# Vista para ver un Tablero en detalle
class BoardDetailView(LoginRequiredMixin, DetailView):
    model = Board
    template_name = "boards/board_detail.html"
    context_object_name = "board"

    def get_object(self, queryset=None):
        board = super().get_object(queryset)
        if board.owner != self.request.user:
            raise PermissionDenied
        return board

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        board = self.get_object()

        # --- 1. LÓGICA DE FILTRADO Y DEFINICIÓN DE LISTAS ---
        active_tag_id = self.request.GET.get("tag")
        tasks_queryset = Task.objects.all()

        if active_tag_id:
            tasks_queryset = tasks_queryset.filter(tags__id=active_tag_id)
            context["active_tag"] = get_object_or_404(Tag, id=active_tag_id)

        # Aquí definimos la variable que te daba el NameError
        lists_with_filtered_tasks = board.lists.prefetch_related(
            Prefetch("tasks", queryset=tasks_queryset.order_by("position"))
        )

        # --- 2. CÁLCULO DE PROGRESO ---
        all_tasks = Task.objects.filter(task_list__board=board)
        total_count = all_tasks.count()

        done_tasks = all_tasks.filter(
            Q(task_list__title__icontains="hecho")
            | Q(task_list__title__icontains="terminado")
            | Q(task_list__title__icontains="done")
            | Q(task_list__title__icontains="completa")
            | Q(task_list__title__icontains="finalizada")
        ).count()

        progress = int((done_tasks / total_count) * 100) if total_count > 0 else 0

        # --- 3. PASAR DATOS AL CONTEXTO ---
        context["board_lists"] = lists_with_filtered_tasks
        context["progress"] = progress
        context["done_tasks"] = done_tasks
        context["total_tasks"] = (
            total_count  # Corregido: antes intentabas usar total_tasks sin definirlo
        )

        # Etiquetas para el resumen superior y el modal
        context["board_tags"] = (
            Tag.objects.filter(tasks__task_list__board=board)
            .annotate(num_tasks=Count("tasks", filter=Q(tasks__task_list__board=board)))
            .distinct()
        )
        context["tags"] = Tag.objects.all()
        context["users"] = User.objects.all()

        return context


# Vista para añadir una Lista
def add_list(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    if request.method == "POST":
        form = TaskListForm(request.POST)
        if form.is_valid():
            new_list = form.save(commit=False)
            new_list.board = board
            # Calculamos la posición (la última)
            new_list.position = board.lists.count()
            new_list.save()
    return redirect("boards:board_detail", pk=board_id)


# funcion para añadir una Tarea
def add_task(request, list_id):
    task_list = get_object_or_404(TaskList, id=list_id, board__owner=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.task_list = task_list
            task.position = task_list.tasks.count()
            task.created_by = request.user
            task.save()

            # --- PARTE NUEVA PARA ETIQUETAS ---
            selected_tags = request.POST.getlist("tags")  # Captura los checkboxes
            task.tags.set(selected_tags)  # Guarda las etiquetas en la tarea
    return redirect("boards:board_detail", pk=task_list.board.id)


# funcion para eliminar una Lista
@login_required
@require_POST
def delete_list(request, list_id):
    # Buscamos la lista asegurándonos de que el tablero pertenece al usuario
    task_list = get_object_or_404(TaskList, id=list_id, board__owner=request.user)
    board_id = task_list.board.id
    task_list.delete()
    return redirect("boards:board_detail", pk=board_id)


# funcion para eliminar una Tarea
@login_required
@require_POST
def delete_task(request, task_id):
    # Buscamos la tarea validando que el tablero pertenezca al usuario actual
    task = get_object_or_404(Task, id=task_id, task_list__board__owner=request.user)
    board_id = task.task_list.board.id
    task.delete()
    return redirect("boards:board_detail", pk=board_id)


# funcion para mover una Tarea
@login_required
def move_task(request):
    if request.method == "POST":
        data = json.loads(request.body)
        task_id = data.get("task_id")
        new_list_id = data.get("new_list_id")

        # Buscamos la tarea y la nueva lista
        task = get_object_or_404(Task, id=task_id, task_list__board__owner=request.user)
        new_list = get_object_or_404(
            TaskList, id=new_list_id, board__owner=request.user
        )

        task.task_list = new_list
        task.save()

        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


# funcion para editar una Tarea
@login_required
@require_POST
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, task_list__board__owner=request.user)

    # Actualizamos los campos con lo que viene del formulario
    task.title = request.POST.get("title")
    task.description = request.POST.get("description")
    task.priority = request.POST.get("priority")
    assigned_to_id = request.POST.get("assigned_to") or None
    task.assigned_to_id = assigned_to_id

    # Manejo de la fecha (puede venir vacía)
    due_date = request.POST.get("due_date")
    task.due_date = due_date if due_date else None

    task.save()

    # --- PARTE NUEVA PARA ETIQUETAS ---
    selected_tags = request.POST.getlist("tags")
    task.tags.set(selected_tags)  # Actualiza la lista de etiquetas
    return redirect("boards:board_detail", pk=task.task_list.board.id)
