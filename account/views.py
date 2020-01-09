from django.contrib.auth.models import User, Group
from django.shortcuts import render

from rest_framework import viewsets, permissions

from . import serializers
from . import models

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by()
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAdminUser]

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAdminUser]

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = models.Profile.objects.all()
    serializer_class = serializers.ProfileSerializer
    permission_classes = [permissions.IsAdminUser]
