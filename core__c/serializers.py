from rest_framework import serializers
from core__c.models import Chatmessage
from core__a.models import User




class UserSmallSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('id','first_name', 'last_name')
    
   

class ChatMessageSerializer(serializers.ModelSerializer):
    user = UserSmallSerializer(many=False)
    class Meta:
        model = Chatmessage
        fields = '__all__'