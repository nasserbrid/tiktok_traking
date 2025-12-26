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
    Démarre/arrête la transcription IA.
    """
    from tracking.services.transcription_service import (
        start_transcription_for_live,
        stop_transcription_for_live
    )

    channel_layer = get_channel_layer()

    lives = compte.lives.filter(statut="en_cours")

    if live_detected:
        if not lives.exists():
            # Crée un live temporaire pour refléter le statut
            live = Live.objects.create(
                compte=compte,
                titre="Live TikTok détecté",
                date_debut=timezone.now(),
                statut="en_cours",
                nb_spectateurs=0
            )

            logger.info(f"🔴 @{compte.username} est en live")

            # Démarrer la transcription IA
            success = start_transcription_for_live(live)
            if success:
                logger.info(f"✅ Transcription IA démarrée pour live {live.id}")
            else:
                logger.error(f"❌ Échec démarrage transcription pour live {live.id}")

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
    else:
        for live in lives:
            # Arrêter la transcription IA
            stop_transcription_for_live(live)
            logger.info(f"🛑 Transcription IA arrêtée pour live {live.id}")

            live.statut = "termine"
            live.date_fin = timezone.now()
            live.save(update_fields=["statut", "date_fin"])
            logger.info(f"🏁 Live #{live.id} terminé pour @{compte.username}")
