from django.contrib.auth.models import User, Group

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from . import models
from . import validators

class GenreSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Genre
        fields = ['name', 'image', 'url', 'pk', 'view_count']

class LanguageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Language
        fields = ['name', 'url', 'pk', 'view_count']

class AuthorSerializer(serializers.HyperlinkedModelSerializer):

    def validate(self, attrs):
        if attrs['date_of_birth'] and attrs['date_of_death']:
            if attrs['date_of_birth'] > attrs['date_of_death']:
                raise serializers.ValidationError('Incorrect date logic assignment! '
                                                  'Check how the dates are set and reconfigure them accordingly!')
        return attrs

    class Meta:
        model = models.Author
        fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death', 'image', 'about_the_author', 'url', 'pk', 'view_count']
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
            raise serializers.ValidationError('Incorrect date logic assignment! '
                                              'Check how the dates are set and reconfigure them accordingly!')

        return attrs


    class Meta:
        model = models.Book
        fields = ['url', 'title', 'author', 'summary', 'isbn', 'genre', 'language', 'date_added', 'published',
                  'copies', 'loaned_copies', 'available_copies', 'image']

        validators = [
            UniqueTogetherValidator(
                queryset=models.Book.objects.all(),
                fields=['title', 'author']
            )
        ]

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']

class BookInstanceSerializer(serializers.HyperlinkedModelSerializer):



    class Meta:
        model = models.BookInstance
        fields = ['url', 'imprint', 'borrower', 'book', 'due_back', 'status']

    def create(self, validated_data):
        validated_data['imprint'] = 'My test borrower'
        validated_data['book_copies'] = 11
        return models.BookInstance.objects.create(**validated_data)

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email']
