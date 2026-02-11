from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from boards import views as board_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", board_views.CustomLoginView.as_view(), name="login"),
    path("accounts/resend-activation/", board_views.ResendActivationView.as_view(), name="resend_activation"),
    path("accounts/password_reset/", board_views.CustomPasswordResetView.as_view(), name="password_reset"),
    path("accounts/password_reset/done/", board_views.CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("accounts/reset/<uidb64>/<token>/", board_views.CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("accounts/reset/done/", board_views.CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("accounts/cookie-consent/", board_views.cookie_consent_preference, name="cookie_consent_preference"),
    # Rutas de autenticación de Django (login, logout, password management)
    path("accounts/", include("django.contrib.auth.urls")),
    # Nuestras rutas de la app boards
    path("boards/", include("boards.urls")),
    # Páginas legales
    path("legal/aviso-legal/", board_views.legal_notice, name="legal_notice"),
    path("legal/privacidad/", board_views.privacy_policy, name="privacy_policy"),
    path("legal/cookies/", board_views.cookies_policy, name="cookies_policy"),
    # Home pública
    path("", board_views.public_home, name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
