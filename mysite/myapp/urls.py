from django.urls import path, include
from . import views
from .views import create_community_view
from .views import ctg_ensayos_view
from django.conf import settings
from django.conf.urls.static import static
from .views import delete_campaign
from .views import add_comment_to_resource, EditResourceCommentView, DeleteResourceCommentView
from .views import AddCampaignCommentView, EditCampaignCommentView, DeleteCampaignCommentView
from .views import create_trial 
from .views import UserAutocomplete, CommunityAutocomplete
from .views import AddTrialCommentView
from .views import donate_view
from .views import trial_contact
from .views import create_chat
from .views import get_chat_messages
from .views import join_chat_group
from .views import check_unread_message_notifications
from .views import EditTrialCommentView, DeleteTrialCommentView



urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('cart/', views.cart, name='cart'),
    path('notifications/', views.notifications, name='notifications'),
    path('explore/', views.explore, name='explore'),
    path('r/<str:community_name>/', views.view_community, name='view_community'),
    path('create/', create_community_view, name='create_community'),
    path('create_post/<int:community_id>/', views.create_post_view, name='create_post'),
    path('like_post/<int:post_id>/', views.like_post, name='like_post'),
    path('<str:username>/liked/', views.liked_content, name='liked_content'),
    path('<str:content_type_model>/<int:content_id>/save/', views.save_content, name='save_content'),
    path('profile/<str:username>/saved/', views.saved_content, name='saved_content'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/add_comment/', views.add_comment, name='add_comment'),
    path('profile/<str:username>/edit_profile/', views.edit_profile, name='edit_profile'),
    path('search_results/', views.search_results, name='search_results'),
    path('search_results/communities/', views.community_results, name='community_results'),
    path('search_results/users/', views.user_results, name='user_results'),
    path('search_results/posts/', views.post_results, name='post_results'),
    path('ctg_ensayos/', views.ctg_ensayos_view, name='ctg_ensayos_view'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/edit/', views.EditPostView.as_view(), name='edit_post'),
    path('crowdfunding/start/', views.create_crowdfunding_campaign, name='create_campaign'),
    path('get_campaign_data/<int:campaign_id>/', views.get_campaign_data, name='get_campaign_data'),
    path('campaign/<int:campaign_id>/edit/', views.update_campaign, name='update_campaign'),
    path('crowdfunding/<int:campaign_id>/', views.view_campaign_detail, name='view_campaign_detail'),
    path('get_post_data/<int:post_id>/', views.get_post_data, name='get_post_data'),
    path('post/<int:post_id>/content/', views.post_content, name='post_content'),
    path('edit_comment/<int:comment_id>/', views.EditCommentView.as_view(), name='edit_comment'),
    path('delete_comment/<int:comment_id>/', views.DeleteCommentView.as_view(), name='delete_comment'),
    path('post/<int:post_id>/delete/', views.DeletePostView.as_view(), name='delete_post'),
    path('crowdfunding/donate/<int:campaign_id>/', views.donate_view, name='donate_view'),
    path('like_campaign/<int:campaign_id>/', views.like_campaign, name='like_campaign'),
    path('r/<str:community_name>/posts/', views.community_posts, name='community_posts'),
    path('r/<str:community_name>/resources/', views.community_resources, name='community_resources'),
    path('r/<str:community_name>/trials/', views.community_trials, name='community_trials'),
    path('campaign/<int:campaign_id>/update_ajax/', views.update_campaign_ajax, name='update_campaign_ajax'),
    path('campaign/<int:campaign_id>/save/', views.save_campaign, name='save_campaign'),
    path('delete_campaign/<int:campaign_id>/', views.delete_campaign, name='delete_campaign'),
    path('get_campaigns/', views.get_campaigns, name='get_campaigns'),
    path('resources/add/', views.add_resource, name='add_resource'),
    path('resources/<int:resource_id>/', views.view_resource_detail, name='view_resource_detail'),
    path('resource/<int:resource_id>/comment/', add_comment_to_resource, name='add_comment_to_resource'),
    path('resource/comment/<int:comment_id>/edit/', EditResourceCommentView.as_view(), name='edit_resource_comment'),
    path('resource/comment/<int:comment_id>/delete/', DeleteResourceCommentView.as_view(), name='delete_resource_comment'),
    path('resources/', views.all_resources, name='all_resources'),
    path('resource/<int:resource_id>/update/', views.update_resource_ajax, name='update_resource_ajax'),
    path('resource/<int:resource_id>/delete/', views.delete_resource, name='delete_resource'),
    path('get_resource_data/<int:resource_id>/', views.get_resource_data, name='get_resource_data'),
    path('resource/<int:resource_id>/edit/', views.edit_resource, name='edit_resource'),
    path('like_resource/<int:resource_id>/', views.like_resource, name='like_resource'),
    path('campaign/<int:campaign_id>/comment/', AddCampaignCommentView.as_view(), name='add_campaign_comment'),
    path('campaign/comment/<int:comment_id>/edit/', EditCampaignCommentView.as_view(), name='edit_campaign_comment'),
    path('campaign/comment/<int:comment_id>/delete/', DeleteCampaignCommentView.as_view(), name='delete_campaign_comment'),
    path('crowdfunding/', views.all_crowdfunding, name='all_crowdfunding'),
    path('create_trial/', create_trial, name='create_trial'),
    path('user-autocomplete/', UserAutocomplete.as_view(), name='user-autocomplete'),
    path('community-autocomplete/', CommunityAutocomplete.as_view(), name='community-autocomplete'),
    path('trials/<int:id>/', views.trial_detail, name='view_trial_detail'),
    path('add-trial-comment/<int:trial_id>/', AddTrialCommentView.as_view(), name='add_trial_comment'),
    path('trial/comment/<int:comment_id>/edit/', EditTrialCommentView.as_view(), name='edit_trial_comment'),
    path('trial/comment/<int:comment_id>/delete/', DeleteTrialCommentView.as_view(), name='delete_trial_comment'),
    path('trials/<int:trial_id>/donate/', donate_view, name='donate_view'),
    path('trials/<int:trial_id>/contact/', trial_contact, name='trial_contact'),
    path('get_application_details/<int:application_id>/', views.get_application_details, name='get_application_details'),
    path('paypal/', include('paypal.standard.ipn.urls')), 
    path('trials/<int:trial_id>/update_donation/', views.update_donation, name='update_donation'),
    path('trials/edit/<int:id>/', views.edit_trial, name='edit_trial'),
    path('create-chat/', create_chat, name='create_chat'),
    path('trials/', views.all_trials, name='all_trials'),
    path('get-chat-messages/<int:chat_group_id>/', get_chat_messages, name='get_chat_messages'),
    path('send-message/<int:chat_group_id>/', views.send_message, name='send_message'),
    path('messages/', views.messages, name='messages'),
    path('messages/<int:chat_group_id>/', views.messages, name='messages_with_id'),
    path('start-chat/<str:username>/', views.start_chat, name='start_chat'),
    path('join-chat-group/<int:chat_group_id>/', join_chat_group, name='join_chat_group'),
    path('get-chat-group-info/<int:chat_group_id>/', views.get_chat_group_info, name='get_chat_group_info'),
    path('chat-action/<int:chat_group_id>/', views.chat_action, name='chat_action'),
    path('get-chat-group-members/<int:chat_group_id>/', views.get_chat_group_members, name='get_chat_group_members'),
    path('check-unread-message-notifications/', check_unread_message_notifications, name='check_unread_message_notifications'),
    path('mark-messages-as-read/<int:chat_group_id>/', views.mark_messages_as_read, name='mark_messages_as_read'),
]
    

    


    # ... tus otras urls ...
    

  






    



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)