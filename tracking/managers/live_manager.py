# tracking/managers/live_manager.py
from tracking.models import Live
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def update_live_status(compte, live_detected: bool):
    """
    Met à jour le statut live dans la DB pour le compte.
    """
    lives = compte.lives.filter(statut="en_cours")

    if live_detected:
        if not lives.exists():
            # Crée un live temporaire pour refléter le statut
            Live.objects.create(
                compte=compte,
                titre="Live TikTok détecté",
                date_debut=timezone.now(),
                statut="en_cours",
                nb_spectateurs=0
            )
            logger.info(f"🔴 @{compte.username} est en live")
    else:
        for live in lives:
            live.statut = "termine"
            live.date_fin = timezone.now()
            live.save(update_fields=["statut", "date_fin"])
            logger.info(f"🏁 Live #{live.id} terminé pour @{compte.username}")
