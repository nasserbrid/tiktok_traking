# tracking/tiktok_api.py (nouveau fichier)

import httpx
from tracking.models import CompteTiktok, Live
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def check_if_live_http(compte: CompteTiktok):
    """
    Vérifie si un compte est en live en utilisant l'API web de TikTok.
    """
    try:
        url = f"https://www.tiktok.com/@{compte.username}/live"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        with httpx.Client(headers=headers, follow_redirects=True) as client:
            response = client.get(url, timeout=10)
            
            # Si on est redirigé vers le profil, pas de live
            if "/live" not in response.url.path:
                logger.info(f"⚫ @{compte.username} n'est pas en live")
                
                # Termine les lives en cours
                lives_en_cours = compte.lives.filter(statut="en_cours")
                if lives_en_cours.exists():
                    for live in lives_en_cours:
                        live.statut = "termine"
                        live.date_fin = timezone.now()
                        live.save()
                return
            
            # Le compte est en live
            logger.info(f"🔴 @{compte.username} est EN LIVE !")
            
            # Vérifie si un live existe déjà
            live_existant = compte.lives.filter(statut="en_cours").first()
            
            if not live_existant:
                live = Live.objects.create(
                    compte=compte,
                    titre="Live TikTok",
                    date_debut=timezone.now(),
                    statut="en_cours"
                )
                
                # Envoie la notification
                from tracking.tasks import send_notification_async
                send_notification_async.delay(live.id)
                
                logger.info(f"✅ Live créé pour @{compte.username}")
                
    except Exception as e:
        logger.error(f"❌ Erreur HTTP pour @{compte.username}: {e}")