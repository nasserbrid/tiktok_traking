# notifications/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from tracking.models import Live
from notifications.models import Notification

def envoyer_notification_live(live: Live):
    user = live.compte.user
    channel_layer = get_channel_layer()

    if not channel_layer:
        return  # Channels non configuré, ne fait rien

    # Créer la notification en DB
    notif = Notification.objects.create(
        user=user,
        live=live,
        message=f"{live.compte.username} est en live : {live.titre}"
    )

    # Envoyer au groupe utilisateur
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "live_notification",
            "compte": live.compte.username,
            "titre": live.titre
        }
    )

# from notifications.models import Notification
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# from django.contrib.auth import get_user_model
# from tracking.models import Live

# User = get_user_model()

# def envoyer_notification_live(live: Live):
#     user = live.compte.user  
#     channel_layer = get_channel_layer()

#     notif = Notification.objects.create(
#         user=user,
#         live=live,
#         message=f"{live.compte.username} est en live : {live.titre}"
#     )

#     async_to_sync(channel_layer.group_send)(
#         f"user_{user.id}",
#         {
#             "type": "live_notification",
#             "compte": live.compte.username,
#             "titre": live.titre,
#         }
#     )

