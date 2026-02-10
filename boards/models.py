from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_boards"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class BoardMembership(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("editor", "Editor"),
        ("viewer", "Viewer"),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="board_memberships")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="viewer")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("board", "user")

    def __str__(self):
        return f"{self.user.username} - {self.board.title} ({self.role})"


class BoardInvite(models.Model):
    ROLE_CHOICES = BoardMembership.ROLE_CHOICES

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="invites")
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="viewer")
    invited_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_invites"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("board", "username", "email")

    def __str__(self):
        return f"{self.email} - {self.board.title} ({self.role})"


class TaskList(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="lists")
    title = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)  # Para el orden visual

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"{self.title} ({self.board.title})"


# Modelo para etiquetas (tags) de tareas
class Tag(models.Model):
    # Colores pastel elegantes
    COLOR_CHOICES = [
        ("#d1e7dd", "Verde"),
        ("#f8d7da", "Rojo"),
        ("#fff3cd", "Amarillo"),
        ("#cff4fc", "Azul"),
        ("#e2e3e5", "Gris"),
        ("#f3e5f5", "Morado"),
    ]
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, choices=COLOR_CHOICES, default="#cff4fc")

    def __str__(self):
        return self.name


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Baja"),
        ("medium", "Media"),
        ("high", "Alta"),
    ]

    task_list = models.ForeignKey(
        TaskList, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ManyToManyField(
        User, blank=True, related_name="assigned_tasks"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
    )
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    due_date = models.DateTimeField(null=True, blank=True)
    due_soon_notified_at = models.DateTimeField(null=True, blank=True)
    overdue_notified_at = models.DateTimeField(null=True, blank=True)
    due_soon_notified_at = models.DateTimeField(null=True, blank=True)
    overdue_notified_at = models.DateTimeField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="tasks")

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    notify_task_assigned = models.BooleanField(default=True)
    notify_task_due = models.BooleanField(default=True)
    notify_task_status = models.BooleanField(default=True)
    notify_task_due = models.BooleanField(default=True)
    notify_task_status = models.BooleanField(default=True)

    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return "/static/img/taskmaster.png"

    def __str__(self):
        return self.user.username


class Activity(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=120)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} ({self.board.title})"
