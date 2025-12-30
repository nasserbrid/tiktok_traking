# Utilise une image Python officielle légère avec Python 3.12
FROM python:3.12-slim-bookworm

# Évite la génération de fichiers .pyc et active le flushing des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Répertoire de travail
WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip
RUN pip install --no-cache-dir --upgrade pip


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du projet
COPY . .

# Création des dossiers nécessaires (logs, etc.) mentionnés dans transcriber.py
RUN mkdir -p logs

# Port exposé par Django (ou Gunicorn)
EXPOSE 8000

# Commande par défaut (ajuste selon si tu veux lancer le serveur ou un worker Celery)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
