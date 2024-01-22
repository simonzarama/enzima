def user_notifications(request):
    return {
        'notifications_unread': request.user.is_authenticated and request.user.notification_set.filter(is_read=False).exists()
    }

from .models import MessageNotification

def unread_messages(request):
    if request.user.is_authenticated:
        has_unread_messages = MessageNotification.objects.filter(user=request.user, is_read=False).exists()
        return {'messages_unread': has_unread_messages}
    return {'messages_unread': False}


from django.conf import settings

def profile_picture(request):
    if request.user.is_authenticated:
        return {'profile_picture_url': request.user.userprofile.profile_picture.url if request.user.userprofile.profile_picture else settings.STATIC_URL + 'myapp/images/default_profile_icon.png'}
    return {}