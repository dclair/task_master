from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from boards import views as board_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", board_views.CustomLoginView.as_view(), name="login"),
    path("accounts/resend-activation/", board_views.ResendActivationView.as_view(), name="resend_activation"),
    # Rutas de autenticación de Django (login, logout, password management)
    path("accounts/", include("django.contrib.auth.urls")),
    # Nuestras rutas de la app boards
    path("boards/", include("boards.urls")),
    # Redirigir la raíz a los tableros
    path("", RedirectView.as_view(url="/boards/", permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
