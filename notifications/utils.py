from notifications.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from tracking.models import Live

User = get_user_model()

def envoyer_notification_live(live: Live):
    users = User.objects.all()  # ou filtrer selon les abonnements
    channel_layer = get_channel_layer()

    for user in users:
        notif = Notification.objects.create(
            user=user,
            live=live,
            message=f"Live en cours : {live.compte.username} - {live.titre}"
        )
        async_to_sync(channel_layer.group_send)(
            "lives",
            {
                "type": "live_notification",
                "compte": live.compte.username,
                "titre": live.titre,
                "user_id": user.id
            }
        )
