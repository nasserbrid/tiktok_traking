# Architecture Technique Détaillée

## Table des matières

1. [Structure du projet](#structure-du-projet)
2. [Apps Django](#apps-django)
3. [Modèles de données](#modèles-de-données)
4. [Services et managers](#services-et-managers)
5. [WebSocket et temps réel](#websocket-et-temps-réel)
6. [Système de détection de lives](#système-de-détection-de-lives)
7. [Architecture IA](#architecture-ia)

---

## Structure du projet

### Arborescence complète

```
tiktok_traking/
├── core/                          # Configuration Django
│   ├── __init__.py
│   ├── settings.py               # Configuration principale
│   ├── urls.py                   # Routage URL principal
│   ├── wsgi.py                   # Configuration WSGI (HTTP)
│   ├── asgi.py                   # Configuration ASGI (WebSocket)
│   └── views.py                  # Vue home page
│
├── authentication/               # App authentification
│   ├── migrations/
│   ├── __init__.py
│   ├── models.py                 # Modèle User personnalisé
│   ├── views.py                  # Vues signup, logout
│   ├── forms.py                  # SignupForm
│   ├── validators.py             # Validateurs de mot de passe
│   └── urls.py                   # URLs auth
│
├── tracking/                     # App surveillance TikTok
│   ├── migrations/
│   ├── managers/
│   │   └── live_manager.py      # Gestion statut des lives
│   ├── services/
│   │   └── tiktok_live_service.py  # Détection via API TikTok
│   ├── __init__.py
│   ├── models.py                 # CompteTiktok, Live
│   ├── views.py                  # CRUD comptes, affichage lives
│   ├── forms.py                  # CompteTiktokForm
│   ├── tasks.py                  # Tâches Celery (commentées)
│   └── urls.py                   # URLs tracking
│
├── notifications/                # App notifications WebSocket
│   ├── migrations/
│   ├── __init__.py
│   ├── models.py                 # Modèle Notification
│   ├── views.py                  # Liste notifications
│   ├── consumers.py              # WebSocket consumer
│   ├── routing.py                # Routage WebSocket
│   ├── utils.py                  # Utilitaire envoi notifications
│   └── urls.py                   # URLs notifications
│
├── templates/                    # Templates HTML
│   ├── base.html                 # Template de base (navbar)
│   ├── authentication/
│   │   ├── login.html
│   │   ├── signup.html
│   │   └── password_reset_*.html
│   ├── tracking/
│   │   ├── liste_comptes.html   # Dashboard
│   │   ├── detail_compte.html   # Détail compte
│   │   ├── liste_lives.html     # Historique lives
│   │   └── ajouter_compte.html
│   └── notifications/
│       └── liste.html
│
├── static/                       # Fichiers statiques
│   ├── css/
│   │   └── styles.css           # Styles personnalisés
│   └── js/
│       └── websocket.js         # Client WebSocket
│
├── logs/                         # Logs application (gitignored)
├── venv/                         # Environnement virtuel Python
├── .env                          # Variables d'environnement
├── .gitignore
├── manage.py                     # Script Django
├── requirements.txt              # Dépendances Python
├── Procfile                      # Configuration Render
└── README.md
```

---

## Apps Django

### 1. App `core/` - Configuration principale

**Fichiers clés** :

#### `settings.py`

**Configuration de base** :
```python
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
SECRET_KEY = config('SECRET_KEY')
```

**Apps installées** :
```python
INSTALLED_APPS = [
    'daphne',  # ASGI server pour WebSocket
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps custom
    'authentication',
    'tracking',
    'notifications',
]
```

**Middleware** :
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Base de données** :
```python
# Utilise DATABASE_URL en production, sinon config locale
DATABASES = {
    'default': dj_database_url.config(
        default=f"postgresql://{config('DB_USER')}:{config('DB_PASSWORD')}"
                f"@{config('DB_HOST')}:{config('DB_PORT')}/{config('DB_NAME')}"
    )
}
```

**Channel Layers (WebSocket)** :
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config("REDIS_URL")],
        },
    },
}
```

**Celery (actuellement commenté)** :
```python
# CELERY_BROKER_URL = config("REDIS_URL")
# CELERY_RESULT_BACKEND = config("REDIS_URL")
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
```

**Static files** :
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**Email** :
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```

#### `asgi.py` - Configuration WebSocket

```python
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import notifications.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notifications.routing.websocket_urlpatterns
        )
    ),
})
```

**Explication** :
- `ProtocolTypeRouter` : Route HTTP et WebSocket
- `AuthMiddlewareStack` : Authentification pour WebSocket
- `URLRouter` : Routing WebSocket depuis `notifications/routing.py`

#### `views.py` - Page d'accueil

```python
@login_required(login_url='/auth/login/')
def home_page(request):
    comptes = CompteTiktok.objects.filter(user=request.user)

    # PROBLÈME : Détection synchrone sur chaque chargement de page
    for compte in comptes:
        live_detected = asyncio.run(is_live(compte.username))
        update_live_status(compte, live_detected)

    context = {'comptes': comptes}
    return render(request, 'tracking/liste_comptes.html', context)
```

**Problématique** : Cette approche bloque le rendu de la page pendant que `is_live()` interroge l'API TikTok pour chaque compte. Solution recommandée : utiliser Celery pour détection en background.

---

### 2. App `authentication/` - Gestion utilisateurs

#### Modèle `User`

```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ADMIN = 'ADMIN'
    USER = 'USER'

    ROLE_CHOICES = (
        (ADMIN, 'Administrateur'),
        (USER, 'Utilisateur'),
    )

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username
```

**Héritage** : Hérite de `AbstractUser` qui fournit :
- `username`, `email`, `password`
- `first_name`, `last_name`
- `is_active`, `is_staff`, `is_superuser`
- `date_joined`, `last_login`

**Champ personnalisé** : `role` pour différencier admins et utilisateurs

#### Formulaire `SignupForm`

```python
from django.contrib.auth.forms import UserCreationForm

class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'password1', 'password2']
```

**Validation** :
- Hérite des validateurs Django (longueur min, similarité, etc.)
- Validateur custom `ContainsLetterValidator` (au moins 1 lettre)

#### Vues

**`signup_page(request)`** :
```python
def signup_page(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Compte créé avec succès')
            return redirect('login')
    else:
        form = SignupForm()

    return render(request, 'authentication/signup.html', {'form': form})
```

**`CustomLogoutView`** :
```python
class CustomLogoutView(LogoutView):
    next_page = 'login'
```

#### URLs

```python
urlpatterns = [
    path('login/', LoginView.as_view(template_name='authentication/login.html'), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.signup_page, name='signup'),
    path('change-password/', PasswordChangeView.as_view(...), name='password_change'),
    path('password_reset/', PasswordResetView.as_view(...), name='password_reset'),
    # ... autres vues reset password
]
```

---

### 3. App `tracking/` - Surveillance TikTok

#### Modèles

**`CompteTiktok`** :

```python
class CompteTiktok(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comptes_tiktok'
    )
    username = models.CharField(max_length=100)
    url = models.URLField()
    date_creation = models.DateTimeField(auto_now_add=True)
    nb_followers = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'username')
        ordering = ['-date_creation']

    @property
    def en_live(self):
        """Retourne True si le compte a un live actif"""
        return self.lives.filter(statut='en_cours').exists()

    @property
    def statut_dynamique(self):
        """Retourne le statut actuel du compte"""
        if self.en_live:
            return 'En ligne'
        # Logique additionnelle pour 'Actif' ou 'Hors ligne'
        return 'Hors ligne'

    def __str__(self):
        return f"@{self.username}"
```

**Contrainte importante** : `unique_together = ('user', 'username')` empêche un utilisateur de suivre deux fois le même compte.

**`Live`** :

```python
class Live(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]

    compte = models.ForeignKey(
        CompteTiktok,
        on_delete=models.CASCADE,
        related_name='lives'
    )
    titre = models.CharField(max_length=255, blank=True)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    nb_spectateurs = models.PositiveIntegerField(default=0)
    statut = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default='en_cours'
    )

    class Meta:
        ordering = ['-date_debut']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Si nouveau live et statut='en_cours', envoyer notification
        if is_new and self.statut == 'en_cours':
            from notifications.utils import envoyer_notification_live
            envoyer_notification_live(self)

    def __str__(self):
        return f"Live {self.compte.username} - {self.date_debut}"
```

**Signal automatique** : Lors de la création d'un `Live` avec `statut='en_cours'`, une notification est automatiquement envoyée via WebSocket.

#### Services

**`tracking/services/tiktok_live_service.py`** :

```python
from TikTokLive import TikTokLiveClient
import logging

logger = logging.getLogger(__name__)

async def is_live(username: str) -> bool:
    """
    Vérifie si un compte TikTok est en live.

    Args:
        username: Username TikTok (avec ou sans @)

    Returns:
        bool: True si en live, False sinon
    """
    username = username.lstrip("@")
    client = TikTokLiveClient(unique_id=username)

    try:
        is_streaming = await client.is_live()
        return is_streaming
    except Exception as e:
        logger.error(f"Erreur détection live pour @{username}: {e}")
        return False
```

**Librairie utilisée** : TikTokLive v6.6.5
**Mode** : Asynchrone (async/await)
**Gestion d'erreurs** : Retourne `False` en cas d'exception

#### Managers

**`tracking/managers/live_manager.py`** :

```python
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def update_live_status(compte, live_detected: bool):
    """
    Met à jour le statut des lives pour un compte donné.

    Args:
        compte: Instance de CompteTiktok
        live_detected: True si live détecté, False sinon
    """
    from tracking.models import Live

    # Récupérer le live actif s'il existe
    live_actif = compte.lives.filter(statut='en_cours').first()

    if live_detected:
        # Si live détecté et aucun live actif, créer un nouveau Live
        if not live_actif:
            Live.objects.create(
                compte=compte,
                titre=f"Live de {compte.username}",
                statut='en_cours'
            )
            # La création déclenchera automatiquement la notification (save signal)
    else:
        # Si pas de live détecté mais un live actif existe, le terminer
        if live_actif:
            live_actif.statut = 'termine'
            live_actif.date_fin = timezone.now()
            live_actif.save()

            # Envoyer notification de fin via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "lives",
                {
                    "type": "live_notification",
                    "compte": compte.username,
                    "titre": "Live terminé",
                    "user_id": compte.user.id
                }
            )
```

**Logique** :
1. Live détecté + pas de live actif → Créer `Live` (déclenche notification)
2. Pas de live + live actif existe → Marquer `statut='termine'` + envoyer notification fin

#### Vues

**`liste_comptes(request)`** - Dashboard :
```python
@login_required
def liste_comptes(request):
    comptes = CompteTiktok.objects.filter(user=request.user)
    return render(request, 'tracking/liste_comptes.html', {'comptes': comptes})
```

**`ajouter_compte(request)`** :
```python
@login_required
def ajouter_compte(request):
    if request.method == 'POST':
        form = CompteTiktokForm(request.POST, user=request.user)
        if form.is_valid():
            compte = form.save(commit=False)
            compte.user = request.user
            compte.url = f"https://www.tiktok.com/@{compte.username}"
            compte.save()
            messages.success(request, f"Compte @{compte.username} ajouté")
            return redirect('liste_comptes')
    else:
        form = CompteTiktokForm(user=request.user)

    return render(request, 'tracking/ajouter_compte.html', {'form': form})
```

**Particularité** : L'URL est auto-générée à partir du username.

**`detail_compte(request, pk)`** :
```python
@login_required
def detail_compte(request, pk):
    compte = get_object_or_404(CompteTiktok, pk=pk, user=request.user)
    lives = compte.lives.all()  # Historique des lives

    return render(request, 'tracking/detail_compte.html', {
        'compte': compte,
        'lives': lives
    })
```

**`supprimer_compte(request, pk)`** :
```python
@login_required
def supprimer_compte(request, pk):
    compte = get_object_or_404(CompteTiktok, pk=pk, user=request.user)
    username = compte.username
    compte.delete()
    messages.success(request, f"Compte @{username} supprimé")
    return redirect('liste_comptes')
```

**`liste_lives(request)`** :
```python
@login_required
def liste_lives(request):
    # Tous les lives des comptes de l'utilisateur
    lives = Live.objects.filter(compte__user=request.user)

    return render(request, 'tracking/liste_lives.html', {'lives': lives})
```

#### Tâches Celery (actuellement désactivées)

**`tracking/tasks.py`** :

```python
from celery import shared_task
import asyncio

@shared_task
def check_all_accounts():
    """Vérifie tous les comptes TikTok pour détecter les lives"""
    from tracking.models import CompteTiktok
    from tracking.services.tiktok_live_service import is_live
    from tracking.managers.live_manager import update_live_status

    comptes = CompteTiktok.objects.all()

    for compte in comptes:
        live_detected = asyncio.run(is_live(compte.username))
        update_live_status(compte, live_detected)

@shared_task
def send_notification_async(live_id):
    """Envoie une notification de manière asynchrone"""
    from tracking.models import Live
    from notifications.utils import envoyer_notification_live

    try:
        live = Live.objects.get(pk=live_id)
        envoyer_notification_live(live)
    except Live.DoesNotExist:
        pass
```

**Configuration Beat (commentée dans settings.py)** :
```python
# from celery.schedules import crontab
#
# CELERY_BEAT_SCHEDULE = {
#     'check-lives-every-2-minutes': {
#         'task': 'tracking.tasks.check_all_accounts',
#         'schedule': 120.0,  # 2 minutes
#     },
# }
```

---

### 4. App `notifications/` - Notifications WebSocket

#### Modèle `Notification`

```python
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    live = models.ForeignKey(
        'tracking.Live',
        on_delete=models.CASCADE
    )
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return f"Notification pour {self.user.username} - {self.message}"
```

**Usage** : Stockage persistant des notifications pour historique.

#### Consumer WebSocket

**`notifications/consumers.py`** :

```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class LiveNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Appelé lors de la connexion WebSocket"""
        # Rejoindre le groupe "lives" (broadcast global)
        await self.channel_layer.group_add(
            "lives",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Appelé lors de la déconnexion"""
        await self.channel_layer.group_discard(
            "lives",
            self.channel_name
        )

    async def live_notification(self, event):
        """
        Handler pour les messages de type 'live_notification'.
        Appelé quand channel_layer.group_send() est utilisé.
        """
        # Envoyer le message au client WebSocket
        await self.send(text_data=json.dumps({
            "type": "live_notification",
            "compte": event["compte"],
            "titre": event["titre"],
            "user_id": event.get("user_id")
        }))
```

**Fonctionnement** :
1. Client se connecte → `connect()` → rejoint groupe "lives"
2. Backend appelle `channel_layer.group_send("lives", {...})`
3. Consumer reçoit message → `live_notification(event)`
4. Consumer envoie JSON au client via `self.send()`

#### Routing WebSocket

**`notifications/routing.py`** :

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/lives/$', consumers.LiveNotificationConsumer.as_asgi()),
]
```

**URL WebSocket** : `ws://domain/ws/lives/` (ou `wss://` en HTTPS)

#### Utilitaire d'envoi

**`notifications/utils.py`** :

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

def envoyer_notification_live(live):
    """
    Envoie une notification pour un nouveau live.

    Args:
        live: Instance de Live
    """
    # Créer la notification en base de données
    notification = Notification.objects.create(
        user=live.compte.user,
        live=live,
        message=f"Le compte @{live.compte.username} est en live : {live.titre}"
    )

    # Envoyer via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "lives",  # Nom du groupe
        {
            "type": "live_notification",  # Nom de la méthode dans le consumer
            "compte": live.compte.username,
            "titre": live.titre,
            "user_id": live.compte.user.id
        }
    )
```

**Double action** :
1. Sauvegarde en BDD (historique)
2. Broadcast WebSocket (temps réel)

#### Vue

**`notifications_list(request)`** :

```python
@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'notifications/liste.html', {
        'notifications': notifications
    })
```

---

## WebSocket et temps réel

### Architecture complète

```
┌─────────────────────┐
│   Django Backend    │
│                     │
│  live_manager.py    │
│         ↓           │
│  channel_layer.     │
│  group_send()       │
└─────────┬───────────┘
          │
          ↓ Redis
┌─────────────────────┐
│   Channel Layer     │
│   (Redis)           │
└─────────┬───────────┘
          │
          ↓ WebSocket
┌─────────────────────┐
│   LiveNotification  │
│   Consumer          │
│  (Channels)         │
└─────────┬───────────┘
          │
          ↓ WebSocket Protocol
┌─────────────────────┐
│   Client Browser    │
│   (JavaScript)      │
└─────────────────────┘
```

### Client JavaScript

**`static/js/websocket.js`** (exemple) :

```javascript
// Connexion WebSocket
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const wsUrl = protocol + window.location.host + '/ws/lives/';
const socket = new WebSocket(wsUrl);

// Événement : connexion établie
socket.onopen = function(e) {
    console.log('WebSocket connecté');
};

// Événement : message reçu
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    if (data.type === 'live_notification') {
        // Afficher notification
        showNotification(data.compte, data.titre);
    }
};

// Événement : erreur
socket.onerror = function(error) {
    console.error('Erreur WebSocket:', error);
};

// Événement : connexion fermée
socket.onclose = function(e) {
    console.log('WebSocket déconnecté');
    // Reconnexion automatique après 3s
    setTimeout(() => {
        location.reload();
    }, 3000);
};

function showNotification(compte, titre) {
    // Afficher toast/alert
    alert(`@${compte} est en live : ${titre}`);
}
```

**Inclusion dans template** :

```django
{% load static %}
<script src="{% static 'js/websocket.js' %}"></script>
```

---

## Système de détection de lives

### Flux complet

```
┌──────────────────────────────────────────────────┐
│                  DÉMARRAGE                        │
└────────────────────┬─────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │ Page Dashboard chargée │
        │  (ou Celery Beat task) │
        └────────────┬───────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │ Pour chaque compte :   │
        │ is_live(username)      │
        └────────────┬───────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ↓                     ↓
    ┌─────────┐         ┌─────────────┐
    │ True    │         │ False       │
    └────┬────┘         └─────┬───────┘
         │                    │
         ↓                    ↓
 ┌───────────────┐    ┌──────────────────┐
 │ Live actif ?  │    │ Live actif ?     │
 └───┬───────────┘    └────┬─────────────┘
     │                     │
   Non│                  Oui│
     │                     │
     ↓                     ↓
┌─────────────────┐  ┌──────────────────┐
│ Créer Live      │  │ Marquer 'termine'│
│ statut='en_cours│  │ date_fin=now()   │
└────┬────────────┘  └────┬─────────────┘
     │                    │
     ↓                    ↓
┌─────────────────┐  ┌──────────────────┐
│ save() signal → │  │ WebSocket send   │
│ Notification    │  │ "Live terminé"   │
└────┬────────────┘  └──────────────────┘
     │
     ↓
┌─────────────────┐
│ WebSocket send  │
│ "Nouveau live"  │
└─────────────────┘
```

### Méthodes de détection

#### 1. Détection synchrone (actuelle)

**Où** : `core/views.py` → `home_page()`

**Problème** :
- Bloque le rendu de la page
- Requête API pour chaque compte à chaque chargement
- Pas scalable (10 comptes = 10 requêtes API synchrones)

**Temps de réponse** :
- ~500ms par compte (latence API TikTok)
- 10 comptes = ~5 secondes de chargement

#### 2. Détection asynchrone (recommandée via Celery)

**Configuration** :

```python
# Dans settings.py
CELERY_BROKER_URL = config("REDIS_URL")
CELERY_RESULT_BACKEND = config("REDIS_URL")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-lives-every-2-minutes': {
        'task': 'tracking.tasks.check_all_accounts',
        'schedule': 120.0,  # Toutes les 2 minutes
    },
}
```

**Procfile** :

```
web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A core worker -l info
beat: celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Avantages** :
- Détection en arrière-plan
- Page charge instantanément
- Scalable (traitement parallèle possible)
- Fréquence configurable

---

## Architecture IA

### Vue d'ensemble

```
┌────────────────────────────────────────────────┐
│          DÉTECTION LIVE (Django)               │
└────────────────┬───────────────────────────────┘
                 │
                 ↓
    ┌────────────────────────┐
    │ Live détecté           │
    │ (statut='en_cours')    │
    └────────────┬───────────┘
                 │
                 ↓
┌────────────────────────────────────────────────┐
│   TRANSCRIPTION (transcript_ttt)               │
│                                                │
│   TikTokLiveTranscriber                        │
│   ↓                                            │
│   1. Récupération URL flux audio (API TikTok) │
│   2. Capture segments 15s (FFmpeg)            │
│   3. Transcription (Whisper)                  │
│   ↓                                            │
│   Callback: on_transcription(text, segment)   │
└────────────────┬───────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────┐
│   ANALYSE (transcript_ttt)                     │
│                                                │
│   analyze_text(text)                           │
│   ↓                                            │
│   1. Chargement prompt (template.yml)         │
│   2. Injection texte dans prompt              │
│   3. Appel Groq API (LLaMA 3.3 70B)           │
│   4. Parsing JSON réponse                     │
│   5. Calcul risque_score                      │
│   ↓                                            │
│   {categorie, viralite, discours_haineux,     │
│    cible, justification, risque_score}        │
└────────────────┬───────────────────────────────┘
                 │
                 ↓
    ┌────────────────────────┐
    │ risque_score > seuil ? │
    └────┬──────────────┬────┘
         │ Oui          │ Non
         ↓              ↓
┌─────────────────┐  ┌──────────────┐
│ ALERTE ADMIN    │  │ Log + Suite  │
│ + Option arrêt  │  │ transcription│
│ live            │  │              │
└─────────────────┘  └──────────────┘
```

### Composants détaillés

#### 1. TikTokLiveTranscriber

**Fichier** : `transcript/transcript.py`

**Classe principale** :

```python
class TikTokLiveTranscriber:
    def __init__(
        self,
        room_id: str,              # ID de la room TikTok
        model: str = "small",      # Modèle Whisper
        language: str = "fr",      # Langue
        duration: int = 15,        # Durée segment (secondes)
        unique_id: str = "",       # Username TikTok
        on_transcription: Callable = None,  # Callback transcription
        on_error: Callable = None,          # Callback erreur
        on_complete: Callable = None        # Callback fin
    )
```

**Méthodes principales** :

```python
def start(self) -> bool:
    """
    Démarre la transcription.

    Étapes :
    1. Chargement modèle Whisper
    2. Récupération URL flux via _get_live_url()
    3. Lancement thread transcription

    Returns:
        True si démarrage réussi, False sinon
    """

def _get_live_url(self, retry_count: int = 0) -> Optional[str]:
    """
    Récupère l'URL du flux audio TikTok.

    API : https://webcast.tiktok.com/webcast/room/info/?aid=1988&room_id={room_id}

    Parsing :
    response['data']['stream_url']['live_core_sdk_data']['pull_data']
            ['stream_data'] (JSON string)
            → ['data']['ao']['main']['flv']

    Gestion codes erreur :
    - 4001 : Live terminé
    - 5000, 4003 : Erreur temporaire → retry
    """

def _transcription_loop(self, stream_url: str) -> None:
    """
    Boucle principale de capture + transcription.

    Tant que is_running :
    1. _record_segment() → Enregistrement FFmpeg
    2. _transcribe_segment() dans un thread séparé
    3. Alternance FILE_A / FILE_B
    4. Refresh URL si expiration
    """

def _record_segment(self, stream_url: str, output: str, num: int) -> bool:
    """
    Capture audio avec FFmpeg.

    Commande :
    ffmpeg -y -t 15 -i {stream_url} -loglevel error {output_file}

    Timeout : 20s par défaut
    """

def _transcribe_segment(self, filename: str, segment_num: int) -> None:
    """
    Transcription d'un segment.

    1. Vérification fichier non vide
    2. self.model.transcribe(filename, language=self.language)
    3. Extraction texte
    4. Appel callback : on_transcription(text, segment_num, unique_id)
    5. Suppression fichier
    """

def stop(self) -> None:
    """Arrête la transcription proprement"""

def get_stats(self) -> Dict[str, Any]:
    """Retourne métriques (segments traités, taux succès, etc.)"""
```

**Métriques trackées** :

```python
class TranscriptionMetrics:
    total_segments: int             # Nombre total de segments
    successful_transcriptions: int  # Transcriptions réussies
    failed_transcriptions: int      # Échecs
    silent_segments: int            # Segments silencieux
    start_time: float               # Timestamp début

    def get_stats(self) -> dict:
        return {
            "total_segments": ...,
            "successful": ...,
            "failed": ...,
            "silent": ...,
            "elapsed_time": ...,
            "success_rate": "95.2%"
        }
```

#### 2. Analyseur de discours

**Fichier** : `analyse/analyzer.py`

```python
def analyze_text(text: str) -> dict:
    """
    Analyse un texte pour détecter discours haineux.

    Args:
        text: Texte transcrit

    Returns:
        {
            "categorie": str,
            "viralite": str,
            "discours_haineux": bool,
            "cible": str,
            "justification": str,
            "risque_score": float
        }
    """
    # 1. Charger prompt depuis template.yml
    prompt_template = load_prompt("text_moderation", "analysis_prompt")

    # 2. Injecter le texte
    prompt = prompt_template.replace("{{ text }}", text)

    # 3. Appel LLM
    raw_response = call_llm(prompt)

    # 4. Parser JSON
    data = json.loads(raw_response)

    # 5. Calculer score de risque
    score = 0.2  # Base
    if data["viralite"] == "moyenne":
        score += 0.3
    elif data["viralite"] == "forte":
        score += 0.5

    if data["discours_haineux"]:
        score += 0.4

    data["risque_score"] = min(score, 1.0)

    return data
```

**Client LLM** (`analyse/llm_client.py`) :

```python
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt: str) -> str:
    """
    Appelle l'API Groq avec LLaMA 3.3 70B.

    Modèle : llama-3.3-70b-versatile
    Température : 0.5 (équilibre créativité/stabilité)
    Max tokens : 1024
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_completion_tokens=1024
    )

    return completion.choices[0].message.content
```

**Template de prompt** (`analyse/template.yml`) :

```yaml
text_moderation:
  analysis_prompt: |
    Tu es un expert en analyse de discours sur les réseaux sociaux africains,
    avec une bonne connaissance des contextes sociaux et politiques du Burkina Faso.

    Analyse le texte suivant :

    """
    {{ text }}
    """

    Tâches :
    1. Classifie le texte dans une seule catégorie :
       - Neutre
       - Polémique
       - Potentiellement viral
       - Discours haineux

    2. Évalue le niveau de viralité :
       - faible
       - moyenne
       - forte

    3. Indique si le texte contient un discours haineux.

    4. Si oui, précise :
       - la cible (ethnie, religion, individu, groupe social, autre)
       - le type (insulte, stigmatisation, appel à la violence)

    Réponds STRICTEMENT au format JSON suivant :

    {
      "categorie": "",
      "viralite": "",
      "discours_haineux": true,
      "cible": "",
      "justification": ""
    }
```

**Contexte spécialisé** : Le prompt est adapté pour le contexte burkinabé et africain.

#### 3. Intégration avec Django

**Étapes d'intégration** :

1. **Installer dépendances** :
```bash
pip install openai-whisper torch ffmpeg-python groq pyyaml
```

2. **Copier modules** :
```
tracking/
├── services/
│   ├── tiktok_live_service.py  (existant)
│   ├── transcription_service.py  (nouveau)
│   └── analysis_service.py  (nouveau)
```

3. **Créer modèles** :
```python
# tracking/models.py

class Transcription(models.Model):
    live = models.ForeignKey(Live, on_delete=models.CASCADE, related_name='transcriptions')
    segment_number = models.PositiveIntegerField()
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['segment_number']

class AnalyseDiscours(models.Model):
    transcription = models.OneToOneField(Transcription, on_delete=models.CASCADE)
    categorie = models.CharField(max_length=50)
    viralite = models.CharField(max_length=20)
    discours_haineux = models.BooleanField(default=False)
    cible = models.CharField(max_length=100, blank=True)
    justification = models.TextField()
    risque_score = models.FloatField()
    date_analyse = models.DateTimeField(auto_now_add=True)
```

4. **Service de transcription** :
```python
# tracking/services/transcription_service.py

from transcript.transcript import TikTokLiveTranscriber
from analyse.analyzer import analyze_text
from tracking.models import Live, Transcription, AnalyseDiscours

def start_transcription(live: Live):
    """Démarre la transcription pour un live"""

    def handle_transcription(text: str, segment: int, unique_id: str):
        # Sauvegarder transcription
        trans = Transcription.objects.create(
            live=live,
            segment_number=segment,
            text=text
        )

        # Analyser le texte
        analysis = analyze_text(text)

        # Sauvegarder analyse
        AnalyseDiscours.objects.create(
            transcription=trans,
            categorie=analysis['categorie'],
            viralite=analysis['viralite'],
            discours_haineux=analysis['discours_haineux'],
            cible=analysis.get('cible', ''),
            justification=analysis['justification'],
            risque_score=analysis['risque_score']
        )

        # Si score de risque élevé, alerter
        if analysis['risque_score'] > 0.7:
            send_high_risk_alert(live, analysis)

    def handle_error(error: str):
        logger.error(f"Erreur transcription live {live.id}: {error}")

    def handle_complete(stats: dict):
        logger.info(f"Transcription terminée pour live {live.id}: {stats}")

    transcriber = TikTokLiveTranscriber(
        room_id=str(live.compte.tiktok_room_id),  # À ajouter au modèle
        model="small",
        language="fr",
        unique_id=live.compte.username,
        on_transcription=handle_transcription,
        on_error=handle_error,
        on_complete=handle_complete
    )

    transcriber.start()

    # Stocker transcriber pour pouvoir l'arrêter plus tard
    return transcriber
```

5. **Mise à jour live_manager.py** :
```python
# tracking/managers/live_manager.py

from tracking.services.transcription_service import start_transcription

# Dictionnaire pour tracker les transcribers actifs
active_transcribers = {}

def update_live_status(compte, live_detected: bool):
    live_actif = compte.lives.filter(statut='en_cours').first()

    if live_detected:
        if not live_actif:
            live = Live.objects.create(
                compte=compte,
                titre=f"Live de {compte.username}",
                statut='en_cours'
            )

            # Démarrer transcription
            transcriber = start_transcription(live)
            active_transcribers[live.id] = transcriber
    else:
        if live_actif:
            live_actif.statut = 'termine'
            live_actif.date_fin = timezone.now()
            live_actif.save()

            # Arrêter transcription
            if live_actif.id in active_transcribers:
                transcriber = active_transcribers[live_actif.id]
                transcriber.stop()
                del active_transcribers[live_actif.id]
```

---

## Configuration système requise

### Dépendances système

**FFmpeg** (pour capture audio) :
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Télécharger depuis https://ffmpeg.org/download.html
```

**CUDA** (optionnel, pour accélération GPU Whisper) :
```bash
# Si GPU NVIDIA disponible
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Variables d'environnement

**Nouvelles variables pour IA** :

```env
# Groq API
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

# Whisper
WHISPER_MODEL=small  # tiny, base, small, medium, large
WHISPER_LANGUAGE=fr

# Analyse
RISK_THRESHOLD=0.7  # Seuil d'alerte (0.0 - 1.0)
```

---

## Performance et optimisation

### Benchmarks estimés

**Transcription (Whisper small)** :
- CPU : ~3-5s par segment de 15s
- GPU : ~0.5-1s par segment de 15s

**Analyse (Groq LLaMA 3.3 70B)** :
- Latence API : ~500ms-2s par requête

**Détection live (TikTokLive API)** :
- Latence : ~300-800ms par compte

### Recommandations

1. **Utiliser GPU pour Whisper** si disponible (10x plus rapide)
2. **Limiter modèle Whisper** à "small" ou "base" pour temps réel
3. **Cacher résultats analyse** pour segments similaires
4. **Rate limiting** sur API Groq (quotas)
5. **Queue Celery** pour traitement asynchrone analyses

---

**Document généré le** : 2025-12-26
**Version** : 1.0
