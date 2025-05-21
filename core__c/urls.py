from django.urls import path

from core__c.views import ChatListView

urlpatterns = [
    path('users-list/', ChatListView.as_view(), name='chat-list'),
]
