from django.conf import settings
from django.urls import reverse


# Normaliza un título de lista a una clave de estado usada por UI y notificaciones.
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


# Etiqueta legible para cada estado interno.
def get_list_status_label(title):
    key = get_list_status_key(title)
    return {
        "todo": "Por hacer",
        "doing": "En proceso",
        "done": "Completadas",
    }.get(key, title)


# Construye URL absoluta/relativa al tablero según exista request o SITE_URL.
def build_board_url(board_id, request=None):
    path = reverse("boards:board_detail", args=[board_id])
    if request is not None:
        return request.build_absolute_uri(path)
    base = getattr(settings, "SITE_URL", "").rstrip("/")
    if base:
        return f"{base}{path}"
    return path
