from django.shortcuts import render

from rest_framework import generics, permissions, viewsets

from . import models
from . import serializers

class GenreView(viewsets.ModelViewSet):
    queryset = models.Genre.objects.all()
    serializer_class = serializers.GenreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_fields = ('name',)

class LanguageView(viewsets.ModelViewSet):
    queryset = models.Language.objects.all()
    serializer_class = serializers.LanguageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_fields = ('name',)

class AuthorView(viewsets.ModelViewSet):
    queryset = models.Author.objects.all()
    serializer_class = serializers.AuthorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_fields = ('first_name', 'last_name')

class BookView(viewsets.ModelViewSet):
    queryset = models.Book.objects.all()
    serializer_class = serializers.BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_fields = ('title', 'author', 'genre', 'language')

