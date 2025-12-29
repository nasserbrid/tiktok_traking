from tracking.models import Live
from django.utils import timezone
import logging
from channels.layers import get_channel_layer

import threading
from asgiref.sync import async_to_sync



logger = logging.getLogger(__name__)


def _execute_live_processing_thread(live,room_id, username, user_id):
    """
    TRAITEMENT EN ARRIÈRE-PLAN via Thread.
    """
    from tracking.services.transcription_service import start_transcription_for_live
    from django.db import connections

    try:
        # 1. Démarrage de la transcription IA

        success = start_transcription_for_live(live,room_id)

        if success:
            logger.info(f"✅ [Thread] IA opérationnelle pour @{username}")
        else:
            logger.error(f"❌ [Thread] Échec démarrage IA pour @{username}")

        # 2. Notification WebSocket
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "lives",
                {
                    "type": "live_notification",
                    "compte": username,
                    "titre": live.titre,
                    "user_id": user_id
                }
            )
            logger.info(f"✅ [Thread] Notification envoyée pour @{username}")

    except Exception as e:
        logger.error(f"❌ [Thread] Erreur lors du traitement de @{username}: {e}")
    finally:
        # Indispensable : Fermer les connexions orphelines dans ce thread
        connections.close_all()


def update_live_status(compte, live_detected: bool, room_id: str = None):
    """
    Met à jour le statut live dans la DB pour le compte.
    Envoie une notification via WebSocket si un live démarre.
    Démarre/arrête la transcription IA.
    """
    from tracking.services.transcription_service import (
        start_transcription_for_live,
        stop_transcription_for_live,
        active_transcribers
    )

    channel_layer = get_channel_layer()

    lives = compte.lives.filter(statut="en_cours")

    if live_detected:
        live = lives.first()
        if not lives.exists():
            # Crée un live temporaire pour refléter le statut
            live = Live.objects.create(
                compte=compte,
                titre="Live TikTok détecté",
                date_debut=timezone.now(),
                statut="en_cours",
                nb_spectateurs=0
            )
            
            
        
        if not Live.objects.filter(pk=live.pk).exists():
            logger.error(f"❌ Impossible de démarrer le thread : Live {live.pk} n'existe plus.")
            return

        if live.id in active_transcribers:
            existing = active_transcribers[live.id]
            if existing.is_running:
                logger.info(f"Transcription déjà active pour @{compte.username} (Live #{live.id})")
                return

        logger.info(f"🔴 @{compte.username} est en live")

        # Démarrer la transcription IA



        thread = threading.Thread(
            target=_execute_live_processing_thread,
            args=(live, room_id, compte.username, compte.user.id if hasattr(compte, "user") else None),
            daemon=True
        )
        thread.start()


            # success = start_transcription_for_live(live)
            # if success:
            #     logger.info(f"✅ Transcription IA démarrée pour live {live.id}")
            # else:
            #     logger.error(f"❌ Échec démarrage transcription pour live {live.id}")
            #
            # # ENVOI NOTIFICATION WEBSOCKET
            # async_to_sync(channel_layer.group_send)(
            #     "lives",
            #     {
            #         "type": "live_notification",
            #         "compte": compte.username,
            #         "titre": live.titre,
            #         "user_id": compte.user.id if hasattr(compte, "user") else None
            #     }
            #)
    else:
        for live in lives:
            # Arrêter la transcription IA
            stop_transcription_for_live(live)
            logger.info(f"🛑 Transcription IA arrêtée pour live {live.id}")

            live.statut = "termine"
            live.date_fin = timezone.now()
            live.save(update_fields=["statut", "date_fin"])
            logger.info(f"🏁 Live #{live.id} terminé pour @{compte.username}")
