#!/usr/bin/env bash
set -e  # Detener si algún comando falla

# Instala dependencias
pip install -r requirements.txt

# Recoge archivos estáticos
python3 manage.py collectstatic --noinput

# Aplica migraciones
python3 manage.py migrate
