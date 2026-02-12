# mylogin/consumers.py
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from django.utils import timezone

from mylogin.models import ChatThread, ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # ดึง thread_id จาก URL: ws/chat/<thread_id>/
        self.thread_id = int(self.scope['url_route']['kwargs']['thread_id'])
        self.room_group_name = f"chat_thread_{self.thread_id}"

        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        # เช็กว่า user อยู่ใน thread นี้จริงไหม (ต้องเป็น owner หรือ customer)
        allowed = await self.user_in_thread(user.id, self.thread_id)
        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "").strip()
        if not message:
            return

        user = self.scope["user"]
        display_name = user.get_full_name() or user.email or "Unknown"

        # บันทึกข้อความลง DB + อัปเดต updated_at ของ thread
        msg = await self.save_message(user, message)

        # ใช้เวลาจริงจาก DB (localtime) แล้ว format เป็น HH:MM
        ts = timezone.localtime(msg.timestamp)
        timestamp_str = ts.strftime("%H:%M")

        # ส่งให้ทั้งสองฝั่งในห้อง
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": display_name,
                "timestamp": timestamp_str,
            }
        )

    async def chat_message(self, event):
        # ส่งกลับไปให้ frontend
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "username": event["username"],
            "timestamp": event["timestamp"],
        }))

    @database_sync_to_async
    def user_in_thread(self, user_id, thread_id):
        """เช็กว่า user คนนั้นอยู่ใน thread นี้หรือเปล่า"""
        return ChatThread.objects.filter(
            id=thread_id
        ).filter(
            Q(customer_id=user_id) | Q(owner_id=user_id)
        ).exists()

    @database_sync_to_async
    def save_message(self, user, content):
        """สร้าง ChatMessage ใหม่ใน thread นี้ แล้วอัปเดตเวลา updated_at ของ thread"""
        thread = ChatThread.objects.get(pk=self.thread_id)
        msg = ChatMessage.objects.create(
            thread=thread,
            sender=user,
            content=content
        )
        # อัปเดตเวลาแก้ไขล่าสุดของห้องแชท
        thread.updated_at = timezone.now()
        thread.save(update_fields=["updated_at"])
        return msg
