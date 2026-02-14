from pathlib import Path
import os  # Uso os para facilitar carga de rutas y variables de entorno.
from django.contrib.messages import constants as messages
import dj_database_url


# Construyo rutas base del proyecto a partir de BASE_DIR.
BASE_DIR = Path(__file__).resolve().parent.parent


def load_env(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_env(BASE_DIR / ".env")


# Mantengo esta configuración pensada para desarrollo, no para producción.
# Referencia: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# En producción debo proteger SECRET_KEY y gestionarla por entorno.
SECRET_KEY = "django-insecure-@j_p^q%1!o1_a%qpg1cfgz83+7!-xnyo_b7&8py@72rim8m4^n"

# En producción debo desactivar DEBUG.
DEBUG = False

ALLOWED_HOSTS = [".onrender.com"]


# Defino aquí las aplicaciones instaladas.

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "boards",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Indico que Django busque plantillas tambien en la carpeta global templates.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Defino la base de datos por defecto.
# Referencia: https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {"default": dj_database_url.config(default=os.getenv("DATABASE_URL"))}


# Defino validadores de contraseña.
# Referencia: https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Defino idioma y configuración de internacionalización.
# Referencia: https://docs.djangoproject.com/en/4.2/topics/i18n/

# Ajusto idioma a español y mantengo zona horaria configurada.
LANGUAGE_CODE = "es-es"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Defino archivos estaticos (CSS, JavaScript e imágenes).
# Referencia: https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# defino carpeta raiz de archivos estaticos
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Declaro carpeta global de estaticos.
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
# Repito STATICFILES_DIRS para asegurar deteccion de carpeta static global.
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Defino archivos subidos por usuario (media).
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Defino el tipo de clave primaria por defecto.
# Referencia: https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuro redirecciones de autenticación.
LOGIN_REDIRECT_URL = "boards:board_list"
LOGOUT_REDIRECT_URL = "login"

# Configuro expiración del token de activación (segundos).
ACTIVATION_TOKEN_TIMEOUT = 60 * 60 * 24  # 24 horas

# Configuro expiración del token de invitación (segundos).
INVITE_TOKEN_TIMEOUT = 60 * 60 * 24 * 7  # 7 días

# Defino el correo remitente para emails salientes.
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_USER")

# Defino el correo de contacto que recibe mensajes.
CONTACT_EMAIL = os.getenv("EMAIL_USER")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_USER")
SERVER_EMAIL = os.getenv("EMAIL_USER")
# Configuro servidor SMTP de Gmail.
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Cargo credenciales SMTP desde variables de entorno.
EMAIL_HOST_USER = os.getenv("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_PASS"
)  # Uso la variable EMAIL_PASS desde el entorno.
