# Task Master

Gestor de tareas estilo Trello con tableros, listas, tareas movibles, etiquetas, prioridades, usuarios y colaboración por roles.

## Funcionalidades

- Registro, login y logout.
- Activación de cuenta por email con expiración y reenvío.
- Restablecimiento de contraseña con emails personalizados.
- Tableros y listas con orden visual y drag & drop (SortableJS).
- Tareas con prioridad, etiquetas, fecha límite, descripción.
- Asignación de tareas a múltiples usuarios (solo miembros del tablero).
- Progreso general del tablero.
- Búsqueda y filtros por tags y prioridad.
- Filtro por estado (por hacer / en proceso / completadas).
- Paginación por lista (10 tareas por página).
- Exportación de tareas a CSV y JSON (owner/editor).
- Auditoría de actividad (creación, edición, movimientos, membresías, invitaciones) con paginación.
- Panel lateral de actividad con redimensionado y colapsable en móvil.
- Filtros colapsables en móvil y contadores por estado.
- Gestión de miembros y roles (owner/editor/viewer).
- Invitaciones por email con aceptación y caducidad.
- Perfil de usuario con avatar, bio y preferencias de notificaciones.
- Notificaciones por email cuando te asignan una tarea (opt‑in por perfil).
- Notificaciones por email de vencimiento (próximas y vencidas) y cambio de estado.
- Cambio de email con verificación por enlace.

## Roles

- **Owner**: control total (gestión de miembros, invitaciones, editar).
- **Editor**: puede crear/editar/mover tareas y listas.
- **Viewer**: solo lectura.

## Emails

Plantillas HTML con logo embebido:
- Activación de cuenta
- Confirmación de activación
- Invitaciones
- Asignación de tareas
- Vencimiento de tareas (próximas y vencidas)
- Cambio de estado
- Confirmación de cambio de email
- Reset de contraseña

## Tecnologías

- Django
- SQLite (por defecto)
- Bootstrap 5 + Bootstrap Icons
- SortableJS
- SMTP (Gmail en dev)

## Instalación rápida

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
env/bin/python manage.py migrate
env/bin/python manage.py runserver
```

## Diagrama de modelos

```mermaid
erDiagram
    USER ||--o{ BOARD : owns
    BOARD ||--o{ TASKLIST : has
    TASKLIST ||--o{ TASK : has
    TASK }o--o{ TAG : tags
    USER ||--o{ USERPROFILE : has
    BOARD ||--o{ BOARDMEMBERSHIP : members
    USER ||--o{ BOARDMEMBERSHIP : role
    BOARD ||--o{ BOARDINVITE : invites
    USER ||--o{ BOARDINVITE : invited_by
    BOARD ||--o{ ACTIVITY : activity
    USER ||--o{ ACTIVITY : actor
    TASK }o--o{ USER : assigned_to
```

## Diagrama de flujo (registro, activación e invitaciones)

```mermaid
flowchart TD
    A[Usuario se registra] --> B[Cuenta creada: is_active = false]
    B --> C[Email activación]
    C --> D[Usuario activa]
    D --> E[Cuenta activa]
    E --> F[Login]

    G[Owner envía invitación] --> H[Email invitación]
    H --> I{Usuario tiene cuenta?}
    I -- No --> J[Registro + activación]
    I -- Sí --> K[Login]
    J --> L[Abrir enlace invitación]
    K --> L
    L --> M[Invitación aceptada]
    M --> N[Miembro del tablero]
```

## Variables de entorno (.env)

```ini
EMAIL_USER=tu_correo@gmail.com
EMAIL_PASS=tu_app_password
SITE_URL=https://tudominio.com
```

## Notificaciones por vencimiento

Se envían con un comando programable:

```bash
python manage.py send_task_due_notifications
```

Recomendado: ejecutar cada hora con cron.

## Notas de UI

- Panel de actividad ajustable (drag) y colapsable en móvil.
- Columnas kanban optimizadas para ver más de 3 en pantalla.
- Botón de "Añadir tarea" compacto y centrado.

## Despliegue (producción)

1. Configura `DEBUG=False` y `ALLOWED_HOSTS`.
2. Usa una base de datos robusta (PostgreSQL recomendado).
3. Configura `STATIC_ROOT` y ejecuta:
   ```bash
   env/bin/python manage.py collectstatic
   ```
4. Configura SMTP real (o servicio como SendGrid).
5. Sirve con Gunicorn/Uvicorn y un proxy (Nginx/Apache).

Ejemplo Gunicorn:
```bash
env/bin/gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

## Rutas útiles

- `/boards/` lista de tableros
- `/boards/<id>/` detalle del tablero
- `/boards/profile/` perfil
- `/accounts/login/`
- `/accounts/password_reset/`

## Exportación

- CSV: `/boards/<id>/export/csv/`
- JSON: `/boards/<id>/export/json/`
- Actividad: `/boards/<id>/export/activity/`

## Notas

- Los envíos de email requieren SMTP válido.
- Las invitaciones caducan a los 7 días.
- Activación de cuenta caduca a las 24 horas.
