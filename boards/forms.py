from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
import os
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Board, TaskList, Task, UserProfile


# ---------------------------------------------------------------------
# Formularios de tablero y autenticación
# ---------------------------------------------------------------------
# Formulario para crear un Tablero
class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control rounded-pill",
                    "placeholder": "Ej: Proyecto de Desarrollo Web",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control rounded-4",
                    "placeholder": "¿De qué trata este tablero?",
                    "rows": 3,
                }
            ),
        }


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control rounded-pill"})
            field.widget.attrs.setdefault("id", f"signup-{name}")
        if "email" in self.fields:
            self.fields["email"].required = True

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control rounded-pill"}),
            "email": forms.EmailInput(attrs={"class": "form-control rounded-pill"}),
        }


# Bloquea login de cuentas sin activar.
class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                _("Tu cuenta no está activada. Revisa tu correo o reenvía el enlace."),
                code="inactive",
            )


# ---------------------------------------------------------------------
# Formularios de perfil
# ---------------------------------------------------------------------
class ProfileForm(forms.ModelForm):
    MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
    ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

    class Meta:
        model = UserProfile
        fields = (
            "bio",
            "avatar",
            "notify_task_assigned",
            "notify_task_due",
            "notify_task_status",
            "cookie_consent",
        )
        widgets = {
            "bio": forms.Textarea(
                attrs={"class": "form-control rounded-4", "rows": 3}
            ),
            "cookie_consent": forms.Select(
                attrs={"class": "form-select rounded-pill"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cookie_consent"].required = False
        self.fields["cookie_consent"].label = "Preferencia de cookies"
        self.fields["cookie_consent"].choices = [
            ("", "Sin definir"),
            *UserProfile.COOKIE_CONSENT_CHOICES,
        ]

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            return avatar

        # Si no es un upload nuevo (ej. imagen existente en perfil), no forzamos validación MIME.
        if not hasattr(avatar, "content_type"):
            return avatar

        content_type = getattr(avatar, "content_type", "")
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationError("Formato de imagen no válido (usa JPG, PNG, GIF o WEBP).")

        if avatar.size > self.MAX_AVATAR_SIZE:
            raise ValidationError("La imagen supera el tamaño máximo de 2MB.")

        return avatar

    def save(self, commit=True):
        profile = super().save(commit=False)
        selected = profile.cookie_consent or None
        previous = None
        if self.instance and self.instance.pk:
            previous = self.instance.cookie_consent

        if selected != previous:
            profile.cookie_consent_updated_at = timezone.now() if selected else None

        if commit:
            profile.save()
        return profile


# Actualiza datos base del usuario (tabla auth_user).
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control rounded-pill"}),
            "email": forms.EmailInput(attrs={"class": "form-control rounded-pill"}),
            "first_name": forms.TextInput(attrs={"class": "form-control rounded-pill"}),
            "last_name": forms.TextInput(attrs={"class": "form-control rounded-pill"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Ese nombre de usuario ya existe."))
        return username


# Formulario custom para reset: exige coincidencia usuario + email.
class CustomPasswordResetForm(PasswordResetForm):
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control rounded-pill"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["username"].required = True

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").strip()
        username = cleaned_data.get("username", "").strip()
        if email and username:
            exists = User._default_manager.filter(
                email__iexact=email, username__iexact=username, is_active=True
            ).exists()
            if not exists:
                raise forms.ValidationError(
                    "Revisa tu nombre de usuario y email, no coinciden. "
                    "Si necesitas ayuda escribe a soporte@taskmaster.com."
                )
        return cleaned_data

    def get_users(self, email):
        username = self.cleaned_data.get("username", "").strip()
        return User._default_manager.filter(
            email__iexact=email, username__iexact=username, is_active=True
        )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        subject = render_to_string(subject_template_name, context).strip()
        text_body = render_to_string(email_template_name, context)
        html_body = ""
        if html_email_template_name:
            html_body = render_to_string(html_email_template_name, context)

        email = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
        if html_body:
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


# ---------------------------------------------------------------------
# Formularios Kanban: listas y tareas
# ---------------------------------------------------------------------
# Formulario para crear una Lista de Tareas
class TaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control rounded-pill",
                    "placeholder": "Ej: Por hacer",
                }
            )
        }


# Formulario para crear una Tarea
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "due_date", "assigned_to"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control rounded-pill"}),
            "description": forms.Textarea(
                attrs={"class": "form-control rounded-4", "rows": 3}
            ),
            "priority": forms.Select(attrs={"class": "form-select rounded-pill"}),
            "due_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control rounded-pill",
                    "type": "datetime-local",  # Esto hace que aparezca el calendario del navegador
                }
            ),
        }
