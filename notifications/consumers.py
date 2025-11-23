# # notifications/consumers.py
# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class LiveNotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user = self.scope["user"]
#         if self.user.is_anonymous:
#             await self.close()
#         else:
#             self.group_name = f"user_{self.user.id}"
#             await self.channel_layer.group_add(self.group_name, self.channel_name)
#             await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)

#     async def live_notification(self, event):
#         await self.send(text_data=json.dumps({
#             "type": "live_notification",
#             "compte": event["compte"],
#             "titre": event["titre"]
#         }))

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LiveNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("lives", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("lives", self.channel_name)

    async def live_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "live_notification",
            "compte": event["compte"],
            "titre": event["titre"],
            "user_id": event.get("user_id")
        }))
