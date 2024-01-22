from django.contrib import admin
from .models import Community, Post, Like, SavedContent, Comment, CrowdfundingCampaign, Resource, CampaignLike, CampaignComment, ResourceComment, ResourceLike, Trial, MessageNotification, TrialComment, Application, Notification, ChatGroup, Message, MessageReadStatus


# Register your models here.

admin.site.register(Community)
admin.site.register(Post)
admin.site.register(Like)
admin.site.register(SavedContent)
admin.site.register(Comment)
admin.site.register(CrowdfundingCampaign)
admin.site.register(Resource)
admin.site.register(CampaignLike)
admin.site.register(CampaignComment)
admin.site.register(ResourceComment)
admin.site.register(ResourceLike)
admin.site.register(Trial)
admin.site.register(MessageNotification)
admin.site.register(TrialComment)
admin.site.register(Application)
admin.site.register(Notification)
admin.site.register(ChatGroup)
admin.site.register(Message)
admin.site.register(MessageReadStatus)