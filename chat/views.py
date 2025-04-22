import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Max, F, Q
from .models import ChatSession, ChatMessage
import uuid

@staff_member_required
def staff_chat_dashboard(request):
    """Admin chat dashboard view"""
    # Get active chat sessions with unread count
    chat_sessions = ChatSession.objects.filter(is_active=True).annotate(
        unread_count=Count('messages', filter=Q(messages__sender='visitor', messages__is_read=False)),
        last_message_time=Max('messages__timestamp')
    ).order_by('-last_message_time')
    
    return render(request, 'chat/staff_chat.html', {
        'chat_sessions': chat_sessions,
    })

class ChatSessionDetailView(View):
    @method_decorator(staff_member_required)
    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id)
            messages = session.messages.all()
            
            return JsonResponse({
                'success': True,
                'session': {
                    'id': session.id,
                    'visitor_id': session.visitor_id,
                    'created_at': session.created_at.isoformat(),
                    'name': session.get_display_name(),
                    'user_email': session.user_email,
                    'is_authenticated': bool(session.user)
                },
                'messages': [
                    {
                        'id': msg.id,
                        'message': msg.message,
                        'sender': msg.sender,
                        'is_read': msg.is_read,
                        'timestamp': msg.timestamp.isoformat()
                    } for msg in messages
                ]
            })
        except ChatSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Chat session not found'
            }, status=404)

class MarkMessagesReadView(View):
    @method_decorator(staff_member_required)
    @method_decorator(csrf_exempt)
    def post(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id)
            # Mark all visitor messages as read
            session.messages.filter(sender='visitor', is_read=False).update(is_read=True)
            
            return JsonResponse({
                'success': True,
                'marked_count': session.messages.filter(sender='visitor', is_read=True).count()
            })
        except ChatSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Chat session not found'
            }, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class SendMessageView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            message = data.get('message')
            sender = data.get('sender')
            
            if not all([session_id, message, sender]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields'
                })
            
            # Get session
            try:
                session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Chat session not found'
                })
            
            # Create message
            chat_message = ChatMessage.objects.create(
                session=session,
                message=message,
                sender=sender,
                is_read=(sender == 'agent')  # Agent messages are auto-read
            )
            
            # Update session timestamp
            session.save()  # This will update the updated_at field
            
            # Send to WebSocket channel
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'chat_{session_id}',
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender': sender,
                        'timestamp': chat_message.timestamp.isoformat()
                    }
                )
                print(f"Message sent to channel: chat_{session_id}")
            except Exception as e:
                print(f"Error sending to channel: {e}")
            
            return JsonResponse({
                'success': True,
                'message_id': chat_message.id,
                'timestamp': chat_message.timestamp.isoformat()
            })
        except Exception as e:
            print(f"Error in SendMessageView: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class InitChatView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            visitor_id = data.get('visitor_id')
            
            if not visitor_id:
                visitor_id = str(uuid.uuid4())
            
            # Create or get session
            session, created = ChatSession.objects.get_or_create(
                visitor_id=visitor_id,
                is_active=True
            )
            
            # Update user information if user is logged in
            if request.user.is_authenticated:
                session.user = request.user
                session.user_name = request.user.get_full_name() or request.user.username
                session.user_email = request.user.email
                session.save()
            
            if created:
                # Add welcome message
                ChatMessage.objects.create(
                    session=session,
                    message="Hello! 👋 How can we help you today?",
                    sender="agent",
                    is_read=True
                )
            
            # Get messages
            messages = session.messages.all()
            
            return JsonResponse({
                'success': True,
                'visitor_id': visitor_id,
                'session_id': session.id,
                'user_name': session.get_display_name(),
                'messages': [
                    {
                        'message': msg.message,
                        'sender': msg.sender,
                        'timestamp': msg.timestamp.isoformat()
                    } for msg in messages
                ]
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
