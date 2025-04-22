import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatSession, ChatMessage
import uuid
from datetime import datetime

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        print(f"WebSocket connected: {self.session_id}")
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected: {self.session_id}, code: {close_code}")
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        print(f"Received message: {text_data}")
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json['sender']
        visitor_id = text_data_json.get('visitor_id')
        timestamp = text_data_json.get('timestamp', datetime.now().isoformat())
        
        # Save message to database
        await self.save_message(self.session_id, visitor_id, message, sender)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
                'timestamp': timestamp
            }
        )
    
    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event.get('timestamp')
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp': timestamp
        }))
    
    @database_sync_to_async
    def save_message(self, session_id, visitor_id, message, sender):
        try:
            # Get or create chat session
            session = ChatSession.objects.get(id=session_id)
            
            # Update session if visitor_id is provided
            if visitor_id and not session.visitor_id:
                session.visitor_id = visitor_id
                session.save()
                
            # Create message
            ChatMessage.objects.create(
                session=session,
                message=message,
                sender=sender
            )
            
            # Update session timestamp
            session.save()  # This will update the updated_at field
            
            print(f"Message saved to database: {message}")
            return True
        except ChatSession.DoesNotExist:
            print(f"Session not found: {session_id}")
            # Create new session if it doesn't exist
            session = ChatSession.objects.create(
                id=session_id,
                visitor_id=visitor_id or str(uuid.uuid4()),
                is_active=True
            )
            
            # Create message
            ChatMessage.objects.create(
                session=session,
                message=message,
                sender=sender
            )
            
            print(f"Created new session and saved message: {message}")
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
