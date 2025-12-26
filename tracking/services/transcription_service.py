"""
Service de gestion de la transcription automatique et de l'analyse IA des lives TikTok.

Ici, je gère tout le cycle de vie de la transcription :
- Démarrage/arrêt de la transcription Whisper
- Sauvegarde des segments transcrits
- Analyse automatique via Groq LLM
- Création d'alertes de modération
- Notifications WebSocket en temps réel
"""

import logging
from typing import Dict, Optional
from tracking.ai.transcript.transcriber import TikTokLiveTranscriber
from tracking.ai.analyse.analyzer import analyze_text
from tracking.models import Live, Transcription, AnalyseDiscours, AlerteModeration
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

# Ici, je stocke les transcribers actifs pour éviter les doublons
active_transcribers: Dict[int, TikTokLiveTranscriber] = {}


class TranscriptionService:
    """
    Service de gestion de la transcription et analyse IA.

    Ici, je centralise toute la logique de transcription :
    - Connexion au live TikTok
    - Capture et transcription audio via Whisper
    - Analyse de discours via Groq LLM
    - Gestion des alertes et notifications
    """

    def __init__(self, live: Live):
        """
        Ici, j'initialise le service pour un live spécifique.

        Args:
            live: Instance du modèle Live à transcrire
        """
        self.live = live
        self.transcriber: Optional[TikTokLiveTranscriber] = None

    def start(self) -> bool:
        """
        Ici, je démarre la transcription automatique du live.

        Étapes :
        1. Vérifier qu'aucune transcription n'est déjà active
        2. Récupérer le room_id TikTok
        3. Créer et configurer le transcriber Whisper
        4. Démarrer la capture audio

        Returns:
            bool: True si le démarrage a réussi, False sinon
        """
        # Ici, je vérifie si une transcription est déjà en cours
        if self.live.id in active_transcribers:
            logger.warning(f"Transcription déjà active pour live {self.live.id}")
            return False

        try:
            # Ici, je récupère le room_id nécessaire pour se connecter au live
            room_id = self._get_room_id()
            if not room_id:
                logger.error(f"Impossible de récupérer room_id pour {self.live.compte.username}")
                return False

            # Ici, je crée le transcriber avec la configuration depuis settings
            self.transcriber = TikTokLiveTranscriber(
                room_id=room_id,
                model=getattr(settings, 'WHISPER_MODEL', 'small'),
                language=getattr(settings, 'WHISPER_LANGUAGE', 'fr'),
                duration=15,  # Ici, je définis des segments de 15 secondes
                unique_id=self.live.compte.username,
                on_transcription=self._handle_transcription,  # Ici, je définis le callback de transcription
                on_error=self._handle_error,  # Ici, je gère les erreurs
                on_complete=self._handle_complete  # Ici, je gère la fin
            )

            # Ici, je démarre la transcription
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
        """
        Ici, j'arrête la transcription en cours pour ce live.

        Ici, je libère les ressources et retire le transcriber de la liste active.
        """
        if self.live.id in active_transcribers:
            transcriber = active_transcribers[self.live.id]
            transcriber.stop()  # Ici, j'arrête le transcriber proprement
            del active_transcribers[self.live.id]  # Ici, je le retire de la liste
            logger.info(f"Transcription arrêtée pour live {self.live.id}")

    def _get_room_id(self) -> Optional[str]:
        """
        Ici, je récupère le room_id TikTok nécessaire pour la connexion au live.

        Ici, j'utilise TikTokLiveClient pour me connecter brièvement et obtenir
        le room_id, puis je me déconnecte immédiatement.

        Returns:
            str: Le room_id si trouvé, None sinon
        """
        from TikTokLive import TikTokLiveClient
        import asyncio

        async def get_room():
            """Ici, je définis une fonction async pour récupérer le room_id"""
            client = TikTokLiveClient(unique_id=self.live.compte.username)
            try:
                # Ici, je me connecte au live pour obtenir le room_id
                await client.start()
                room_id = client.room_id
                await client.disconnect()  # Ici, je me déconnecte immédiatement
                return str(room_id)
            except Exception as e:
                logger.error(f"Erreur récupération room_id: {e}")
                return None

        # Ici, j'exécute la fonction async de manière synchrone
        return asyncio.run(get_room())

    def _handle_transcription(self, text: str, segment: int, unique_id: str) -> None:
        """
        Ici, je traite chaque segment transcrit par Whisper.

        Workflow complet :
        1. Sauvegarder la transcription en BDD
        2. Analyser le texte avec Groq LLM
        3. Sauvegarder l'analyse
        4. Créer une alerte si risque élevé
        5. Envoyer notification WebSocket

        Args:
            text: Le texte transcrit par Whisper
            segment: Numéro du segment (ordre chronologique)
            unique_id: Username TikTok
        """
        try:
            # Ici, je sauvegarde le segment transcrit en base de données
            transcription = Transcription.objects.create(
                live=self.live,
                segment_number=segment,
                text=text
            )
            logger.info(f"Transcription segment {segment} sauvegardée pour live {self.live.id}")

            # Ici, j'analyse le texte avec l'IA pour détecter les contenus à risque
            analysis_result = analyze_text(text)

            # Ici, je sauvegarde les résultats de l'analyse en BDD
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

            # Ici, je vérifie si le score dépasse le seuil d'alerte
            risk_threshold = getattr(settings, 'RISK_THRESHOLD', 0.7)
            if analyse.risque_score >= risk_threshold:
                self._create_alert(analyse)  # Ici, je crée une alerte pour les admins

            # Ici, j'envoie une notification WebSocket en temps réel
            self._send_transcription_notification(transcription, analyse)

        except Exception as e:
            logger.error(f"Erreur traitement transcription: {e}", exc_info=True)

    def _handle_error(self, error: str) -> None:
        """
        Ici, je gère les erreurs remontées par le transcriber.

        Args:
            error: Message d'erreur
        """
        logger.error(f"Erreur transcription live {self.live.id}: {error}")

    def _handle_complete(self, stats: dict) -> None:
        """
        Ici, je traite la fin de la transcription et log les statistiques.

        Args:
            stats: Dictionnaire contenant les métriques de transcription
        """
        logger.info(f"Transcription terminée pour live {self.live.id}: {stats}")

    def _map_categorie(self, categorie_llm: str) -> str:
        """
        Ici, je convertis la catégorie retournée par le LLM vers les choix du modèle Django.

        Args:
            categorie_llm: Catégorie en texte libre retournée par Groq

        Returns:
            str: Clé correspondante dans CATEGORIE_CHOICES
        """
        mapping = {
            'Neutre': 'neutre',
            'Polémique': 'polemique',
            'Potentiellement viral': 'viral',
            'Discours haineux': 'haineux'
        }
        return mapping.get(categorie_llm, 'neutre')

    def _create_alert(self, analyse: AnalyseDiscours) -> None:
        """
        Ici, je crée une alerte de modération pour tous les administrateurs.

        Ici, je notifie tous les admins via :
        - Création d'un enregistrement AlerteModeration en BDD
        - Envoi d'une notification WebSocket sur le canal "moderation"

        Args:
            analyse: Instance d'AnalyseDiscours qui a déclenché l'alerte
        """
        from authentication.models import User

        # Ici, je récupère tous les utilisateurs avec le rôle ADMIN
        admins = User.objects.filter(role=User.ADMIN)

        for admin in admins:
            # Ici, je crée une alerte individuelle pour chaque admin
            alerte = AlerteModeration.objects.create(
                analyse=analyse,
                admin_notifie=admin,
                statut='pending'
            )
            logger.warning(f"Alerte créée pour admin {admin.username}: {alerte.id}")

        # Ici, j'envoie une notification WebSocket aux admins connectés
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "moderation",  # Ici, je cible le groupe WebSocket des admins
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
        """
        Ici, j'envoie une notification WebSocket pour chaque nouvelle transcription.

        Ici, je permets aux clients connectés de recevoir les transcriptions en temps réel
        sur le canal spécifique à ce live.

        Args:
            transcription: Instance de Transcription
            analyse: Instance d'AnalyseDiscours associée
        """
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"live_{self.live.id}",  # Ici, je cible le canal spécifique au live
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
    Ici, je fournis une fonction utilitaire pour démarrer facilement une transcription.

    Ici, je crée un service et démarre la transcription en une seule ligne.

    Args:
        live: Instance du modèle Live

    Returns:
        bool: True si le démarrage a réussi, False sinon
    """
    service = TranscriptionService(live)
    return service.start()


def stop_transcription_for_live(live: Live) -> None:
    """
    Ici, je fournis une fonction utilitaire pour arrêter facilement une transcription.

    Ici, je crée un service et arrête la transcription proprement.

    Args:
        live: Instance du modèle Live
    """
    service = TranscriptionService(live)
    service.stop()
