from django.conf import settings
from django.urls import reverse


def get_list_status_key(title):
    text = (title or "").lower()
    if "por hacer" in text or "pendiente" in text:
        return "todo"
    if "proceso" in text or "curso" in text:
        return "doing"
    if (
        "hecho" in text
        or "termin" in text
        or "complet" in text
        or "finaliz" in text
        or "done" in text
    ):
        return "done"
    return "other"


def get_list_status_label(title):
    key = get_list_status_key(title)
    return {
        "todo": "Por hacer",
        "doing": "En proceso",
        "done": "Completadas",
    }.get(key, title)


def build_board_url(board_id, request=None):
    path = reverse("boards:board_detail", args=[board_id])
    if request is not None:
        return request.build_absolute_uri(path)
    base = getattr(settings, "SITE_URL", "").rstrip("/")
    if base:
        return f"{base}{path}"
    return path
