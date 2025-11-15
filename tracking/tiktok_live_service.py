from TikTokLive import TikTokLiveClient
from tracking.models import CompteTiktok, Live
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def check_if_live(compte: CompteTiktok):
    """
    Vérifie si un compte TikTok est en live et crée/met à jour les enregistrements.
    """
    try:
        client = TikTokLiveClient(unique_id=compte.username)
        
        # Tente de se connecter pour vérifier si en live
        try:
            # Cette méthode lève une exception si le compte n'est pas en live
            info = client.room_info
            
            # Si on arrive ici, le compte existe
            logger.info(f"📡 Connexion réussie à @{compte.username}")
            
            # Vérifie le statut du live
            # status: 2 = en live, 4 = hors ligne
            if info and hasattr(info, 'status'):
                status = info.status
                logger.info(f"📊 Statut de @{compte.username}: {status}")
                
                if status == 2:  # En live
                    logger.info(f"🔴 @{compte.username} est EN LIVE !")
                    
                    # Vérifie si un live est déjà enregistré
                    live_existant = compte.lives.filter(statut="en_cours").first()
                    
                    if not live_existant:
                        # Récupère les infos du live
                        titre = getattr(info, 'title', 'Live TikTok')
                        nb_spectateurs = getattr(info, 'user_count', 0)
                        
                        # Crée un nouveau live
                        live = Live.objects.create(
                            compte=compte,
                            titre=titre,
                            date_debut=timezone.now(),
                            statut="en_cours",
                            nb_spectateurs=nb_spectateurs
                        )
                        
                        logger.info(f"✅ Live créé pour @{compte.username}: {titre} ({nb_spectateurs} spectateurs)")
                        
                        # Envoie la notification de manière asynchrone
                        from tracking.tasks import send_notification_async
                        send_notification_async.delay(live.id)
                    else:
                        # Met à jour le nombre de spectateurs
                        new_count = getattr(info, 'user_count', 0)
                        if live_existant.nb_spectateurs != new_count:
                            live_existant.nb_spectateurs = new_count
                            live_existant.save(update_fields=['nb_spectateurs'])
                            logger.info(f"📊 Spectateurs mis à jour: {new_count} pour @{compte.username}")
                else:
                    # Pas en live (status != 2)
                    logger.info(f"⚫ @{compte.username} n'est pas en live (status: {status})")
                    
                    # Termine les lives en cours
                    lives_en_cours = compte.lives.filter(statut="en_cours")
                    if lives_en_cours.exists():
                        for live in lives_en_cours:
                            live.statut = "termine"
                            live.date_fin = timezone.now()
                            live.save()
                        logger.info(f"🏁 Lives terminés pour @{compte.username}")
            else:
                logger.warning(f"⚠️ Impossible de récupérer le statut de @{compte.username}")
                
        except AttributeError as e:
            logger.error(f"⚠️ Erreur d'attribut pour @{compte.username}: {e}")
        except Exception as e:
            error_msg = str(e)
            logger.debug(f"🔍 @{compte.username}: {error_msg}")
            
            # Termine les lives en cours en cas d'erreur
            lives_en_cours = compte.lives.filter(statut="en_cours")
            if lives_en_cours.exists():
                for live in lives_en_cours:
                    live.statut = "termine"
                    live.date_fin = timezone.now()
                    live.save()
                    
    except Exception as e:
        error_msg = str(e)
        if "UserNotFoundError" not in error_msg:
            logger.error(f"❌ Erreur globale pour @{compte.username}: {error_msg}")
        
        # Termine les lives en cours
        lives_en_cours = compte.lives.filter(statut="en_cours")
        if lives_en_cours.exists():
            for live in lives_en_cours:
                live.statut = "termine"
                live.date_fin = timezone.now()
                live.save()

# # tracking/tiktok_live_service.py

# from TikTokLive import TikTokLiveClient
# from TikTokLive.events import ConnectEvent, DisconnectEvent
# from threading import Thread
# from tracking.models import CompteTiktok, Live
# from notifications.utils import envoyer_notification_live
# from django.utils import timezone

# def start_tiktok_listener(compte: CompteTiktok):
#     """
#     Lance un TikTokLiveClient pour écouter un compte TikTok en temps réel.
#     """
#     client = TikTokLiveClient(unique_id=compte.username)

#     @client.on(ConnectEvent)
#     def on_connect(event):
#         """Déclenché quand on se connecte à un live en cours"""
#         print(f"[LIVE CONNECT] {compte.username}")

#         # Vérifie si un live existe déjà pour ce compte
#         live_existant = compte.lives.filter(statut="en_cours").first()
        
#         if not live_existant:
#             live = Live.objects.create(
#                 compte=compte,
#                 titre="Live TikTok",
#                 date_debut=timezone.now(),
#                 statut="en_cours"
#             )
#             envoyer_notification_live(live)

#     @client.on(DisconnectEvent)
#     def on_disconnect(event):
#         """Déclenché quand le live se termine ou qu'on se déconnecte"""
#         print(f"[LIVE DISCONNECT] {compte.username}")

#         try:
#             live = compte.lives.filter(statut="en_cours").latest("date_debut")
#             live.statut = "termine"
#             live.date_fin = timezone.now()
#             live.save()
#         except Live.DoesNotExist:
#             pass

#     # Lance le client dans un thread séparé
#     def run_client():
#         try:
#             client.run()
#         except Exception as e:
#             print(f"[ERROR] {compte.username}: {e}")

#     Thread(target=run_client, daemon=True).start()


# def start_all_tiktok_watchers():
#     """Démarre l'écoute pour tous les comptes TikTok"""
#     comptes = CompteTiktok.objects.all()
#     for compte in comptes:
#         start_tiktok_listener(compte)
#         print(f"[LISTENING] {compte.username}")