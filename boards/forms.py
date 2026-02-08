from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
import os
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Board, TaskList, Task, UserProfile


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



class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(
                _("Tu cuenta no está activada. Revisa tu correo o reenvía el enlace."),
                code="inactive",
            )


class ProfileForm(forms.ModelForm):
    MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
    ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

    class Meta:
        model = UserProfile
        fields = ("bio", "avatar")
        widgets = {
            "bio": forms.Textarea(
                attrs={"class": "form-control rounded-4", "rows": 3}
            ),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            return avatar

        content_type = getattr(avatar, "content_type", "")
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationError("Formato de imagen no válido (usa JPG, PNG, GIF o WEBP).")

        if avatar.size > self.MAX_AVATAR_SIZE:
            raise ValidationError("La imagen supera el tamaño máximo de 2MB.")

        return avatar


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


class CustomPasswordResetForm(PasswordResetForm):
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
