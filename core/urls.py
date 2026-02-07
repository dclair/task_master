from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Rutas de autenticación de Django (login, logout, password management)
    path("accounts/", include("django.contrib.auth.urls")),
    # Nuestras rutas de la app boards
    path("boards/", include("boards.urls")),
    # Redirigir la raíz a los tableros
    path("", RedirectView.as_view(url="/boards/", permanent=True)),
]
