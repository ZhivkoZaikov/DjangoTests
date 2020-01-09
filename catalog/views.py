from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render
from requests import Response

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

    filter_fields = ('title', )

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAdminUser]

class BookInstanceView(viewsets.ModelViewSet):
    queryset = models.BookInstance.objects.all()
    serializer_class = serializers.BookInstanceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_fields = ('book', 'imprint')


from django.contrib import messages
from django.views.generic.edit import FormView
from django.shortcuts import redirect

from .forms import GenerateRandomUserForm
from .tasks import create_random_user_accounts

class GenerateRandomUserView(FormView):
    template_name = 'catalog/generate_random_users.html'
    form_class = GenerateRandomUserForm

    def form_valid(self, form):
        total = form.cleaned_data.get('total')
        create_random_user_accounts.delay(total)
        messages.success(self.request, 'We are generating your random users! Wait a moment and refresh this page.')
        return redirect('user-list')

