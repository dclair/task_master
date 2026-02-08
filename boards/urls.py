from django.urls import path
from . import views

app_name = "boards"

urlpatterns = [
    path("", views.BoardListView.as_view(), name="board_list"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("create/", views.BoardCreateView.as_view(), name="board_create"),
    path("<int:pk>/", views.BoardDetailView.as_view(), name="board_detail"),
    path("board/<int:board_id>/add-list/", views.add_list, name="add_list"),
    path("list/<int:list_id>/add-task/", views.add_task, name="add_task"),
    path("list/<int:list_id>/delete/", views.delete_list, name="delete_list"),
    path("task/<int:task_id>/delete/", views.delete_task, name="delete_task"),
    path("task/move/", views.move_task, name="move_task"),
]
