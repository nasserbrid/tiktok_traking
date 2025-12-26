"""
WebSocket consumers pour les notifications en temps réel.

Ici, je gère 3 types de notifications :
1. Notifications de lives (quand un compte suivi démarre un live)
2. Alertes de modération (quand l'IA détecte un contenu à risque)
3. Transcriptions temps réel (segments transcrits d'un live)
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class LiveNotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les notifications de lives.

    Ici, je gère les connexions WebSocket des utilisateurs pour recevoir
    les notifications en temps réel quand leurs comptes suivis sont en live.
    """

    async def connect(self):
        """
        Ici, je gère la connexion d'un utilisateur au WebSocket.

        Workflow :
        1. Vérifier que l'utilisateur est authentifié
        2. L'ajouter à son groupe personnel (user_{user_id})
        3. L'ajouter au groupe global "lives" pour broadcast général
        4. Accepter la connexion
        """
        self.user = self.scope["user"]

        # Ici, je vérifie que l'utilisateur est connecté
        if self.user.is_anonymous:
            await self.close()  # Ici, je refuse la connexion si anonyme
            return

        # Ici, je définis le nom du groupe personnel de l'utilisateur
        self.user_group = f"user_{self.user.id}"

        # Ici, j'ajoute l'utilisateur à son groupe personnel
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )

        # Ici, j'ajoute aussi au groupe global pour les broadcasts
        await self.channel_layer.group_add(
            "lives",
            self.channel_name
        )

        # Ici, j'accepte la connexion WebSocket
        await self.accept()

    async def disconnect(self, close_code):
        """
        Ici, je gère la déconnexion d'un utilisateur.

        Ici, je retire l'utilisateur de tous ses groupes pour libérer les ressources.
        """
        if hasattr(self, 'user') and not self.user.is_anonymous:
            # Ici, je retire du groupe personnel
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )

            # Ici, je retire du groupe global
            await self.channel_layer.group_discard(
                "lives",
                self.channel_name
            )

    async def live_notification(self, event):
        """
        Ici, je traite une notification de live détecté.

        Ici, j'envoie la notification au client WebSocket au format JSON.

        Args:
            event: Dictionnaire contenant les données de la notification
                   {compte, titre, user_id}
        """
        # Ici, je prépare les données à envoyer au client
        await self.send(text_data=json.dumps({
            "type": "live_notification",
            "compte": event["compte"],
            "titre": event["titre"],
            "user_id": event.get("user_id"),
            "message": f"@{event['compte']} est en live : {event['titre']}"
        }))

    async def moderation_alert(self, event):
        """
        Ici, je traite une alerte de modération IA.

        Ici, j'envoie l'alerte uniquement aux administrateurs connectés.

        Args:
            event: Dictionnaire contenant les données de l'alerte
                   {alerte_id, live_id, compte, risque_score, categorie}
        """
        # Ici, je vérifie que l'utilisateur est admin
        if hasattr(self.user, 'role') and self.user.role == 'ADMIN':
            # Ici, j'envoie l'alerte à l'admin
            await self.send(text_data=json.dumps({
                "type": "moderation_alert",
                "alerte_id": event["alerte_id"],
                "live_id": event["live_id"],
                "compte": event["compte"],
                "risque_score": event["risque_score"],
                "categorie": event["categorie"],
                "message": f"⚠️ Alerte : @{event['compte']} - Risque {event['risque_score']}"
            }))

    async def new_transcription(self, event):
        """
        Ici, je traite une nouvelle transcription de segment.

        Ici, j'envoie la transcription en temps réel aux utilisateurs qui suivent ce live.

        Args:
            event: Dictionnaire contenant les données de transcription
                   {segment, text, risque_score, categorie}
        """
        await self.send(text_data=json.dumps({
            "type": "new_transcription",
            "segment": event["segment"],
            "text": event["text"],
            "risque_score": event["risque_score"],
            "categorie": event["categorie"]
        }))


class ModerationConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket dédié aux alertes de modération pour les admins.

    Ici, je gère un canal séparé spécifiquement pour les administrateurs
    qui surveillent les alertes de modération en temps réel.
    """

    async def connect(self):
        """
        Ici, je gère la connexion d'un admin au canal de modération.

        Ici, je vérifie que l'utilisateur est bien un administrateur avant
        de l'ajouter au groupe "moderation".
        """
        self.user = self.scope["user"]

        # Ici, je vérifie que l'utilisateur est admin
        if self.user.is_anonymous or not hasattr(self.user, 'role') or self.user.role != 'ADMIN':
            await self.close()  # Ici, je refuse si pas admin
            return

        # Ici, j'ajoute l'admin au groupe de modération
        await self.channel_layer.group_add(
            "moderation",
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """Ici, je retire l'admin du groupe de modération"""
        if hasattr(self, 'user') and not self.user.is_anonymous:
            await self.channel_layer.group_discard(
                "moderation",
                self.channel_name
            )

    async def moderation_alert(self, event):
        """
        Ici, je traite et envoie une alerte de modération aux admins.

        Args:
            event: Données de l'alerte
        """
        await self.send(text_data=json.dumps({
            "type": "moderation_alert",
            "alerte_id": event["alerte_id"],
            "live_id": event["live_id"],
            "compte": event["compte"],
            "risque_score": event["risque_score"],
            "categorie": event["categorie"],
            "timestamp": event.get("timestamp")
        }))
