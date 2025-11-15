import os
from celery import Celery

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('tiktok_tracking')

# Charge la config depuis Django settings avec le préfixe CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvre automatiquement les tâches dans tasks.py de chaque app
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')