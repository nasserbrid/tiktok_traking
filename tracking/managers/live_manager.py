from tracking.models import Live
from django.utils import timezone
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


logger = logging.getLogger(__name__)

def update_live_status(compte, live_detected: bool):
    """
    Met à jour le statut live dans la DB pour le compte.
    Envoie une notification via WebSocket si un live démarre.
    """
    
    channel_layer = get_channel_layer()
    
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
            
            # ENVOI NOTIFICATION WEBSOCKET
            async_to_sync(channel_layer.group_send)(
                "lives",
                {
                    "type": "live_notification",
                    "compte": compte.username,
                    "titre": live.titre,
                    "user_id": compte.user.id if hasattr(compte, "user") else None
                }
            )
            print(f"channel_layer.group_send:{channel_layer.group_send}")
    else:
        for live in lives:
            live.statut = "termine"
            live.date_fin = timezone.now()
            live.save(update_fields=["statut", "date_fin"])
            logger.info(f"🏁 Live #{live.id} terminé pour @{compte.username}")
