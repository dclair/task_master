from django.contrib import admin
from .models import Board, TaskList, Task, Tag

admin.site.register(Board)
admin.site.register(TaskList)
admin.site.register(Task)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    # Esto hará que veas el nombre y el color directamente en la lista del admin
    list_display = ("name", "color")
