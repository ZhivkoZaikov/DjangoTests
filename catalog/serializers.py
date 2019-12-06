from django.contrib.auth.models import User, Group

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from . import models
from . import validators

class GenreSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Genre
        fields = ['name', 'image', 'url', 'pk']

class LanguageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Language
        fields = ['name', 'url', 'pk']

class AuthorSerializer(serializers.HyperlinkedModelSerializer):

    def validate(self, attrs):
        if attrs['date_of_birth'] > attrs['date_of_death']:
            raise serializers.ValidationError('Incorrect date assignment! Date of birth must be before date of death!')
        return attrs

    class Meta:
        model = models.Author
        fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death', 'image', 'about_the_author', 'url', 'pk']
        validators = [
            UniqueTogetherValidator(
                queryset=models.Author.objects.all(),
                fields = ['first_name', 'last_name'],
            ),

        ]

class BookSerializer(serializers.HyperlinkedModelSerializer):

    def validate(self, attrs):
        total_number = attrs['available_copies'] + attrs['loaned_copies']
        if attrs['copies'] != total_number:
            raise serializers.ValidationError('Incorrect values. '
                            'Total copies should match the aggregate of available and loaned copies')
        if attrs['published'] > attrs['date_added']:
            raise serializers.ValidationError('Incorrect date assignment! '
                        'Published book date cannot be newer than the date it is added to the store!')

        return attrs


    class Meta:
        model = models.Book
        fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language', 'date_added', 'published',
                  'copies', 'loaned_copies', 'available_copies', 'image']
