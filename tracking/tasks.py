#methode avec tiktok_api.py
from celery import shared_task
from tracking.models import CompteTiktok
from tracking.tiktok_api import check_if_live_http  # Nouvelle méthode
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def check_all_accounts(self):
    """
    Vérifie tous les comptes TikTok pour détecter les lives.
    """
    comptes = CompteTiktok.objects.all()
    
    if not comptes.exists():
        logger.info("Aucun compte à vérifier")
        return "Aucun compte à vérifier"
    
    logger.info(f"🔍 Vérification de {comptes.count()} comptes...")
    
    success_count = 0
    error_count = 0
    
    for compte in comptes:
        try:
            check_if_live_http(compte)  # Utilise la nouvelle méthode HTTP
            success_count += 1
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Erreur pour @{compte.username}: {str(e)}")
    
    result = f"✅ Vérifié {success_count} comptes | ❌ {error_count} erreurs"
    logger.info(result)
    return result

# ... reste du fichier identique
#methode avec tiktok_live_service.py
# from celery import shared_task
# from tracking.models import CompteTiktok
# from tracking.tiktok_live_service import check_if_live
# import logging

# logger = logging.getLogger(__name__)

# @shared_task(bind=True, max_retries=3)
# def check_all_accounts(self):
#     """
#     Vérifie tous les comptes TikTok pour détecter les lives.
#     S'exécute automatiquement toutes les 2 minutes via Celery Beat.
#     """
#     comptes = CompteTiktok.objects.all()
    
#     if not comptes.exists():
#         logger.info("Aucun compte à vérifier")
#         return "Aucun compte à vérifier"
    
#     logger.info(f"🔍 Vérification de {comptes.count()} comptes...")
    
#     success_count = 0
#     error_count = 0
    
#     for compte in comptes:
#         try:
#             check_if_live(compte)
#             success_count += 1
#         except Exception as e:
#             error_count += 1
#             logger.error(f"❌ Erreur pour @{compte.username}: {str(e)}")
    
#     result = f"✅ Vérifié {success_count} comptes | ❌ {error_count} erreurs"
#     logger.info(result)
#     return result


# @shared_task
# def check_single_account(compte_id):
#     """
#     Vérifie un seul compte spécifique.
#     Utile pour tester ou forcer une vérification manuelle.
#     """
#     try:
#         compte = CompteTiktok.objects.get(id=compte_id)
#         check_if_live(compte)
#         return f"✅ Vérifié @{compte.username}"
#     except CompteTiktok.DoesNotExist:
#         return "❌ Compte introuvable"
#     except Exception as e:
#         return f"❌ Erreur: {str(e)}"


# @shared_task
# def send_notification_async(live_id):
#     """
#     Envoie une notification de manière asynchrone.
#     """
#     from tracking.models import Live
#     from notifications.utils import envoyer_notification_live
    
#     try:
#         live = Live.objects.get(id=live_id)
#         envoyer_notification_live(live)
#         return f"✅ Notification envoyée pour {live.compte.username}"
#     except Live.DoesNotExist:
#         return "❌ Live introuvable"
#     except Exception as e:
#         return f"❌ Erreur: {str(e)}"