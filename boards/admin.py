from django.contrib import admin
from .models import Board, TaskList, Task, Tag, BoardMembership, UserProfile, Activity

admin.site.register(Board)
admin.site.register(TaskList)
admin.site.register(Task)
@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
    list_display = ("board", "user", "role", "created_at")
    list_filter = ("role", "board")
    search_fields = ("board__title", "user__username", "user__email")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "avatar")
    search_fields = ("user__username", "user__email")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("board", "user", "action", "created_at")
    list_filter = ("board", "action")
    search_fields = ("board__title", "user__username", "action", "details")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    # Esto hará que veas el nombre y el color directamente en la lista del admin
    list_display = ("name", "color")
