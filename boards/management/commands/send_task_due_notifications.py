from django.core.management.base import BaseCommand
from django.utils import timezone

from boards.models import Task, UserProfile
from boards.utils import build_board_url
from boards.views import send_task_due_soon_email, send_task_overdue_email


# Expongo este comando para que pueda ejecutarse por cron y enviar avisos de vencimiento.
class Command(BaseCommand):
    help = "Envia notificaciones por vencimiento de tareas (próximas y vencidas)."

    def handle(self, *args, **options):
        # Tomo una ventana de 24h para avisos "por vencer" y separo también las vencidas.
        now = timezone.now()
        soon_limit = now + timezone.timedelta(hours=24)

        due_soon_qs = (
            Task.objects.filter(due_date__isnull=False)
            .filter(due_date__gt=now, due_date__lte=soon_limit)
            .filter(due_soon_notified_at__isnull=True)
            .select_related("task_list__board")
            .prefetch_related("assigned_to")
        )
        overdue_qs = (
            Task.objects.filter(due_date__isnull=False)
            .filter(due_date__lt=now)
            .filter(overdue_notified_at__isnull=True)
            .select_related("task_list__board")
            .prefetch_related("assigned_to")
        )

        due_soon_sent = 0
        overdue_sent = 0

        # Recorro tareas próximas y solo notifico a usuarios asignados con opt-in activo.
        for task in due_soon_qs:
            board_url = build_board_url(task.task_list.board_id)
            sent_any = False
            for user in task.assigned_to.exclude(email=""):
                profile, _ = UserProfile.objects.get_or_create(user=user)
                if not profile.notify_task_due:
                    continue
                send_task_due_soon_email(task, user, board_url)
                sent_any = True
                due_soon_sent += 1
            if sent_any:
                task.due_soon_notified_at = now
                task.save(update_fields=["due_soon_notified_at"])

        # Recorro tareas ya vencidas y marco timestamp para evitar duplicar avisos.
        for task in overdue_qs:
            board_url = build_board_url(task.task_list.board_id)
            sent_any = False
            for user in task.assigned_to.exclude(email=""):
                profile, _ = UserProfile.objects.get_or_create(user=user)
                if not profile.notify_task_due:
                    continue
                send_task_overdue_email(task, user, board_url)
                sent_any = True
                overdue_sent += 1
            if sent_any:
                task.overdue_notified_at = now
                task.save(update_fields=["overdue_notified_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Notificaciones enviadas. Próximas: {due_soon_sent}, Vencidas: {overdue_sent}"
            )
        )
