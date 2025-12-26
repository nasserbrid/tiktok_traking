# Guide d'Intégration de la Solution IA

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Prérequis](#prérequis)
3. [Installation](#installation)
4. [Intégration étape par étape](#intégration-étape-par-étape)
5. [Configuration](#configuration)
6. [Tests](#tests)
7. [Déploiement](#déploiement)
8. [Troubleshooting](#troubleshooting)

---

## Vue d'ensemble

Cette documentation décrit le processus complet d'intégration de la solution IA (transcription + analyse) développée par votre associé dans l'application Django TikTok Tracking existante.

### Objectifs de l'intégration

- ✅ Transcription automatique des lives TikTok en temps réel
- ✅ Analyse de discours pour détecter contenus haineux
- ✅ Alertes automatiques basées sur score de risque
- ✅ Interface de modération pour administrateurs
- ✅ Stockage et consultation de l'historique

### Architecture post-intégration

```
Live TikTok détecté
    ↓
TikTokLiveTranscriber (transcription audio)
    ↓
Transcription stockée en BDD
    ↓
Analyse via Groq LLM
    ↓
AnalyseDiscours stockée en BDD
    ↓
Si risque_score > seuil → Alerte admin
    ↓
Admin peut arrêter le live
```

---

## Prérequis

### 1. Système

**FFmpeg** (requis pour capture audio) :

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Télécharger depuis https://ffmpeg.org/download.html
# Ajouter au PATH système
```

**Vérification** :
```bash
ffmpeg -version
```

### 2. Python

**Version requise** : Python 3.10+

**Vérification** :
```bash
python --version
```

### 3. Services externes

**Groq API Key** :
1. Créer un compte sur https://console.groq.com
2. Générer une API key
3. Copier la clé (format : `gsk_...`)

### 4. Application Django existante

- Application TikTok Tracking fonctionnelle
- PostgreSQL configuré
- Redis configuré (pour Celery)
- Environnement virtuel activé

---

## Installation

### Étape 1 : Cloner le repository IA

```bash
# Depuis la racine du projet tiktok_traking
cd ..
git clone https://github.com/ohamjoseph/transcript_ttt.git
```

### Étape 2 : Installer les dépendances IA

**Ajouter au `requirements.txt`** :

```txt
# IA - Transcription et Analyse
openai-whisper==20250625
torch==2.9.1
triton==3.5.1
ffmpeg-python==0.2.0
groq==0.15.0
pyyaml==6.0.2

# Dépendances Whisper
tiktoken==0.12.0
tqdm==4.67.1
numpy==2.3.5
numba==0.62.1
```

**Installer** :

```bash
cd tiktok_traking
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

**Note** : L'installation de Whisper peut prendre 5-10 minutes (modèles volumineux).

### Étape 3 : Copier les modules IA

**Structure cible** :

```
tiktok_traking/
├── tracking/
│   ├── ai/                    # Nouveau dossier
│   │   ├── __init__.py
│   │   ├── transcript/
│   │   │   ├── __init__.py
│   │   │   └── transcriber.py
│   │   └── analyse/
│   │       ├── __init__.py
│   │       ├── analyzer.py
│   │       ├── llm_client.py
│   │       ├── utils.py
│   │       └── template.yml
```

**Commandes** :

```bash
# Créer structure
mkdir -p tracking/ai/transcript
mkdir -p tracking/ai/analyse

# Copier les fichiers
cp ../transcript_ttt/transcript/transcript.py tracking/ai/transcript/transcriber.py
cp ../transcript_ttt/analyse/analyzer.py tracking/ai/analyse/
cp ../transcript_ttt/analyse/llm_client.py tracking/ai/analyse/
cp ../transcript_ttt/analyse/utils.py tracking/ai/analyse/
cp ../transcript_ttt/analyse/template.yml tracking/ai/analyse/

# Créer __init__.py
touch tracking/ai/__init__.py
touch tracking/ai/transcript/__init__.py
touch tracking/ai/analyse/__init__.py
```

### Étape 4 : Adapter les imports

**Modifier `tracking/ai/transcript/transcriber.py`** :

Remplacer :
```python
# Ligne ~8
from analyse.analyzer import analyze_text
from transcript.transcript import TikTokLiveTranscriber
```

Par :
```python
# Imports relatifs
from tracking.ai.analyse.analyzer import analyze_text
```

**Modifier `tracking/ai/analyse/analyzer.py`** :

Remplacer :
```python
# Lignes 2-3
from .llm_client import call_llm
from .utils import load_prompt
```

Par :
```python
from tracking.ai.analyse.llm_client import call_llm
from tracking.ai.analyse.utils import load_prompt
```

**Modifier `tracking/ai/analyse/utils.py`** :

Remplacer :
```python
# Ligne 4
PROMPT_PATH = Path(__file__).parent / "template.yml"
```

Par :
```python
from django.conf import settings
PROMPT_PATH = settings.BASE_DIR / "tracking" / "ai" / "analyse" / "template.yml"
```

---

## Intégration étape par étape

### Étape 5 : Créer les nouveaux modèles

**Fichier** : `tracking/models.py`

**Ajouter** :

```python
class Transcription(models.Model):
    """Segment de transcription d'un live"""
    live = models.ForeignKey(
        Live,
        on_delete=models.CASCADE,
        related_name='transcriptions'
    )
    segment_number = models.PositiveIntegerField(
        help_text="Numéro du segment (ordre chronologique)"
    )
    text = models.TextField(
        help_text="Texte transcrit du segment audio"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Horodatage de la transcription"
    )

    class Meta:
        ordering = ['segment_number']
        unique_together = ('live', 'segment_number')

    def __str__(self):
        return f"Segment {self.segment_number} - Live {self.live.id}"


class AnalyseDiscours(models.Model):
    """Analyse de discours d'une transcription"""

    CATEGORIE_CHOICES = [
        ('neutre', 'Neutre'),
        ('polemique', 'Polémique'),
        ('viral', 'Potentiellement viral'),
        ('haineux', 'Discours haineux'),
    ]

    VIRALITE_CHOICES = [
        ('faible', 'Faible'),
        ('moyenne', 'Moyenne'),
        ('forte', 'Forte'),
    ]

    transcription = models.OneToOneField(
        Transcription,
        on_delete=models.CASCADE,
        related_name='analyse'
    )
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES
    )
    viralite = models.CharField(
        max_length=10,
        choices=VIRALITE_CHOICES
    )
    discours_haineux = models.BooleanField(
        default=False,
        help_text="Indique si un discours haineux a été détecté"
    )
    cible = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cible du discours haineux (si détecté)"
    )
    justification = models.TextField(
        help_text="Explication de l'analyse"
    )
    risque_score = models.FloatField(
        help_text="Score de risque (0.0 à 1.0)"
    )
    date_analyse = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Analyse de discours"
        verbose_name_plural = "Analyses de discours"
        ordering = ['-risque_score', '-date_analyse']

    def __str__(self):
        return f"Analyse {self.transcription} - Score: {self.risque_score}"

    @property
    def niveau_risque(self):
        """Retourne le niveau de risque textuel"""
        if self.risque_score >= 0.7:
            return "Élevé"
        elif self.risque_score >= 0.4:
            return "Moyen"
        else:
            return "Faible"


class AlerteModeration(models.Model):
    """Alerte générée pour modération"""

    STATUT_CHOICES = [
        ('pending', 'En attente'),
        ('reviewed', 'Examinée'),
        ('action_taken', 'Action effectuée'),
        ('dismissed', 'Ignorée'),
    ]

    analyse = models.ForeignKey(
        AnalyseDiscours,
        on_delete=models.CASCADE,
        related_name='alertes'
    )
    admin_notifie = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='alertes_recues'
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='pending'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    action_effectuee = models.TextField(
        blank=True,
        help_text="Description de l'action prise"
    )
    traite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_traitees'
    )

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Alerte de modération"
        verbose_name_plural = "Alertes de modération"

    def __str__(self):
        return f"Alerte {self.id} - {self.statut} - Risque: {self.analyse.risque_score}"
```

**Créer les migrations** :

```bash
python manage.py makemigrations tracking
python manage.py migrate
```

### Étape 6 : Créer le service de transcription

**Fichier** : `tracking/services/transcription_service.py`

```python
import logging
from typing import Dict, Optional
from tracking.ai.transcript.transcriber import TikTokLiveTranscriber
from tracking.ai.analyse.analyzer import analyze_text
from tracking.models import Live, Transcription, AnalyseDiscours, AlerteModeration
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

# Dictionnaire global pour tracker les transcribers actifs
active_transcribers: Dict[int, TikTokLiveTranscriber] = {}


class TranscriptionService:
    """Service de gestion de la transcription et analyse IA"""

    def __init__(self, live: Live):
        self.live = live
        self.transcriber: Optional[TikTokLiveTranscriber] = None

    def start(self) -> bool:
        """
        Démarre la transcription pour le live.

        Returns:
            bool: True si démarrage réussi, False sinon
        """
        if self.live.id in active_transcribers:
            logger.warning(f"Transcription déjà active pour live {self.live.id}")
            return False

        try:
            # Récupérer le room_id depuis l'API TikTok
            room_id = self._get_room_id()
            if not room_id:
                logger.error(f"Impossible de récupérer room_id pour {self.live.compte.username}")
                return False

            # Créer le transcriber
            self.transcriber = TikTokLiveTranscriber(
                room_id=room_id,
                model=getattr(settings, 'WHISPER_MODEL', 'small'),
                language=getattr(settings, 'WHISPER_LANGUAGE', 'fr'),
                duration=15,
                unique_id=self.live.compte.username,
                on_transcription=self._handle_transcription,
                on_error=self._handle_error,
                on_complete=self._handle_complete
            )

            # Démarrer
            if self.transcriber.start():
                active_transcribers[self.live.id] = self.transcriber
                logger.info(f"Transcription démarrée pour live {self.live.id}")
                return True
            else:
                logger.error(f"Échec démarrage transcription pour live {self.live.id}")
                return False

        except Exception as e:
            logger.error(f"Erreur démarrage transcription: {e}", exc_info=True)
            return False

    def stop(self) -> None:
        """Arrête la transcription pour le live"""
        if self.live.id in active_transcribers:
            transcriber = active_transcribers[self.live.id]
            transcriber.stop()
            del active_transcribers[self.live.id]
            logger.info(f"Transcription arrêtée pour live {self.live.id}")

    def _get_room_id(self) -> Optional[str]:
        """
        Récupère le room_id TikTok pour le compte.

        Note: Le room_id est disponible via TikTokLiveClient après connexion.
        Pour l'instant, on utilise un workaround avec l'API.
        """
        from TikTokLive import TikTokLiveClient
        import asyncio

        async def get_room():
            client = TikTokLiveClient(unique_id=self.live.compte.username)
            try:
                # Connexion pour récupérer room_id
                await client.start()
                room_id = client.room_id
                await client.disconnect()
                return str(room_id)
            except Exception as e:
                logger.error(f"Erreur récupération room_id: {e}")
                return None

        return asyncio.run(get_room())

    def _handle_transcription(self, text: str, segment: int, unique_id: str) -> None:
        """
        Callback appelé à chaque transcription.

        Args:
            text: Texte transcrit
            segment: Numéro du segment
            unique_id: Username TikTok
        """
        try:
            # 1. Sauvegarder la transcription
            transcription = Transcription.objects.create(
                live=self.live,
                segment_number=segment,
                text=text
            )
            logger.info(f"Transcription segment {segment} sauvegardée pour live {self.live.id}")

            # 2. Analyser le texte
            analysis_result = analyze_text(text)

            # 3. Sauvegarder l'analyse
            analyse = AnalyseDiscours.objects.create(
                transcription=transcription,
                categorie=self._map_categorie(analysis_result['categorie']),
                viralite=analysis_result['viralite'],
                discours_haineux=analysis_result['discours_haineux'],
                cible=analysis_result.get('cible', ''),
                justification=analysis_result['justification'],
                risque_score=analysis_result['risque_score']
            )
            logger.info(f"Analyse sauvegardée - Score: {analyse.risque_score}")

            # 4. Vérifier seuil de risque
            risk_threshold = getattr(settings, 'RISK_THRESHOLD', 0.7)
            if analyse.risque_score >= risk_threshold:
                self._create_alert(analyse)

            # 5. Envoyer notification WebSocket (optionnel)
            self._send_transcription_notification(transcription, analyse)

        except Exception as e:
            logger.error(f"Erreur traitement transcription: {e}", exc_info=True)

    def _handle_error(self, error: str) -> None:
        """Callback appelé en cas d'erreur"""
        logger.error(f"Erreur transcription live {self.live.id}: {error}")

    def _handle_complete(self, stats: dict) -> None:
        """Callback appelé à la fin de la transcription"""
        logger.info(f"Transcription terminée pour live {self.live.id}: {stats}")

    def _map_categorie(self, categorie_llm: str) -> str:
        """Map la catégorie LLM vers le choix du modèle"""
        mapping = {
            'Neutre': 'neutre',
            'Polémique': 'polemique',
            'Potentiellement viral': 'viral',
            'Discours haineux': 'haineux'
        }
        return mapping.get(categorie_llm, 'neutre')

    def _create_alert(self, analyse: AnalyseDiscours) -> None:
        """Crée une alerte de modération"""
        from authentication.models import User

        # Récupérer tous les admins
        admins = User.objects.filter(role=User.ADMIN)

        for admin in admins:
            alerte = AlerteModeration.objects.create(
                analyse=analyse,
                admin_notifie=admin,
                statut='pending'
            )
            logger.warning(f"Alerte créée pour admin {admin.username}: {alerte.id}")

        # Envoyer notification WebSocket aux admins
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "moderation",  # Groupe pour admins
            {
                "type": "moderation_alert",
                "alerte_id": alerte.id,
                "live_id": self.live.id,
                "compte": self.live.compte.username,
                "risque_score": analyse.risque_score,
                "categorie": analyse.categorie
            }
        )

    def _send_transcription_notification(self, transcription: Transcription, analyse: AnalyseDiscours) -> None:
        """Envoie une notification WebSocket pour la nouvelle transcription"""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"live_{self.live.id}",
            {
                "type": "new_transcription",
                "segment": transcription.segment_number,
                "text": transcription.text,
                "risque_score": analyse.risque_score,
                "categorie": analyse.categorie
            }
        )


def start_transcription_for_live(live: Live) -> bool:
    """
    Fonction utilitaire pour démarrer une transcription.

    Args:
        live: Instance de Live

    Returns:
        bool: True si succès, False sinon
    """
    service = TranscriptionService(live)
    return service.start()


def stop_transcription_for_live(live: Live) -> None:
    """
    Fonction utilitaire pour arrêter une transcription.

    Args:
        live: Instance de Live
    """
    service = TranscriptionService(live)
    service.stop()
```

### Étape 7 : Mettre à jour le Live Manager

**Fichier** : `tracking/managers/live_manager.py`

**Modifier** :

```python
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

def update_live_status(compte, live_detected: bool):
    """
    Met à jour le statut des lives pour un compte donné.

    Args:
        compte: Instance de CompteTiktok
        live_detected: True si live détecté, False sinon
    """
    from tracking.models import Live
    from tracking.services.transcription_service import (
        start_transcription_for_live,
        stop_transcription_for_live
    )

    # Récupérer le live actif s'il existe
    live_actif = compte.lives.filter(statut='en_cours').first()

    if live_detected:
        # Si live détecté et aucun live actif, créer un nouveau Live
        if not live_actif:
            live = Live.objects.create(
                compte=compte,
                titre=f"Live de {compte.username}",
                statut='en_cours'
            )
            logger.info(f"Nouveau live créé: {live.id}")

            # Démarrer la transcription
            success = start_transcription_for_live(live)
            if success:
                logger.info(f"Transcription démarrée pour live {live.id}")
            else:
                logger.error(f"Échec démarrage transcription pour live {live.id}")

            # La création déclenchera automatiquement la notification (save signal)
    else:
        # Si pas de live détecté mais un live actif existe, le terminer
        if live_actif:
            # Arrêter la transcription
            stop_transcription_for_live(live_actif)

            live_actif.statut = 'termine'
            live_actif.date_fin = timezone.now()
            live_actif.save()

            logger.info(f"Live terminé: {live_actif.id}")

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

### Étape 8 : Créer les vues de modération

**Fichier** : `tracking/views.py`

**Ajouter** :

```python
from django.contrib.admin.views.decorators import staff_member_required
from tracking.models import AlerteModeration, AnalyseDiscours, Transcription
from django.utils import timezone

@login_required
@staff_member_required
def tableau_moderation(request):
    """Dashboard de modération pour les admins"""
    alertes_pending = AlerteModeration.objects.filter(
        statut='pending'
    ).select_related('analyse__transcription__live__compte')

    alertes_traitees = AlerteModeration.objects.exclude(
        statut='pending'
    ).select_related('analyse__transcription__live__compte')[:20]

    context = {
        'alertes_pending': alertes_pending,
        'alertes_traitees': alertes_traitees
    }

    return render(request, 'tracking/moderation/dashboard.html', context)


@login_required
@staff_member_required
def detail_alerte(request, alerte_id):
    """Détail d'une alerte de modération"""
    alerte = get_object_or_404(
        AlerteModeration.objects.select_related(
            'analyse__transcription__live__compte',
            'traite_par'
        ),
        pk=alerte_id
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'dismiss':
            alerte.statut = 'dismissed'
            alerte.traite_par = request.user
            alerte.date_traitement = timezone.now()
            alerte.action_effectuee = request.POST.get('notes', '')
            alerte.save()
            messages.success(request, "Alerte ignorée")

        elif action == 'review':
            alerte.statut = 'reviewed'
            alerte.traite_par = request.user
            alerte.date_traitement = timezone.now()
            alerte.action_effectuee = request.POST.get('notes', '')
            alerte.save()
            messages.success(request, "Alerte marquée comme examinée")

        elif action == 'stop_live':
            # TODO: Implémenter arrêt du live via API TikTok
            alerte.statut = 'action_taken'
            alerte.traite_par = request.user
            alerte.date_traitement = timezone.now()
            alerte.action_effectuee = "Live arrêté manuellement"
            alerte.save()
            messages.success(request, "Live arrêté avec succès")

        return redirect('detail_alerte', alerte_id=alerte.id)

    # Récupérer toutes les transcriptions du live
    transcriptions = Transcription.objects.filter(
        live=alerte.analyse.transcription.live
    ).select_related('analyse').order_by('segment_number')

    context = {
        'alerte': alerte,
        'transcriptions': transcriptions
    }

    return render(request, 'tracking/moderation/detail_alerte.html', context)


@login_required
def live_transcriptions(request, live_id):
    """Affichage des transcriptions d'un live"""
    live = get_object_or_404(Live, pk=live_id)

    # Vérifier que l'utilisateur a accès
    if live.compte.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden()

    transcriptions = live.transcriptions.select_related('analyse').all()

    context = {
        'live': live,
        'transcriptions': transcriptions
    }

    return render(request, 'tracking/live_transcriptions.html', context)
```

### Étape 9 : Ajouter les URLs

**Fichier** : `tracking/urls.py`

**Ajouter** :

```python
urlpatterns = [
    # URLs existantes...

    # Modération
    path('moderation/', views.tableau_moderation, name='tableau_moderation'),
    path('moderation/alerte/<int:alerte_id>/', views.detail_alerte, name='detail_alerte'),

    # Transcriptions
    path('live/<int:live_id>/transcriptions/', views.live_transcriptions, name='live_transcriptions'),
]
```

### Étape 10 : Créer les templates

**Template** : `templates/tracking/moderation/dashboard.html`

```django
{% extends 'base.html' %}

{% block title %}Modération{% endblock %}

{% block content %}
<div class="container mt-4">
    <h1>Tableau de modération</h1>

    <div class="row mt-4">
        <div class="col-md-12">
            <h3>Alertes en attente ({{ alertes_pending.count }})</h3>

            {% if alertes_pending %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Compte</th>
                                <th>Risque</th>
                                <th>Catégorie</th>
                                <th>Discours haineux</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for alerte in alertes_pending %}
                                <tr>
                                    <td>{{ alerte.date_creation|date:"d/m/Y H:i" }}</td>
                                    <td>@{{ alerte.analyse.transcription.live.compte.username }}</td>
                                    <td>
                                        <span class="badge {% if alerte.analyse.risque_score >= 0.7 %}bg-danger{% elif alerte.analyse.risque_score >= 0.4 %}bg-warning{% else %}bg-success{% endif %}">
                                            {{ alerte.analyse.risque_score|floatformat:2 }}
                                        </span>
                                    </td>
                                    <td>{{ alerte.analyse.get_categorie_display }}</td>
                                    <td>
                                        {% if alerte.analyse.discours_haineux %}
                                            <span class="badge bg-danger">Oui</span>
                                        {% else %}
                                            <span class="badge bg-success">Non</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <a href="{% url 'detail_alerte' alerte.id %}" class="btn btn-sm btn-primary">Examiner</a>
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <p class="text-muted">Aucune alerte en attente</p>
            {% endif %}
        </div>
    </div>

    <div class="row mt-4">
        <div class="col-md-12">
            <h3>Alertes traitées récentes</h3>

            {% if alertes_traitees %}
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Date traitement</th>
                                <th>Compte</th>
                                <th>Statut</th>
                                <th>Traité par</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for alerte in alertes_traitees %}
                                <tr>
                                    <td>{{ alerte.date_traitement|date:"d/m/Y H:i" }}</td>
                                    <td>@{{ alerte.analyse.transcription.live.compte.username }}</td>
                                    <td>{{ alerte.get_statut_display }}</td>
                                    <td>{{ alerte.traite_par.username }}</td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <p class="text-muted">Aucune alerte traitée</p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

**Template** : `templates/tracking/live_transcriptions.html`

```django
{% extends 'base.html' %}

{% block title %}Transcriptions - {{ live.compte.username }}{% endblock %}

{% block content %}
<div class="container mt-4">
    <h1>Transcriptions du live</h1>
    <p class="text-muted">Compte : @{{ live.compte.username }} | Début : {{ live.date_debut|date:"d/m/Y H:i" }}</p>

    <div class="row mt-4">
        {% for trans in transcriptions %}
            <div class="col-md-12 mb-3">
                <div class="card {% if trans.analyse.risque_score >= 0.7 %}border-danger{% elif trans.analyse.risque_score >= 0.4 %}border-warning{% endif %}">
                    <div class="card-header d-flex justify-content-between">
                        <span>Segment {{ trans.segment_number }}</span>
                        <span class="badge {% if trans.analyse.risque_score >= 0.7 %}bg-danger{% elif trans.analyse.risque_score >= 0.4 %}bg-warning{% else %}bg-success{% endif %}">
                            Risque: {{ trans.analyse.risque_score|floatformat:2 }}
                        </span>
                    </div>
                    <div class="card-body">
                        <p><strong>Transcription :</strong></p>
                        <blockquote class="blockquote">
                            {{ trans.text }}
                        </blockquote>

                        <hr>

                        <p><strong>Analyse :</strong></p>
                        <ul>
                            <li><strong>Catégorie :</strong> {{ trans.analyse.get_categorie_display }}</li>
                            <li><strong>Viralité :</strong> {{ trans.analyse.get_viralite_display }}</li>
                            <li><strong>Discours haineux :</strong> {{ trans.analyse.discours_haineux|yesno:"Oui,Non" }}</li>
                            {% if trans.analyse.cible %}
                                <li><strong>Cible :</strong> {{ trans.analyse.cible }}</li>
                            {% endif %}
                        </ul>

                        <p class="text-muted"><em>{{ trans.analyse.justification }}</em></p>
                    </div>
                    <div class="card-footer text-muted">
                        {{ trans.timestamp|date:"d/m/Y H:i:s" }}
                    </div>
                </div>
            </div>
        {% empty %}
            <p class="text-muted">Aucune transcription disponible</p>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

---

## Configuration

### Étape 11 : Variables d'environnement

**Fichier** : `.env`

**Ajouter** :

```env
# IA - Groq API
GROQ_API_KEY=gsk_votre_cle_api_ici

# Whisper Configuration
WHISPER_MODEL=small  # Options: tiny, base, small, medium, large
WHISPER_LANGUAGE=fr

# Modération
RISK_THRESHOLD=0.7  # Seuil d'alerte (0.0 à 1.0)
```

### Étape 12 : Configuration Django

**Fichier** : `core/settings.py`

**Ajouter** :

```python
# IA Configuration
WHISPER_MODEL = config('WHISPER_MODEL', default='small')
WHISPER_LANGUAGE = config('WHISPER_LANGUAGE', default='fr')
RISK_THRESHOLD = config('RISK_THRESHOLD', default=0.7, cast=float)
GROQ_API_KEY = config('GROQ_API_KEY')  # Requis

# Logging IA
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file_ai': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'ai.log',
        },
    },
    'loggers': {
        'tracking.ai': {
            'handlers': ['file_ai'],
            'level': 'INFO',
            'propagate': False,
        },
        'tracking.services': {
            'handlers': ['file_ai'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Créer dossier logs si inexistant
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
```

### Étape 13 : Admin Django

**Fichier** : `tracking/admin.py`

**Ajouter** :

```python
from django.contrib import admin
from .models import CompteTiktok, Live, Transcription, AnalyseDiscours, AlerteModeration

@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ('live', 'segment_number', 'timestamp', 'text_preview')
    list_filter = ('live__compte__username', 'timestamp')
    search_fields = ('text',)

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Aperçu'


@admin.register(AnalyseDiscours)
class AnalyseDiscoursAdmin(admin.ModelAdmin):
    list_display = ('transcription', 'categorie', 'viralite', 'discours_haineux', 'risque_score', 'niveau_risque')
    list_filter = ('categorie', 'viralite', 'discours_haineux', 'date_analyse')
    search_fields = ('justification', 'cible')
    readonly_fields = ('date_analyse',)


@admin.register(AlerteModeration)
class AlerteModerationAdmin(admin.ModelAdmin):
    list_display = ('id', 'analyse', 'statut', 'admin_notifie', 'date_creation', 'traite_par')
    list_filter = ('statut', 'date_creation')
    readonly_fields = ('date_creation',)
```

---

## Tests

### Test 1 : Vérifier l'installation

```bash
python manage.py shell
```

```python
# Test imports
from tracking.ai.transcript.transcriber import TikTokLiveTranscriber
from tracking.ai.analyse.analyzer import analyze_text

# Test analyse
result = analyze_text("Bonjour, test de transcription")
print(result)
# Devrait afficher un dict avec categorie, viralite, etc.
```

### Test 2 : Tester la transcription (mock)

```python
from tracking.models import CompteTiktok, Live, User

# Créer un compte test
user = User.objects.first()
compte = CompteTiktok.objects.create(
    user=user,
    username="test_user",
    url="https://www.tiktok.com/@test_user"
)

# Créer un live test
live = Live.objects.create(
    compte=compte,
    titre="Live test",
    statut="en_cours"
)

# Tester service
from tracking.services.transcription_service import TranscriptionService
service = TranscriptionService(live)

# Note: Le test complet nécessite un vrai live TikTok actif
```

### Test 3 : Tester l'analyse seule

```python
from tracking.ai.analyse.analyzer import analyze_text

# Test texte neutre
result1 = analyze_text("Bonjour, comment allez-vous aujourd'hui ?")
print(f"Catégorie: {result1['categorie']}, Score: {result1['risque_score']}")

# Test texte polémique
result2 = analyze_text("Le gouvernement est corrompu et incompétent")
print(f"Catégorie: {result2['categorie']}, Score: {result2['risque_score']}")
```

---

## Déploiement

### Configuration Render

**Ajouter variables d'environnement** dans le dashboard Render :

```
GROQ_API_KEY=gsk_...
WHISPER_MODEL=small
WHISPER_LANGUAGE=fr
RISK_THRESHOLD=0.7
```

**Installer FFmpeg** :

Ajouter dans `render.yaml` (ou via Build Command) :

```yaml
services:
  - type: web
    name: tiktok-tracking
    env: python
    buildCommand: |
      apt-get update
      apt-get install -y ffmpeg
      pip install -r requirements.txt
      python manage.py collectstatic --no-input
      python manage.py migrate
    startCommand: gunicorn core.wsgi:application
```

**Ou via Procfile** :

Créer `build.sh` :

```bash
#!/bin/bash
apt-get update
apt-get install -y ffmpeg
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

Rendre exécutable :
```bash
chmod +x build.sh
```

**Procfile** :

```
web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers=2 --threads=4 --timeout=120
worker: celery -A core worker -l info
beat: celery -A core beat -l info
```

**Note** : Render Free Tier ne supporte qu'un seul service. Pour worker/beat, passer au plan payant ou utiliser service externe (Celery Cloud, etc.)

---

## Troubleshooting

### Problème : FFmpeg not found

**Erreur** :
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Solution** :
```bash
# Vérifier installation
which ffmpeg

# Installer si manquant
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # macOS
```

### Problème : Groq API error

**Erreur** :
```
AuthenticationError: Invalid API key
```

**Solution** :
- Vérifier `GROQ_API_KEY` dans `.env`
- Vérifier que la clé est active sur console.groq.com
- Vérifier quotas API

### Problème : Whisper download issues

**Erreur** :
```
Error downloading Whisper model
```

**Solution** :
```bash
# Télécharger manuellement
python -c "import whisper; whisper.load_model('small')"

# Vérifier espace disque (modèles volumineux)
df -h
```

### Problème : Transcription ne démarre pas

**Vérifier** :

1. Room ID valide :
```python
from TikTokLive import TikTokLiveClient
import asyncio

async def test():
    client = TikTokLiveClient(unique_id="@username")
    await client.start()
    print(client.room_id)
    await client.disconnect()

asyncio.run(test())
```

2. Live actif :
```python
from tracking.services.tiktok_live_service import is_live
import asyncio

result = asyncio.run(is_live("@username"))
print(f"En live: {result}")
```

3. Logs :
```bash
tail -f logs/ai.log
```

### Problème : High memory usage

**Whisper consomme beaucoup de RAM** :

- Modèle `tiny` : ~1GB
- Modèle `small` : ~2GB
- Modèle `medium` : ~5GB
- Modèle `large` : ~10GB

**Solutions** :
1. Utiliser modèle plus petit (`tiny` ou `base`)
2. Augmenter RAM serveur
3. Utiliser GPU (beaucoup plus efficace)

---

## Résumé

### Checklist d'intégration

- [ ] FFmpeg installé
- [ ] Dépendances Python installées
- [ ] Modules IA copiés dans `tracking/ai/`
- [ ] Imports adaptés
- [ ] Modèles créés (Transcription, AnalyseDiscours, AlerteModeration)
- [ ] Migrations appliquées
- [ ] TranscriptionService créé
- [ ] LiveManager mis à jour
- [ ] Vues de modération créées
- [ ] Templates créés
- [ ] URLs ajoutées
- [ ] Variables d'environnement configurées
- [ ] Admin Django configuré
- [ ] Tests effectués
- [ ] Déployé en production

### Prochaines étapes

1. Tester avec un vrai live TikTok
2. Ajuster seuil de risque selon résultats
3. Implémenter arrêt automatique de live (si API disponible)
4. Ajouter dashboard analytique
5. Optimiser performance (GPU Whisper)
6. Implémenter cache pour analyses similaires

---

**Document généré le** : 2025-12-26
**Version** : 1.0
