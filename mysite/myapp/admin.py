from django.contrib import admin
from .models import Community, Post, Like, SavedContent, Comment, CrowdfundingCampaign, Resource, CampaignLike, CampaignComment, ResourceComment, ResourceLike


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