from django.shortcuts import render
from django.urls import reverse_lazy, reverse
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
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.views.generic import FormView
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import BoardForm, SignUpForm, CustomAuthenticationForm, ProfileForm, UserUpdateForm, CustomPasswordResetForm
from .tokens import activation_token_generator
from django.shortcuts import get_object_or_404, redirect
from .models import Board, TaskList, Task, Tag, UserProfile, BoardMembership, BoardInvite, Activity
from .forms import TaskListForm, TaskForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse
from django.http import HttpResponse
import csv
from django.core.mail import send_mail, EmailMultiAlternatives
import os
import logging
from email.mime.image import MIMEImage
from django.templatetags.static import static
from django.core import signing
from django.utils import timezone

logger = logging.getLogger(__name__)


# Vista para el Registro de Usuarios
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
    initial = {}

    def get_initial(self):
        initial = super().get_initial()
        email = self.request.GET.get("email")
        if email:
            initial["email"] = email
        return initial

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        self.object = user

        try:
            send_activation_email(self.request, user)
            messages.success(
                self.request,
                "Cuenta creada. Revisa tu correo para activar la cuenta.",
            )
            return redirect(self.get_success_url())
        except Exception:
            logger.exception("Fallo al enviar email de activación")
            messages.error(
                self.request,
                "No se pudo enviar el email de activación. Reintenta el envío.",
            )
            resend_url = f"{reverse('resend_activation')}?email={user.email}"
            return redirect(resend_url)


def send_activation_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = activation_token_generator.make_token(user)
    activation_url = request.build_absolute_uri(
        reverse("boards:activate", args=[uid, token])
    )
    context = {
        "user": user,
        "activation_url": activation_url,
    }
    subject = f"Task Master | Hola {user.username}, activa tu cuenta"
    html_body = render_to_string("registration/activation_email.html", context)
    text_body = f"Hola {user.username}, activa tu cuenta: {activation_url}"

    send_html_email(
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        to_emails=[user.email],
    )


def send_activation_success_email(request, user):
    login_url = request.build_absolute_uri(reverse("login"))
    context = {"user": user, "login_url": login_url}
    subject = f"Task Master | Hola {user.username}, tu cuenta está activa"
    html_body = render_to_string("registration/activation_success_email.html", context)
    text_body = f"Cuenta activada. Entra aquí: {login_url}"
    send_html_email(
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        to_emails=[user.email],
    )


def send_invite_email(request, invite):
    invite_token = signing.dumps({"invite_id": invite.id})
    invite_url = request.build_absolute_uri(
        reverse("boards:accept_invite", args=[invite_token])
    )
    context = {
        "invite": invite,
        "invite_url": invite_url,
    }
    subject = f"Task Master | Invitación a {invite.board.title}"
    html_body = render_to_string("registration/invite_email.html", context)
    text_body = f"Has sido invitado/a a {invite.board.title}: {invite_url}"
    send_html_email(
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        to_emails=[invite.email],
    )


def send_html_email(subject, text_body, html_body, to_emails):
    email = EmailMultiAlternatives(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        to_emails,
    )
    email.attach_alternative(html_body, "text/html")

    logo_path = os.path.join(settings.BASE_DIR, "static", "img", "taskmaster.png")
    try:
        with open(logo_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<taskmaster-logo>")
            img.add_header("Content-Disposition", "inline", filename="taskmaster.png")
            email.attach(img)
    except FileNotFoundError:
        pass

    email.send(fail_silently=False)


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "registration/login.html"

    def form_valid(self, form):
        user = form.get_user()
        is_first_login = user.last_login is None
        response = super().form_valid(form)
        if is_first_login:
            messages.success(
                self.request,
                f"Bienvenido/a, {user.username}. Tu cuenta está lista para empezar: crea tus tableros, organiza tareas y comparte con tu equipo. Equipo Task Master.",
            )
        return response


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.txt"
    html_email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"


class ResendActivationForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control rounded-pill"})
    )


class ResendActivationView(FormView):
    template_name = "registration/resend_activation.html"
    form_class = ResendActivationForm
    success_url = reverse_lazy("login")

    def get_initial(self):
        initial = super().get_initial()
        email = self.request.GET.get("email")
        if email:
            initial["email"] = email
        return initial

    def form_valid(self, form):
        email = form.cleaned_data["email"].strip().lower()
        username = form.cleaned_data["username"].strip()
        user = User.objects.filter(
            email__iexact=email, username__iexact=username
        ).first()

        if not user:
            messages.error(self.request, "No existe una cuenta con esos datos.")
            return redirect(self.get_success_url())

        if user.is_active:
            messages.info(self.request, "La cuenta ya está activada. Inicia sesión.")
            return redirect(self.get_success_url())

        try:
            send_activation_email(self.request, user)
            messages.success(self.request, "Te hemos enviado un nuevo enlace de activación.")
        except Exception:
            logger.exception("Fallo al reenviar email de activación")
            messages.error(self.request, "No se pudo enviar el email. Inténtalo más tarde.")

        return redirect(self.get_success_url())


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user:
        state = activation_token_generator.get_token_state(user, token)
        if state == "valid":
            if not user.is_active:
                user.is_active = True
                user.save()
                try:
                    send_activation_success_email(request, user)
                except Exception:
                    pass
            messages.success(request, "Cuenta activada. Ya puedes iniciar sesión.")
            return redirect("login")
        if state == "expired":
            messages.error(
                request,
                "El enlace de activación ha caducado. Solicita uno nuevo.",
            )
            return redirect(f"{reverse('resend_activation')}?email={user.email}")

    messages.error(request, "Enlace de activación inválido.")
    return redirect("login")


class ProfileView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = "profiles/profile_detail.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class ProfileUpdateView(LoginRequiredMixin, FormView):
    template_name = "profiles/profile_edit.html"
    form_class = ProfileForm
    success_url = reverse_lazy("boards:profile")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        context["profile_form"] = kwargs.get("profile_form") or ProfileForm(instance=profile)
        context["user_form"] = kwargs.get("user_form") or UserUpdateForm(instance=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect(self.success_url)

        return self.render_to_response(
            self.get_context_data(user_form=user_form, profile_form=profile_form)
        )


# Vista para listar los Tableros del usuario
class BoardListView(LoginRequiredMixin, ListView):
    model = Board
    template_name = "boards/home.html"
    context_object_name = "boards"

    def get_queryset(self):
        # Tableros donde el usuario es miembro
        return Board.objects.filter(memberships__user=self.request.user).distinct()


# Vista para crear un Tablero
class BoardCreateView(LoginRequiredMixin, CreateView):
    model = Board
    form_class = BoardForm
    template_name = "boards/board_form.html"
    success_url = reverse_lazy("boards:board_list")

    def form_valid(self, form):
        board = form.save(commit=False)
        board.owner = self.request.user
        board.save()
        BoardMembership.objects.get_or_create(
            board=board, user=self.request.user, defaults={"role": "owner"}
        )
        _log_activity(board, self.request.user, "Tablero creado", board.title)
        return redirect(self.success_url)

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
        if not BoardMembership.objects.filter(
            board=board, user=self.request.user
        ).exists():
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
        membership = BoardMembership.objects.filter(
            board=board, user=self.request.user
        ).first()
        context["user_role"] = membership.role if membership else None
        context["memberships"] = board.memberships.select_related("user").all()
        context["invites"] = board.invites.filter(accepted_at__isnull=True)
        activity_filter = self.request.GET.get("activity")
        activities_qs = board.activities.select_related("user")
        if activity_filter:
            activities_qs = activities_qs.filter(action=activity_filter)
        context["activities"] = activities_qs[:20]
        context["activity_filter"] = activity_filter
        context["activity_actions"] = (
            board.activities.values_list("action", flat=True).distinct()
        )

        # Etiquetas para el resumen superior y el modal
        context["board_tags"] = (
            Tag.objects.filter(tasks__task_list__board=board)
            .annotate(num_tasks=Count("tasks", filter=Q(tasks__task_list__board=board)))
            .distinct()
        )
        context["tags"] = Tag.objects.all()
        member_ids = board.memberships.values_list("user_id", flat=True)
        context["users"] = User.objects.filter(id__in=member_ids)

        return context


# Vista para añadir una Lista
def add_list(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    membership = BoardMembership.objects.filter(board=board, user=request.user).first()
    if not membership or membership.role not in ["owner", "editor"]:
        raise PermissionDenied
    if request.method == "POST":
        form = TaskListForm(request.POST)
        if form.is_valid():
            new_list = form.save(commit=False)
            new_list.board = board
            # Calculamos la posición (la última)
            new_list.position = board.lists.count()
            new_list.save()
            _log_activity(board, request.user, "Lista creada", new_list.title)
    return redirect("boards:board_detail", pk=board_id)


# funcion para añadir una Tarea
def add_task(request, list_id):
    task_list = get_object_or_404(TaskList, id=list_id)
    membership = BoardMembership.objects.filter(
        board=task_list.board, user=request.user
    ).first()
    if not membership or membership.role not in ["owner", "editor"]:
        raise PermissionDenied
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.task_list = task_list
            task.position = task_list.tasks.count()
            task.created_by = request.user
            task.save()
            assigned_ids = request.POST.getlist("assigned_to")
            if assigned_ids:
                valid_ids = BoardMembership.objects.filter(
                    board=task_list.board, user_id__in=assigned_ids
                ).values_list("user_id", flat=True)
                task.assigned_to.set(list(valid_ids))

            # --- PARTE NUEVA PARA ETIQUETAS ---
            selected_tags = request.POST.getlist("tags")  # Captura los checkboxes
            task.tags.set(selected_tags)  # Guarda las etiquetas en la tarea
            _log_activity(task_list.board, request.user, "Tarea creada", task.title)
    return redirect("boards:board_detail", pk=task_list.board.id)


# funcion para eliminar una Lista
@login_required
@require_POST
def delete_list(request, list_id):
    # Buscamos la lista asegurándonos de que el tablero pertenece al usuario
    task_list = get_object_or_404(TaskList, id=list_id)
    membership = BoardMembership.objects.filter(
        board=task_list.board, user=request.user
    ).first()
    if not membership or membership.role not in ["owner", "editor"]:
        raise PermissionDenied
    _log_activity(task_list.board, request.user, "Lista eliminada", task_list.title)
    board_id = task_list.board.id
    task_list.delete()
    return redirect("boards:board_detail", pk=board_id)


# funcion para eliminar una Tarea
@login_required
@require_POST
def delete_task(request, task_id):
    # Buscamos la tarea validando que el tablero pertenezca al usuario actual
    task = get_object_or_404(Task, id=task_id)
    membership = BoardMembership.objects.filter(
        board=task.task_list.board, user=request.user
    ).first()
    if not membership or membership.role not in ["owner", "editor"]:
        raise PermissionDenied
    _log_activity(task.task_list.board, request.user, "Tarea eliminada", task.title)
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
        task = get_object_or_404(Task, id=task_id)
        new_list = get_object_or_404(TaskList, id=new_list_id)
        membership = BoardMembership.objects.filter(
            board=task.task_list.board, user=request.user
        ).first()
        if not membership or membership.role not in ["owner", "editor"]:
            raise PermissionDenied
        if new_list.board_id != task.task_list.board_id:
            raise PermissionDenied

        from_list = task.task_list.title
        task.task_list = new_list
        task.save()
        _log_activity(
            new_list.board,
            request.user,
            "Tarea movida",
            f"{task.title} ({from_list} → {new_list.title})",
        )

        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)


# funcion para editar una Tarea
@login_required
@require_POST
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    membership = BoardMembership.objects.filter(
        board=task.task_list.board, user=request.user
    ).first()
    if not membership or membership.role not in ["owner", "editor"]:
        raise PermissionDenied

    # Actualizamos los campos con lo que viene del formulario
    task.title = request.POST.get("title")
    task.description = request.POST.get("description")
    task.priority = request.POST.get("priority")
    assigned_ids = request.POST.getlist("assigned_to")
    if assigned_ids:
        valid_ids = BoardMembership.objects.filter(
            board=task.task_list.board, user_id__in=assigned_ids
        ).values_list("user_id", flat=True)
        task.assigned_to.set(list(valid_ids))
    else:
        task.assigned_to.clear()

    # Manejo de la fecha (puede venir vacía)
    due_date = request.POST.get("due_date")
    task.due_date = due_date if due_date else None

    task.save()

    # --- PARTE NUEVA PARA ETIQUETAS ---
    selected_tags = request.POST.getlist("tags")
    task.tags.set(selected_tags)  # Actualiza la lista de etiquetas
    _log_activity(task.task_list.board, request.user, "Tarea actualizada", task.title)
    return redirect("boards:board_detail", pk=task.task_list.board.id)


def _require_owner(board, user):
    membership = BoardMembership.objects.filter(board=board, user=user).first()
    if not membership or membership.role != "owner":
        raise PermissionDenied


def _log_activity(board, user, action, details=""):
    Activity.objects.create(board=board, user=user, action=action, details=details)


def _require_member(board, user):
    if not BoardMembership.objects.filter(board=board, user=user).exists():
        raise PermissionDenied


@login_required
@require_POST
def add_member(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    _require_owner(board, request.user)
    identifier = request.POST.get("identifier", "").strip()
    role = request.POST.get("role", "viewer")
    if role not in ["owner", "editor", "viewer"]:
        role = "viewer"

    user = (
        User.objects.filter(username__iexact=identifier).first()
        or User.objects.filter(email__iexact=identifier).first()
    )
    if not user:
        messages.error(request, "No existe un usuario con ese nombre o email.")
        return redirect("boards:board_detail", pk=board_id)

    BoardMembership.objects.update_or_create(
        board=board, user=user, defaults={"role": role}
    )
    messages.success(request, "Miembro actualizado.")
    _log_activity(board, request.user, "Miembro añadido/actualizado", f"{user.username} ({role})")
    return redirect("boards:board_detail", pk=board_id)


@login_required
@require_POST
def update_member_role(request, board_id, membership_id):
    board = get_object_or_404(Board, id=board_id)
    _require_owner(board, request.user)
    membership = get_object_or_404(BoardMembership, id=membership_id, board=board)
    role = request.POST.get("role", membership.role)
    if role in ["owner", "editor", "viewer"]:
        membership.role = role
        membership.save()
    messages.success(request, "Rol actualizado.")
    _log_activity(board, request.user, "Rol actualizado", f"{membership.user.username} → {membership.role}")
    return redirect("boards:board_detail", pk=board_id)


@login_required
@require_POST
def remove_member(request, board_id, membership_id):
    board = get_object_or_404(Board, id=board_id)
    _require_owner(board, request.user)
    membership = get_object_or_404(BoardMembership, id=membership_id, board=board)
    if membership.user_id == board.owner_id:
        messages.error(request, "No puedes eliminar al propietario del tablero.")
        return redirect("boards:board_detail", pk=board_id)
    _log_activity(board, request.user, "Miembro eliminado", membership.user.username)
    membership.delete()
    messages.success(request, "Miembro eliminado.")
    return redirect("boards:board_detail", pk=board_id)


@login_required
def export_tasks_csv(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    membership = BoardMembership.objects.filter(board=board, user=request.user).first()
    if not membership or membership.role not in ["owner", "editor"]:
        raise PermissionDenied

    tasks = (
        Task.objects.filter(task_list__board=board)
        .select_related("task_list", "created_by")
        .prefetch_related("assigned_to", "tags")
        .order_by("task_list__position", "position")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="board_{board.id}_tasks.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "id",
        "title",
        "description",
        "priority",
        "due_date",
        "list",
        "list_id",
        "created_by",
        "created_by_id",
        "assigned_to",
        "assigned_to_ids",
        "tags",
        "tags_ids",
        "created_at",
        "position",
    ])
    for t in tasks:
        assigned = ", ".join([u.username for u in t.assigned_to.all()])
        assigned_ids = ", ".join([str(u.id) for u in t.assigned_to.all()])
        tags = ", ".join([tag.name for tag in t.tags.all()])
        tag_ids = ", ".join([str(tag.id) for tag in t.tags.all()])
        writer.writerow([
            t.id,
            t.title,
            t.description,
            t.priority,
            t.due_date.isoformat() if t.due_date else "",
            t.task_list.title,
            t.task_list.id,
            t.created_by.username if t.created_by else "",
            t.created_by.id if t.created_by else "",
            assigned,
            assigned_ids,
            tags,
            tag_ids,
            t.created_at.isoformat() if t.created_at else "",
            t.position,
        ])

    return response


@login_required
def export_tasks_json(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    membership = BoardMembership.objects.filter(board=board, user=request.user).first()
    if not membership or membership.role not in ["owner", "editor"]:
        raise PermissionDenied

    tasks = (
        Task.objects.filter(task_list__board=board)
        .select_related("task_list", "created_by")
        .prefetch_related("assigned_to", "tags")
        .order_by("task_list__position", "position")
    )

    data = []
    for t in tasks:
        data.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "list": {"id": t.task_list.id, "title": t.task_list.title},
            "created_by": {
                "id": t.created_by.id,
                "username": t.created_by.username,
            } if t.created_by else None,
            "assigned_to": [
                {"id": u.id, "username": u.username} for u in t.assigned_to.all()
            ],
            "tags": [{"id": tag.id, "name": tag.name} for tag in t.tags.all()],
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "position": t.position,
        })

    return JsonResponse({"board": board.title, "tasks": data})


@login_required
def export_activity_csv(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    membership = BoardMembership.objects.filter(board=board, user=request.user).first()
    if not membership or membership.role not in ["owner", "editor"]:
        raise PermissionDenied

    activity_filter = request.GET.get("activity")
    activities = board.activities.select_related("user")
    if activity_filter:
        activities = activities.filter(action=activity_filter)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="board_{board.id}_activity.csv"'

    writer = csv.writer(response)
    writer.writerow(["id", "action", "details", "user", "created_at"])
    for a in activities:
        writer.writerow([
            a.id,
            a.action,
            a.details,
            a.user.username if a.user else "",
            a.created_at.isoformat() if a.created_at else "",
        ])

    return response


@login_required
@require_POST
def invite_member(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    _require_owner(board, request.user)
    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip().lower()
    role = request.POST.get("role", "viewer")
    if role not in ["owner", "editor", "viewer"]:
        role = "viewer"
    if not email or not username:
        messages.error(request, "Email inválido.")
        return redirect("boards:board_detail", pk=board_id)

    user = User.objects.filter(username__iexact=username, email__iexact=email).first()
    if not user:
        messages.error(request, "No existe un usuario con ese nombre y email.")
        return redirect("boards:board_detail", pk=board_id)

    invite, _ = BoardInvite.objects.update_or_create(
        board=board,
        email=email,
        username=username,
        defaults={"role": role, "invited_by": request.user, "accepted_at": None},
    )

    try:
        send_invite_email(request, invite)
        messages.success(request, "Invitación enviada.")
        _log_activity(board, request.user, "Invitación enviada", f"{invite.username} · {invite.email}")
    except Exception:
        logger.exception("Fallo al enviar invitación")
        messages.error(request, "No se pudo enviar la invitación.")

    return redirect("boards:board_detail", pk=board_id)


def accept_invite(request, token):
    try:
        data = signing.loads(
            token,
            max_age=getattr(settings, "INVITE_TOKEN_TIMEOUT", 60 * 60 * 24 * 7),
        )
        invite_id = data.get("invite_id")
    except Exception:
        messages.error(request, "Invitación inválida o caducada.")
        return redirect("boards:board_list")

    invite = get_object_or_404(BoardInvite, id=invite_id)
    if invite.accepted_at:
        messages.info(request, "La invitación ya fue aceptada.")
        return redirect("boards:board_detail", pk=invite.board.id)

    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}&email={invite.email}")

    if request.user.email.lower() != invite.email.lower():
        messages.error(request, "Esta invitación no corresponde a tu email.")
        return redirect("boards:board_list")
    if invite.username and request.user.username.lower() != invite.username.lower():
        messages.error(request, "Esta invitación no corresponde a tu usuario y email.")
        return redirect("boards:board_list")

    BoardMembership.objects.update_or_create(
        board=invite.board, user=request.user, defaults={"role": invite.role}
    )
    invite.accepted_at = timezone.now()
    invite.save()
    _log_activity(invite.board, request.user, "Invitación aceptada", request.user.username)
    messages.success(request, "Invitación aceptada. Ya tienes acceso al tablero.")
    return redirect("boards:board_detail", pk=invite.board.id)


@login_required
@require_POST
def revoke_invite(request, board_id, invite_id):
    board = get_object_or_404(Board, id=board_id)
    _require_owner(board, request.user)
    invite = get_object_or_404(BoardInvite, id=invite_id, board=board)
    invite.delete()
    messages.success(request, "Invitación revocada.")
    _log_activity(board, request.user, "Invitación revocada", invite.email)
    return redirect("boards:board_detail", pk=board_id)
