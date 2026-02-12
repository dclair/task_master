from django.contrib import admin
from .models import Board, TaskList, Task, Tag, BoardMembership, UserProfile, Activity

# Registro entidades base para administrarlas desde Django admin.
admin.site.register(Board)
admin.site.register(TaskList)
admin.site.register(Task)

# Configuro como quiero ver membresias y roles por tablero en admin.
@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
    list_display = ("board", "user", "role", "created_at")
    list_filter = ("role", "board")
    search_fields = ("board__title", "user__username", "user__email")


# Configuro el perfil extendido del usuario (avatar y notificaciones).
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "avatar", "cookie_consent", "cookie_consent_updated_at")
    search_fields = ("user__username", "user__email")


# Configuro el log de actividad para auditoría funcional del tablero.
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("board", "user", "action", "created_at")
    list_filter = ("board", "action")
    search_fields = ("board__title", "user__username", "action", "details")


# Configuro el catálogo de etiquetas disponible en tareas.
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    # Muestro nombre y color directamente en el listado del admin.
    list_display = ("name", "color")
