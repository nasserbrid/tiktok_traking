# tracking/services/tiktok_service.py
import asyncio
from TikTokLive import TikTokLiveClient
import logging

logger = logging.getLogger(__name__)

async def is_live(username: str) -> (bool, str):
    """
    Retourne True si l'utilisateur TikTok est en live.
    """
    username = username.lstrip("@")
    client = TikTokLiveClient(unique_id=username)
    try:
        # live = await client.is_live()
        # # On récupère le room_id directement depuis l'attribut du client mis à jour
        # room_id = str(client.room_id) if is_live else None
        # return live, room_id
        room_id = await client.web.fetch_room_id_from_html(username)

        return True,room_id

    except Exception as e:
        logger.error(f"Erreur TikTok @{username}: {e}")
        return False,None

# import asyncio
# import logging
# from django.utils import timezone
# from TikTokLive import TikTokLiveClient
# from tracking.models import CompteTiktok

# logger = logging.getLogger(__name__)


# def check_if_live(compte: CompteTiktok):
#     """
#     Vérifie si un compte TikTok est en live.
#     Mise à jour des Live existants sans en créer.
#     Compatible avec Celery et Django ORM synchrones.
#     """

#     username = compte.username.lstrip("@")
#     client = TikTokLiveClient(unique_id=username)

#     try:
#         # 🔹 Async uniquement pour récupérer le statut live
#         is_live = asyncio.run(client.is_live())
#         logger.info(f"🔍 @{username} → {'LIVE' if is_live else 'OFFLINE'}")

#         # 🔹 Tout le reste reste synchrone pour Django ORM
#         if is_live:
#             _mark_live(compte)
#         else:
#             _mark_offline(compte)

#     except Exception as e:
#         logger.error(f"❌ Erreur TikTok @{username}: {e}")
#         _mark_offline(compte)


# # ---------------------------------------------------------
# #          GESTION SYNCHRONE DES OBJETS LIVE
# # ---------------------------------------------------------

# def _mark_live(compte: CompteTiktok):
#     """
#     Vérifie s’il existe un live en cours (synchrone)
#     et log le statut, sans créer de live.
#     """
#     live_en_cours = compte.lives.filter(statut="en_cours").first()

#     if live_en_cours:
#         logger.debug(f"🔴 @{compte.username} est déjà marqué EN LIVE (Live #{live_en_cours.id})")
#     else:
#         logger.info(f"🔴 @{compte.username} est EN LIVE (détection OK), aucun Live créé.")


# def _mark_offline(compte: CompteTiktok):
#     """
#     Termine les éventuels lives en cours (synchrone)
#     """
#     lives = compte.lives.filter(statut="en_cours")

#     if not lives.exists():
#         logger.info(f"⚫ @{compte.username} OFFLINE (déjà hors-ligne)")
#         return

#     for live in lives:
#         live.statut = "termine"
#         live.date_fin = timezone.now()
#         live.save(update_fields=["statut", "date_fin"])
#         logger.info(f"🏁 Live #{live.id} terminé pour @{compte.username}")





# from TikTokLive import TikTokLiveClient
# from TikTokLive.events import ConnectEvent, DisconnectEvent
# from tracking.models import CompteTiktok, Live
# from django.utils import timezone
# import logging

# logger = logging.getLogger(__name__)


# def check_if_live(compte: CompteTiktok):
#     """
#     Vérifie si un compte TikTok est en live et met à jour la base.
#     Aucun live n'est créé sur TikTok : on détecte seulement.
#     """
#     try:
#         client = TikTokLiveClient(unique_id=compte.username)

#         try:
#             # TikTokLive nécessite un fetch explicite !
#             info = client.room_info
#             print(f"info: {info}")

#             if not info:
#                 logger.warning(f"⚠ Impossible d'obtenir room_info pour @{compte.username}")
#                 _close_lives(compte)
#                 return

#             status = getattr(info, "status", None)
#             logger.info(f"📡 Statut @{compte.username}: {status}")

#             # 🔴 2 = EN LIVE
#             if status == 2:
#                 logger.info(f"🔴 @{compte.username} est en live")

#                 live_en_cours = compte.lives.filter(statut="en_cours").first()

#                 titre = getattr(info, "title", "Live TikTok")
#                 spectateurs = getattr(info, "user_count", 0)

#                 # ▶ Créer un live seulement s’il n’existe pas déjà
#                 #Je n'ai pas besoin de créer des lives, juste de détecter s'ils sont en live ou pas
#                 # if not live_en_cours:
#                 #     live = Live.objects.create(
#                 #         compte=compte,
#                 #         titre=titre,
#                 #         date_debut=timezone.now(),
#                 #         statut="en_cours",
#                 #         nb_spectateurs=spectateurs
#                 #     )

#                 #     logger.info(f"✅ Live créé pour @{compte.username}: {titre}")

#                 #     # Envoyer la notification si tu en as une
#                 #     try:
#                 #         from tracking.tasks import send_notification_async
#                 #         send_notification_async.delay(live.id)
#                 #     except Exception as e:
#                 #         logger.error(f"⚠ Erreur task notification: {e}")

#                 # else:
#                 #     # ↻ Mise à jour du nombre de spectateurs
#                 #     if live_en_cours.nb_spectateurs != spectateurs:
#                 #         live_en_cours.nb_spectateurs = spectateurs
#                 #         live_en_cours.save(update_fields=['nb_spectateurs'])
#                 #         logger.info(f"📊 Mise à jour spectateurs: {spectateurs}")

#             else:
#                 # ⚫ Pas en live
#                 logger.info(f"⚫ @{compte.username} hors ligne")
#                 _close_lives(compte)

#         except Exception as e:
#             logger.error(f"❌ Erreur TikTok pour @{compte.username}: {e}")
#             _close_lives(compte)

#     except Exception as e:
#         logger.error(f"❌ Erreur globale @{compte.username}: {e}")
#         _close_lives(compte)


# def _close_lives(compte: CompteTiktok):
#     """ Termine proprement les lives en cours """
#     lives = compte.lives.filter(statut="en_cours")

#     for live in lives:
#         live.statut = "termine"
#         live.date_fin = timezone.now()
#         live.save()

#     if lives.exists():
#         logger.info(f"🏁 Lives terminés pour @{compte.username}")

# from TikTokLive import TikTokLiveClient
# from tracking.models import CompteTiktok, Live
# from django.utils import timezone
# import logging

# logger = logging.getLogger(__name__)

# def check_if_live(compte: CompteTiktok):
#     """
#     Vérifie si un compte TikTok est en live et crée/met à jour les enregistrements.
#     """
#     try:
#         client = TikTokLiveClient(unique_id=compte.username)
        
#         # Tente de se connecter pour vérifier si en live
#         try:
#             # Cette méthode lève une exception si le compte n'est pas en live
#             info = client.room_info
            
#             # Si on arrive ici, le compte existe
#             logger.info(f"Connexion réussie à @{compte.username}")
            
#             # Vérifie le statut du live
#             # status: 2 = en live, 4 = hors ligne
#             if info and hasattr(info, 'status'):
#                 status = info.status
#                 logger.info(f"📊 Statut de @{compte.username}: {status}")
                
#                 if status == 2:  # En live
#                     logger.info(f"🔴 @{compte.username} est EN LIVE !")
                    
#                     # Vérifie si un live est déjà enregistré
#                     live_existant = compte.lives.filter(statut="en_cours").first()
                    
#                     if not live_existant:
#                         # Récupère les infos du live
#                         titre = getattr(info, 'title', 'Live TikTok')
#                         nb_spectateurs = getattr(info, 'user_count', 0)
                        
#                         # Crée un nouveau live
#                         live = Live.objects.create(
#                             compte=compte,
#                             titre=titre,
#                             date_debut=timezone.now(),
#                             statut="en_cours",
#                             nb_spectateurs=nb_spectateurs
#                         )
                        
#                         logger.info(f"✅ Live créé pour @{compte.username}: {titre} ({nb_spectateurs} spectateurs)")
                        
#                         # Envoie la notification de manière asynchrone
#                         from tracking.tasks import send_notification_async
#                         send_notification_async.delay(live.id)
#                     else:
#                         # Met à jour le nombre de spectateurs
#                         new_count = getattr(info, 'user_count', 0)
#                         if live_existant.nb_spectateurs != new_count:
#                             live_existant.nb_spectateurs = new_count
#                             live_existant.save(update_fields=['nb_spectateurs'])
#                             logger.info(f"📊 Spectateurs mis à jour: {new_count} pour @{compte.username}")
#                 else:
#                     # Pas en live (status != 2)
#                     logger.info(f"⚫ @{compte.username} n'est pas en live (status: {status})")
                    
#                     # Termine les lives en cours
#                     lives_en_cours = compte.lives.filter(statut="en_cours")
#                     if lives_en_cours.exists():
#                         for live in lives_en_cours:
#                             live.statut = "termine"
#                             live.date_fin = timezone.now()
#                             live.save()
#                         logger.info(f"🏁 Lives terminés pour @{compte.username}")
#             else:
#                 logger.warning(f"⚠️ Impossible de récupérer le statut de @{compte.username}")
                
#         except AttributeError as e:
#             logger.error(f"⚠️ Erreur d'attribut pour @{compte.username}: {e}")
#         except Exception as e:
#             error_msg = str(e)
#             logger.debug(f"🔍 @{compte.username}: {error_msg}")
            
#             # Termine les lives en cours en cas d'erreur
#             lives_en_cours = compte.lives.filter(statut="en_cours")
#             if lives_en_cours.exists():
#                 for live in lives_en_cours:
#                     live.statut = "termine"
#                     live.date_fin = timezone.now()
#                     live.save()
                    
#     except Exception as e:
#         error_msg = str(e)
#         if "UserNotFoundError" not in error_msg:
#             logger.error(f"❌ Erreur globale pour @{compte.username}: {error_msg}")
        
#         # Termine les lives en cours
#         lives_en_cours = compte.lives.filter(statut="en_cours")
#         if lives_en_cours.exists():
#             for live in lives_en_cours:
#                 live.statut = "termine"
#                 live.date_fin = timezone.now()
#                 live.save()

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