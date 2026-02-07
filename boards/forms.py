from django import forms
from .models import Board, TaskList, Task


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
