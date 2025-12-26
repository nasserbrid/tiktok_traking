"""
Utilitaires pour l'envoi de notifications via WebSocket et sauvegarde en BDD.

Ici, je fournis des fonctions helper pour envoyer facilement des notifications
aux utilisateurs, que ce soit pour les lives détectés ou les alertes de modération.
"""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from tracking.models import Live
from notifications.models import Notification


def envoyer_notification_live(live: Live):
    """
    Ici, j'envoie une notification quand un live est détecté.

    Workflow :
    1. Créer une notification en base de données pour l'historique
    2. Envoyer une notification WebSocket au groupe personnel de l'utilisateur
    3. Envoyer aussi au groupe global "lives" pour broadcast

    Args:
        live: Instance du modèle Live qui vient de démarrer
    """
    user = live.compte.user
    channel_layer = get_channel_layer()

    # Ici, je vérifie que le channel layer est configuré
    if not channel_layer:
        return  # Ici, je quitte si Channels n'est pas configuré

    # Ici, je crée la notification en base de données pour l'historique
    notif = Notification.objects.create(
        user=user,
        live=live,
        message=f"{live.compte.username} est en live : {live.titre}"
    )

    # Ici, j'envoie au groupe personnel de l'utilisateur (ciblé)
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "live_notification",
            "compte": live.compte.username,
            "titre": live.titre,
            "user_id": user.id
        }
    )

    # Ici, j'envoie aussi au groupe global "lives" pour broadcast
    async_to_sync(channel_layer.group_send)(
        "lives",
        {
            "type": "live_notification",
            "compte": live.compte.username,
            "titre": live.titre,
            "user_id": user.id
        }
    )


def envoyer_notification_fin_live(live: Live):
    """
    Ici, j'envoie une notification quand un live se termine.

    Args:
        live: Instance du modèle Live qui vient de se terminer
    """
    user = live.compte.user
    channel_layer = get_channel_layer()

    if not channel_layer:
        return

    # Ici, je crée une notification de fin de live
    notif = Notification.objects.create(
        user=user,
        live=live,
        message=f"Le live de {live.compte.username} est terminé"
    )

    # Ici, j'envoie la notification de fin au groupe personnel
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "live_notification",
            "compte": live.compte.username,
            "titre": "Live terminé",
            "user_id": user.id,
            "ended": True  # Ici, j'indique que le live est terminé
        }
    )


def marquer_notifications_lues(user, live=None):
    """
    Ici, je marque les notifications comme lues pour un utilisateur.

    Args:
        user: Instance de User
        live: (Optionnel) Si fourni, marque uniquement les notifs de ce live

    Returns:
        int: Nombre de notifications marquées comme lues
    """
    # Ici, je filtre les notifications non lues de l'utilisateur
    notifications = Notification.objects.filter(user=user, is_read=False)

    # Ici, je filtre par live si spécifié
    if live:
        notifications = notifications.filter(live=live)

    # Ici, je marque toutes comme lues et retourne le compte
    return notifications.update(is_read=True)
