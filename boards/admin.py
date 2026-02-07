from django.contrib import admin
from .models import Board, TaskList, Task

admin.site.register(Board)
admin.site.register(TaskList)
admin.site.register(Task)
