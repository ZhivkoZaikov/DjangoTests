from django.contrib.auth.models import User, Group
from rest_framework import serializers

from . import models

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class ProfileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.Profile
        fields = ['url', 'user', 'short_description', 'birth_date', 'image', 'country', 'town', 'address',
                  'phone_number',]
