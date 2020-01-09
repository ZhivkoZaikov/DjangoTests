import datetime

from django.db.models import Q
from django.db.utils import IntegrityError
from django.db import transaction

from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from django.utils.http import urlencode
import json

from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.authtoken.models import Token

from . import views
from .models import Genre, Language, Author, Book

class MainModelsTestCase(APITestCase):

    def create_object(self, data, model_name):
        counter = model_name.objects.count()

        new_object = model_name()
        for field, value in data.items():
            if not isinstance(value, list):
                setattr(new_object, field, value)

        new_object.save()

        for field, key in data.items():
            self.assertEqual(getattr(new_object, field), key)

        # self.assertEqual(str(new_object), new_object.name)
        # self.assertEqual(new_object.__str__(), new_object.name)
        self.assertEqual(model_name.objects.count(), (counter+1))
        self.assertTrue(isinstance(new_object, model_name))
        self.assertEqual(new_object.view_count, 0)

        return new_object

    def update_object(self, data, new_data, model_name):
        get_model_object = model_name.objects.get(**data)

        for field, key in new_data.items():
            setattr(get_model_object, field, key)
        get_model_object.save()

        for field, key in new_data.items():
            self.assertEqual(getattr(get_model_object, field), key)

        return get_model_object

    def remove_object(self, data, model_name):
        counter = model_name.objects.count()
        object_get = model_name.objects.get(**data)
        object_get.delete()
        self.assertEqual(model_name.objects.count(), (counter - 1))

    def update_object_to_existing_one(self,data, updated_data, model_name):

        original_object_name = model_name.objects.get(**data)

        with transaction.atomic():
            for field, key in updated_data.items():
                setattr(original_object_name, field, key)
            self.assertRaises(IntegrityError, original_object_name.save())

    def create_existing_object(self, data, model_name):

        counter = model_name.objects.count()
        duplicated_object = model_name(**data)

        with transaction.atomic():
            self.assertRaises(IntegrityError, duplicated_object.save)
        self.assertEqual(model_name.objects.count(), counter)

    def create_book_object(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}


        new_genre_obj = self.create_object({'name': 'New Genre Name'}, Genre)
        new_genre_two_obj = self.create_object({'name': 'Second Genre Name'}, Genre)
        new_language_obj = self.create_object({'name': 'New Language Name'}, Language)
        new_author_obj = self.create_object(data_author, Author)


        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genred = Genre.objects.all()

        book_data = {'title': 'Book of John', 'author': new_author_obj, 'id': 1,
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': new_language_obj} #, 'genre': genred

        new_book_object = Book(**book_data)

        new_book_object.genre.set(genred)
        new_book_object.save()

        for key, field in book_data.items():
            self.assertEqual(book_data[key], getattr(new_book_object, key))

        assert Book.objects.get().pk == 1

        return new_book_object

class GenreModelsTest(MainModelsTestCase):

    def test_genre_create(self):
        new_obj = self.create_object({'name': 'New Genre Name'}, Genre)

        self.assertEqual(str(new_obj), new_obj.name)
        self.assertEqual(new_obj.__str__(), new_obj.name)
        self.assertEqual(new_obj.get_absolute_url(), f'/{new_obj._meta.model_name}/{new_obj.pk}/')

    def test_genre_update(self):
        name = 'New Genre Name'
        update_name = 'Updated Genre'
        self.create_object({'name': name}, Genre)
        new_obj = self.update_object({'name': name}, {'name': update_name}, Genre)

        self.assertEqual(str(new_obj), new_obj.name)
        self.assertEqual(new_obj.__str__(), new_obj.name)

        # get_model_object = Genre.objects.get(name=name)
        #
        # new_view_count = 3
        # new_name = 'name_is_updated'
        #
        # get_model_object.name = new_name
        # get_model_object.view_count = new_view_count
        #
        # self.assertEqual(get_model_object.name, new_name)
        # self.assertEqual(get_model_object.view_count, new_view_count)

    def test_genre_remove(self):
        name = 'New Genre Name'
        self.create_object({'name': 'New Genre Name'}, Genre)
        self.remove_object({'name': 'New Genre Name'}, Genre)

        # counter = Genre.objects.count()
        # genre = Genre.objects.get(name=name)
        # genre.delete()
        # self.assertEqual(Genre.objects.count(), (counter - 1))

    def test_update_genre_to_existing_one(self):
        name = 'New Genre Name'
        second_genre = 'Second genre name'
        first_object = self.create_object({'name': name}, Genre)
        second_object = self.create_object({'name': second_genre}, Genre)

        self.update_object_to_existing_one({'name': name}, {'second_object': second_genre}, Genre)

        # update_genre_name = Genre.objects.get(name=name)
        #
        # with transaction.atomic():
        #     update_genre_name.name = second_genre
        #     self.assertRaises(IntegrityError, update_genre_name.save)

    def test_create_existing_genre(self):
        name = 'New Genre Name'
        self.create_object({'name': name}, Genre)
        self.create_existing_object({'name': name}, Genre)
        # duplicated_object = Genre(name=name)
        # with transaction.atomic():
        #     self.assertRaises(IntegrityError, duplicated_object.save)
        # self.assertEqual(Genre.objects.count(), 1)

class LanguageModelTest(MainModelsTestCase):

    def test_create_language(self):
        new_obj = self.create_object({'name': 'New Language Name'}, Language)

        self.assertEqual(str(new_obj), new_obj.name)
        self.assertEqual(new_obj.__str__(), new_obj.name)

    def test_language_update(self):
        name = 'New Language Name'
        update_name = 'Updated Language'
        self.create_object({'name': name}, Language)
        new_obj = self.update_object({'name': name}, {'name': update_name}, Language)

        self.assertEqual(str(new_obj), new_obj.name)
        self.assertEqual(new_obj.__str__(), new_obj.name)

    def test_language_remove(self):
        name = 'New Language Name'
        self.create_object({'name': 'New Language Name'}, Language)
        self.remove_object({'name': 'New Language Name'}, Language)

    def test_language_update_existing(self):

        data = {'name': 'New Language Name', }
        updated_data = {'second_object': 'New Language Name', }
        self.create_object(data, Language)
        self.create_object(updated_data, Language)
        self.update_object_to_existing_one(data, updated_data, Language)

    def test_create_existing_object(self):
        name = 'New Language Name'
        self.create_object({'name': name}, Language)
        self.create_existing_object({'name': name}, Language)

class AuthorModelTest(MainModelsTestCase):

    def test_create_author(self):
        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        new_obj = self.create_object(data, Author)

        self.assertEqual(str(new_obj), f'{new_obj.first_name}, {new_obj.last_name}')
        self.assertEqual(new_obj.__str__(), f'{new_obj.first_name}, {new_obj.last_name}')
        self.assertEqual(new_obj.get_name(), f'{new_obj.last_name}, {new_obj.first_name}')

    def test_update_author(self):
        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        updated_data = {'first_name': 'John Update', 'about_the_author': 'XXX Info Update',
                        'last_name': 'Doe Update', 'date_of_birth': '2005-12-21', 'date_of_death': '2015-11-14'}
        self.create_object(data, Author)
        new_obj = self.update_object(data, updated_data, Author)

        self.assertEqual(str(new_obj), f'{new_obj.first_name}, {new_obj.last_name}')
        self.assertEqual(new_obj.__str__(), f'{new_obj.first_name}, {new_obj.last_name}')
        self.assertEqual(new_obj.get_name(), f'{new_obj.last_name}, {new_obj.first_name}')

    def test_author_remove(self):
        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}
        self.create_object(data, Author)
        self.remove_object(data, Author)

    def test_update_author_to_existing_one(self):
        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        updated_data = {'first_name': 'John Update', 'about_the_author': 'XXX Info Update',
                        'last_name': 'Doe Update', 'date_of_birth': '2005-12-21', 'date_of_death': '2015-11-14'}

        self.create_object(data, Author)
        self.create_object(updated_data, Author)

        # this does not work, probbaly because the unique constaint is declared in Meta:
        # self.update_object_to_existing_one(data, updated_data, Author)

        original_object_name = Author.objects.get(**data)

        with transaction.atomic():
            for field, key in updated_data.items():
                setattr(original_object_name, field, key)
            self.assertRaises(IntegrityError, original_object_name.save)

    def test_create_existing_author(self):
        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}
        self.create_object(data, Author)

        counter = Author.objects.count()

        new_object = Author()
        for field, value in data.items():
            if not isinstance(value, list):
                setattr(new_object, field, value)

        with transaction.atomic():
            with self.assertRaises(Exception) as raised:
                new_object.save()
            self.assertEqual(IntegrityError, type(raised.exception))

        self.assertEqual(Author.objects.count(), counter)

    def test_create_author_incorrect_birth_date(self):

        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-xx-21', 'date_of_death': '2011-11-14'}
        check_date = data['date_of_birth']
        new_object = Author()
        for field, value in data.items():
            if not isinstance(value, list):
                setattr(new_object, field, value)

        with transaction.atomic():
            with self.assertRaises(Exception) as raised:
                new_object.save()
            self.assertEqual(DjangoValidationError, type(raised.exception))
            error_message = f"'{check_date}' value has an invalid date format. It must be in YYYY-MM-DD format."
            self.assertIn(error_message, raised.exception)
        self.assertEqual(Author.objects.count(), 0)

    def test_create_author_incorrect_date_of_death(self):

        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-03-21', 'date_of_death': '20xx-11-14'}
        check_date = data['date_of_death']
        new_object = Author()
        for field, value in data.items():
            if not isinstance(value, list):
                setattr(new_object, field, value)

        with transaction.atomic():
            with self.assertRaises(Exception) as raised:
                new_object.save()
            self.assertEqual(DjangoValidationError, type(raised.exception))
            error_message = f"'{check_date}' value has an invalid date format. It must be in YYYY-MM-DD format."
            self.assertIn(error_message, raised.exception)
        self.assertEqual(Author.objects.count(), 0)

    def test_create_author_birth_date_in_future(self):

        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2020-03-21', 'date_of_death': '2011-03-14'}

        check_date = data['date_of_death']

        new_object = Author()
        for field, value in data.items():
            # if not isinstance(value, list):
                setattr(new_object, field, value)

        # with transaction.atomic():
        #     with self.assertRaises(RestValidationError) as raised:
        #         new_object.full_clean()
        #     self.assertEqual(RestValidationError, type(raised.exception))
        #     error_message = f"'{check_date}' value has an invalid date format. It must be in YYYY-MM-DD format."
        # self.assertEqual(Author.objects.count(), 0)

        # this should be sufficient too
        # with transaction.atomic():
        #     self.assertRaises(IntegrityError, new_object.save())

        try:
            new_object.full_clean()
        except RestValidationError as e:
            self.assertEqual(e.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('Invalid date logic declaration! Check the dates and reconfigure them accordingly!', e.args)

    def test_create_author_date_of_death_in_future(self):

        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-03-21', 'date_of_death': '2021-03-14'}

        check_date = data['date_of_death']

        new_object = Author()
        for field, value in data.items():
            if not isinstance(value, list):
                setattr(new_object, field, value)

        try:
            new_object.full_clean()
        except RestValidationError as e:
            self.assertEqual(e.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('Invalid date logic declaration! Check the dates and reconfigure them accordingly!', e.args)

    def test_create_author_birth_date_after_date_of_death(self):
        # as this validation is declared in the serializer, it should be tested in the serializer tests?``
        pass

class BookModelTest(MainModelsTestCase):

    def test_create_book(self):
        self.create_book_object()
        # data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
        #                 'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}
        #
        #
        # new_genre_obj = self.create_object({'name': 'New Genre Name'}, Genre)
        # new_genre_two_obj = self.create_object({'name': 'Second Genre Name'}, Genre)
        # new_language_obj = self.create_object({'name': 'New Language Name'}, Language)
        # new_author_obj = self.create_object(data_author, Author)
        #
        #
        # published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        # date_added = datetime.date.today()
        # genred = Genre.objects.all()
        #
        # book_data = {'title': 'Book of John', 'author': new_author_obj, 'id': 1,
        #     'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
        #     'date_added': date_added, 'language': new_language_obj} #, 'genre': genred
        #
        # new_book_object = Book(**book_data)
        #
        # new_book_object.genre.set(genred)
        # new_book_object.save()
        #
        # for key, field in book_data.items():
        #     self.assertEqual(book_data[key], getattr(new_book_object, key))
        #
        # assert Book.objects.get().pk == 1
        #
        # return new_book_object

    def test_update_book(self):
        new_book_object = self.create_book_object()

        #Book is now created, we will update it below:

        #updated values
        data_author_updated = {'first_name': 'John update', 'about_the_author': 'XXX Info update',
                        'last_name': 'Doe update', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        new_genre_obj_update = self.create_object({'name': 'New Genre update Name'}, Genre)
        new_genre_two_obj_update = self.create_object({'name': 'Second Genre update Name'}, Genre)
        new_language_obj_update = self.create_object({'name': 'New Language update Name'}, Language)
        new_author_obj_update = self.create_object(data_author_updated, Author)


        published_date_update = datetime.date.today() - datetime.timedelta(weeks=15)
        date_added_update = datetime.date.today()
        genred_update = [new_genre_obj_update, new_genre_two_obj_update]

        book_data_update = {'title': 'Book of John update', 'author': new_author_obj_update, 'id': 1,
            'summary': 'Doe update', 'copies': 30, 'loaned_copies': 0, 'available_copies': 30, 'published': published_date_update,
            'date_added': date_added_update, 'language': new_language_obj_update} #, 'genre': genred

        for field, key in book_data_update.items():
            setattr(new_book_object, field, key)
        new_book_object.save()

        for key, field in book_data_update.items():
            self.assertEqual(book_data_update[key], getattr(new_book_object, key))

        assert Book.objects.count() == 1

    def test_delete_book(self):
        new_book_object = self.create_book_object()

        new_book_object.delete()

        assert Book.objects.count() == 0

    def test_create_book_published_date_in_future(self):

        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        # initial values
        new_genre_obj = self.create_object({'name': 'New Genre Name'}, Genre)
        new_genre_two_obj = self.create_object({'name': 'Second Genre Name'}, Genre)
        new_language_obj = self.create_object({'name': 'New Language Name'}, Language)
        new_author_obj = self.create_object(data_author, Author)


        # published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        published_date = datetime.date.today() + datetime.timedelta(days=1)
        date_added = datetime.date.today()
        # genred = [new_genre_obj, new_genre_two_obj]

        genred = Genre.objects.all()
        book_data = {'title': 'Book of John', 'author': new_author_obj, 'id': 1,
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': new_language_obj} #, 'genre': genred

        new_book_object = Book(**book_data)

        # many to many fields should be added once the instance is created?
        new_book_object.genre.set(genred)
        # new_book_object.full_clean()
        new_book_object.save()

        # with transaction.atomic():
        #     with self.assertRaises(RestValidationError) as raised:
        #         new_book_object.full_clean()
        #     self.assertEqual(RestValidationError, type(raised.exception))
        #     error_message = 'Invalid date logic declaration! Check the dates and reconfigure them accordingly!'
        #     self.assertIn(error_message, raised.exception)
        #     print(raised.exception)

        try:
            new_book_object.full_clean()
        except RestValidationError as e:
            self.assertEqual(e.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('Invalid date logic declaration! Check the dates and reconfigure them accordingly!', e.args)


        #     error_message = f"'{check_date}' value has an invalid date format. It must be in YYYY-MM-DD format."
        # self.assertEqual(Author.objects.count(), 0)

        # for key, field in book_data.items():
        #     print(field)
        #     self.assertEqual(book_data[key], getattr(new_book_object, key))

        # this is happening as the validation is set in validators.py which does not take effect
        # when testing models???
        assert Book.objects.count() == 1

    def test_create_book_date_added_in_future(self):

        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}


        new_genre_obj = self.create_object({'name': 'New Genre Name'}, Genre)
        new_genre_two_obj = self.create_object({'name': 'Second Genre Name'}, Genre)
        new_language_obj = self.create_object({'name': 'New Language Name'}, Language)
        new_author_obj = self.create_object(data_author, Author)


        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today() + datetime.timedelta(days=1)
        genred = Genre.objects.all()

        book_data = {'title': 'Book of John', 'author': new_author_obj, 'id': 1,
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': new_language_obj} #, 'genre': genred

        new_book_object = Book(**book_data)

        new_book_object.genre.set(genred)
        new_book_object.save()

        for key, field in book_data.items():
            self.assertEqual(book_data[key], getattr(new_book_object, key))

        assert Book.objects.get().pk == 1

        try:
            new_book_object.full_clean()
        except RestValidationError as e:
            self.assertEqual(e.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('Invalid date logic declaration! Check the dates and reconfigure them accordingly!', e.args)

    def test_create_book_date_added_incorrect(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        # initial values
        new_genre_obj = self.create_object({'name': 'New Genre Name'}, Genre)
        new_genre_two_obj = self.create_object({'name': 'Second Genre Name'}, Genre)
        new_language_obj = self.create_object({'name': 'New Language Name'}, Language)
        new_author_obj = self.create_object(data_author, Author)


        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = '2000-xx-21'
        genred = [new_genre_obj, new_genre_two_obj]

        book_data = {'title': 'Book of John', 'author': new_author_obj, 'id': 1,
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': new_language_obj} #, 'genre': genred

        new_object = Book()
        for field, value in book_data.items():
            if not isinstance(value, list):
                setattr(new_object, field, value)

        with transaction.atomic():
            with self.assertRaises(Exception) as raised:
                new_object.save()
            self.assertEqual(DjangoValidationError, type(raised.exception))
            error_message = f"'{date_added}' value has an invalid date format. It must be in YYYY-MM-DD format."
            self.assertIn(error_message, raised.exception)
        self.assertEqual(Book.objects.count(), 0)

    def test_create_book_published_date_incorrect(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        # initial values
        new_genre_obj = self.create_object({'name': 'New Genre Name'}, Genre)
        new_genre_two_obj = self.create_object({'name': 'Second Genre Name'}, Genre)
        new_language_obj = self.create_object({'name': 'New Language Name'}, Language)
        new_author_obj = self.create_object(data_author, Author)


        published_date = '20xx-12-21'
        date_added = datetime.date.today()
        genred = [new_genre_obj, new_genre_two_obj]

        book_data = {'title': 'Book of John', 'author': new_author_obj, 'id': 1,
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': new_language_obj} #, 'genre': genred

        new_object = Book()
        for field, value in book_data.items():
            if not isinstance(value, list):
                setattr(new_object, field, value)

        with transaction.atomic():
            with self.assertRaises(Exception) as raised:
                new_object.save()
            self.assertEqual(DjangoValidationError, type(raised.exception))
            error_message = f"'{published_date}' value has an invalid date format. It must be in YYYY-MM-DD format."
            self.assertIn(error_message, raised.exception)
        self.assertEqual(Book.objects.count(), 0)

# =======================================================
#  MODELS TESTS END HERE!!! FROM NOW ON VIEW TESTS!!!
# =======================================================

class MainTestCase(APITestCase):

    def create_user_and_set_token_credentials(self, username='test', email="test@test.com", password="test"):

        self.user = User.objects.create_user(username=username, email=email, password=password)
        self.c = Client()
        self.c.login(username=username, password=password)

    def post_category_by_authenticated_user(self, data, url, model_name):

        self.create_user_and_set_token_credentials()
        response = self.c.post(reverse(f'{url}'), data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert model_name.objects.count() == 1

        for each_key in data:
            assert data[each_key] == response.data[each_key]
            # print(f'{data[each_key]} == {response.data[each_key]}')

        # convert the binary responce into dictionary and
        # check if the data used for this function matches the data in the created object
        # for i in response:
        #     # print(i)
        #     jsonResponse = json.loads(i)
        #     # print(jsonResponse)
        #     for i in data:
        #         assert data[i] == jsonResponse[i]
        #         # print(jsonResponse[i])

        return response

    def post_duplicated_category(self, data, url_list):

        response = self.c.post(reverse(url_list), data, format='json')
        # print(f'The status code of the {name} category is {response.status_code} '
        #       f'and should be 400 as such category exists')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        return response

    # presumably you have already used
    # self.create_user_and_set_token_credentials()
    # in tests and using it again would throw an error
    # in this case use the below function to create another category
    def post_another_category(self, data, url_list, model_name):
        count_objects = model_name.objects.count()
        response = self.c.post(reverse(url_list), data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert model_name.objects.count() == count_objects + 1
        return response

    def post_category_by_unanimous_user(self, data, url, model_name):

        url = reverse(f'{url}')
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert model_name.objects.count() == 0
        return response

    def post_category_by_authenticated_user_incorrect_date_format(self, data, url, model_name):
        '''Check for incorrect date declaration'''
        self.create_user_and_set_token_credentials()
        response = self.c.post(reverse(f'{url}'), data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert model_name.objects.count() == 0

        for key in response.data.keys():
            assert 'Date has wrong format' in response.data[key][0]

        return response

    def date_in_the_future(self, data, url_lst, model_name):
        '''Check if a date would be declared incorrectly in te future'''
        self.create_user_and_set_token_credentials()
        response = self.c.post(reverse(f'{url_lst}'), data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert model_name.objects.count() == 0

        invalid_message = 0
        for key in response.data.keys():
            invalid_message +=1
            # print(response.data[key])
            # print(response.data[key][0])
            # print('Date has wrong format' in response.data[key][0])
            assert 'Invalid date' in response.data[key][0]
        assert invalid_message == 1
        return response

    def second_date_comes_first_incorrect(self, data, url_list, model_name):
        '''Check for incorrect date assignment logic, e.g. date of death is before date of birth'''
        self.create_user_and_set_token_credentials()
        response = self.c.post(reverse(f'{url_list}'), data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert model_name.objects.count() == 0

        for key in response.data.keys():
            assert 'Incorrect date logic assignment! Check how the dates are set and reconfigure them accordingly!' in response.data[key][0]

        return response

    def update_category_by_unanimous_user(self, data, url_detail, model_name):
        response_update_by_unanimous_user = self.client.patch(reverse(url_detail, None,
                                {model_name.objects.get().pk}), data, content_type='application/json')
        assert response_update_by_unanimous_user.status_code == status.HTTP_401_UNAUTHORIZED
        assert model_name.objects.get().id == 1

        return response_update_by_unanimous_user

    def update_category_by_authenticated_user(self, data, url_detail, model_name):

        response_update = self.c.patch(reverse(url_detail, None, {model_name.objects.get().pk}), data,
                                       content_type='application/json')

        assert response_update.status_code == status.HTTP_200_OK
        assert model_name.objects.get().id == 1

        url_get_genre = reverse(url_detail, None, {model_name.objects.get().pk})
        get_responce = self.client.get(url_get_genre, format='json')
        assert get_responce.status_code == status.HTTP_200_OK

        return response_update

    def get_category(self, data, url, model_name):
        response_get = self.client.get(reverse(f'{url}'), data, format='json')
        # print(response_get.data)
        assert response_get.status_code == status.HTTP_200_OK
        assert model_name.objects.get().id == 1

    def post_and_get_category(self, data, url_list, model_name):

        self.post_category_by_authenticated_user(data, url_list, model_name)
        self.get_category(data, url_list, model_name)

    def filter_existing_category(self, data, url_list):
        genre_filter_name = data
        url = f'{reverse(url_list)}?{urlencode(genre_filter_name)}'
        response_filter = self.client.get(url, format='json')

        assert response_filter.status_code == status.HTTP_200_OK
        # assert response_filter.data[0]['name'] == name
        # print(response_filter.data)
        # print(data)
        for key in data:
            assert data[key] == response_filter.data[0][key]
            # print(key)



        try:
            assert response_filter.data[1].exists() == True
            assert False
        except IndexError:
            assert True

        return response_filter

    def filter_non_existing_category(self, data, url_list):
        genre_filter_name = data
        url = f'{reverse(url_list)}?{urlencode(genre_filter_name)}'
        response_filter_non_exist = self.client.get(url, format='json')

        # Although we search for non existing category the code so far returns HTTP 200 OK with no results
        assert response_filter_non_exist.status_code == status.HTTP_200_OK
        for non_results in response_filter_non_exist.data:
            assert non_results == None
        return response_filter_non_exist

    def delete_category(self, pk, url_detail, model_name):

        count_objects = model_name.objects.count()

        url = reverse(url_detail, kwargs={'pk': model_name.objects.get(pk=pk).pk})
        response_delete = self.c.delete(url)

        assert response_delete.status_code == status.HTTP_204_NO_CONTENT
        assert model_name.objects.count() == count_objects - 1

    def delete_non_existing_category(self, pk, url_detail, model_name):

        count_objects = model_name.objects.count()
        try:
            url = reverse(url_detail, kwargs={'pk': model_name.objects.get(pk=pk).pk})
            response_delete = self.c.delete(url)
            assert False
        except model_name.DoesNotExist:
            assert True

        assert model_name.objects.count() == count_objects

class LanguageCategoryApiTest(MainTestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = views.LanguageView.as_view({'get': 'list'})
        self.uri = '/language/'

    def test_get_category(self):
        request = self.factory.get(self.uri)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                'Expected Response Code 200, received {0} instead.'.format(response.status_code))

    def test_post_by_unauthorized_user(self):
        pass

    def test_post_by_authenticated_user(self):
        pass

    def test_update_category_by_unanimous_user(self):
        pass

    def test_update_category_by_authorized_user(self):
        pass

    def test_post_category_which_already_exists(self):
        pass

    def test_filter_category(self):
        pass

    def test_delete_category(self):
        pass

class LanguageCategoryTest(MainTestCase):

    def test_post_and_get_category(self):
        self.post_and_get_category({'name': 'Spanish'}, 'language-list', Language)

    def test_post_by_unauthorized_user(self):
        self.post_category_by_unanimous_user({'name': 'Bengal'}, 'language-list', Language)

    def test_post_by_authenticated_user(self):
        self.post_category_by_authenticated_user({'name': 'Chinese'}, 'language-list', Language)

        # self.create_user_and_set_token_credentials()
        # data = {'name': name}
        # url = reverse(f'{url}')
        # response = self.c.post(url, data, format='json')
        # return response

    def test_update_category_by_unanimous_user(self):
        self.post_category_by_authenticated_user( {'name': 'Japanese - would not be updated!'}, 'language-list', Language)
        self.update_category_by_unanimous_user({'name': 'Japanese UPDATED!'}, 'language-detail', Language)

    def test_update_category_by_authorized_user(self):
        response = self.post_category_by_authenticated_user( {'name': 'US to be updated'}, 'language-list', Language)
        data_update = {'name': 'USA UPDATED!'}
        response_updated = self.update_category_by_authenticated_user(data_update, 'language-detail', Language)
        for i in data_update:
            assert response.data[i] != response_updated.data[i]
            # print(f'{response.data[i]} != {response_updated.data[i]}')

    def test_post_category_which_already_exists(self):
        '''Users should not be able to create new genre which already exists'''

        self.post_category_by_authenticated_user( {'name': 'Bilingual'}, 'language-list', Language)
        self.post_duplicated_category({'name': 'Bilingual'}, 'language-list')

    def test_filter_category(self):
        self.post_category_by_authenticated_user( {'name': 'Music'}, 'language-list', Language)
        self.post_another_category({'name': 'Dancing'}, 'language-list', Language)
        self.filter_existing_category({'name': 'Dancing'}, 'language-list')
        self.filter_non_existing_category({'name': '???'}, 'language-list')

    def test_delete_category(self):
        self.post_and_get_category({'name': 'British English'}, 'language-list', Language)
        self.post_another_category({'name': 'Bengal'}, 'language-list', Language)
        self.delete_category(1, 'language-detail', Language)
        self.delete_non_existing_category(1, 'language-detail', Language)

class GenreCategoryAPITest(MainTestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = views.LanguageView.as_view({'get': 'list'})
        self.uri = '/genre/'

    def test_get_category(self):
        request = self.factory.get(self.uri)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                'Expected Response Code 200, received {0} instead.'.format(response.status_code))

    def test_post_by_unauthorized_user(self):
        pass

    def test_post_by_authenticated_user(self):
        pass

    def test_update_category_by_unanimous_user(self):
        pass

    def test_update_category_by_authorized_user(self):
        pass

    def test_post_category_which_already_exists(self):
        pass

    def test_filter_category(self):
        pass

    def test_delete_category(self):
        pass

class GenreCategoryTest(MainTestCase):

    # def post_genre_category(self, name):
    #     data = {'name': name}
    #     url = reverse('genre-list')
    #     response = self.client.post(url, data, format='json')
    #     return response

    def test_simple_start_test(self):
        self.assertEqual(1, 1)

    def test_post_and_get_category(self):
        '''Check if an authenticated user can create a new genre'''

        self.post_and_get_category({'name': 'Literatures'}, 'genre-list', Genre)

        # OLD CODE HERE:
        # self.create_user_and_set_token_credentials()
        # name = 'Literature'
        # response = self.c.post(reverse('genre-list'), {'name': name}, format='json')
        # print(f'Authorized responce to create genre: {response.status_code}')
        # assert response.status_code == status.HTTP_201_CREATED
        # assert Genre.objects.count() == 1
        # print(Genre.objects.get().name)
        #
        # response_get = self.c.get(reverse('genre-list'), {'name': name}, format='json')
        # print(f'Check if the get method is ok: {response_get.status_code}')
        # assert response_get.status_code == status.HTTP_200_OK

    def test_post_by_unauthorized_user(self):
        self.post_category_by_unanimous_user({'name': 'History'}, 'genre-list', Genre)
        # another_genre_name = 'History'
        # url = 'genre-list'
        # response3 = self.post_category(another_genre_name, url)
        # print(f'Unauthorized attempt to create genre status: {response3.status_code}')
        # assert response3.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_by_authenticated_user(self):
        self.post_category_by_authenticated_user( {'name': 'Crime'}, 'genre-list', Genre)

    def test_update_category_by_unanimous_user(self):
        '''Check if unanimous user can update genre'''
        # self.update_category('WWW3', 'WW3 UPDATED!', 'genre-list', 'genre-detail', Genre )

        self.post_category_by_authenticated_user( {'name': 'WWW3'}, 'genre-list', Genre)
        self.update_category_by_unanimous_user({'name': 'WW3 UPDATED!'}, 'genre-detail', Genre)
        # self.create_user_and_set_token_credentials()
        # genre_name = 'WW3'
        # data = {'name': genre_name}
        # response_create = self.c.post(reverse('genre-list'), data, format='json')
        # print(f'Response update create status test: {response_create.status_code}')
        # print(f"Genre name: {Genre.objects.get().name}")
        # assert response_create.status_code == status.HTTP_201_CREATED
        #
        # url = reverse('genre-detail', None, {Genre.objects.get().pk})
        # print(url)
        #
        # genre_name_updated = 'NO WW'
        # data = {'name': genre_name_updated}
        #
        # response_update_by_unanimous_user = self.client.patch(reverse('genre-detail', None,
        #                                 {Genre.objects.get().pk}), data, content_type='application/json')
        # print(f'Responce updated Genre by Unanimous User: {response_update_by_unanimous_user.status_code}')
        #
        # assert response_update_by_unanimous_user.status_code == status.HTTP_401_UNAUTHORIZED
        # assert Genre.objects.get().id == 1

    def test_update_category_by_authorized_user(self):
        '''Ensure we can update a single field for a genre category'''

        response = self.post_category_by_authenticated_user( {'name': 'To be updated'}, 'genre-list', Genre)
        data_update = {'name': 'UPDATED Properly!'}
        response_updated = self.update_category_by_authenticated_user(data_update, 'genre-detail', Genre)

        for i in data_update:
            assert response.data[i] != response_updated.data[i]
            # print(f'{response.data[i]} != {response_updated.data[i]}')

        # self.create_user_and_set_token_credentials()
        # genre_name = 'WW3'
        # data = {'name': genre_name}
        # response_create = self.c.post(reverse('genre-list'), data, format='json')
        # print(f'Response update create status test: {response_create.status_code}')
        # print(f"Genre name: {Genre.objects.get().name}")
        # assert response_create.status_code == status.HTTP_201_CREATED
        #
        # url = reverse('genre-detail', None, {Genre.objects.get().pk})
        # print(url)

        # genre_name_updated = 'NO WW'
        # data = {'name': genre_name_updated}
        #
        # response_update = self.c.patch(reverse('genre-detail', None, {Genre.objects.get().pk}), data,
        #                                content_type='application/json')
        # print(f'Responce updated Genre: {response_update.status_code}')
        # print(f'Responce updated Genre Name: {response_update.data["name"]}')
        #
        # assert response_update.status_code == status.HTTP_200_OK
        # assert Genre.objects.get().id == 1
        #
        # # Test if the GET response is properly handled - 200 OK
        # url_get_genre = reverse('genre-detail', None, {Genre.objects.get().pk})
        # get_responce = self.client.get(url_get_genre, format='json')
        # assert get_responce.status_code == status.HTTP_200_OK

    def test_post_category_which_already_exists(self):
        '''Users should not be able to create new genre which already exists'''

        self.post_category_by_authenticated_user( {'name': 'To be updated'}, 'genre-list', Genre)
        self.post_duplicated_category({'name': 'To be updated'}, 'genre-list')
        # response = self.c.post(reverse('genre-list'), {'name': 'To be updated'}, format='json')
        # print(response.status_code)
        # assert response.status_code == status.HTTP_400_BAD_REQUEST


        # self.post_category_by_authenticated_user('New Category', 'genre-list', Genre)

        # self.create_user_and_set_token_credentials()
        # genre_name = 'Genre Update Existing'
        # data = {'name': genre_name}
        # response_create = self.c.post(reverse('genre-list'), data, format='json')
        # print(f'Response create existing status test: {response_create.status_code}')
        # print(f"Genre name: {Genre.objects.get().name}")
        # assert response_create.status_code == status.HTTP_201_CREATED
        #
        # new_genre_name = 'Genre Update Existing'
        # data_new = {'name': new_genre_name}
        # response_create_new = self.c.post(reverse('genre-list'), data_new, format='json')
        # print(f"Check the status of the new genre we try to create which already exists: "
        #       f"{response_create_new.status_code}")
        # assert response_create_new.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_category_name(self):
        '''Ensure we can filter a genre category by name'''

        self.post_category_by_authenticated_user({'name': 'Music'}, 'genre-list', Genre)
        print(f'Assert the name is equal to Music {Genre.objects.get().name}')
        assert Genre.objects.get().name == 'Music'
        self.post_another_category({'name': 'Dancing'}, 'genre-list', Genre)
        assert Genre.objects.get(name='Music').name == 'Music'
        self.filter_existing_category({'name': 'Dancing'}, 'genre-list')
        self.filter_non_existing_category({'name': '???'}, 'genre-list')

        # self.create_user_and_set_token_credentials()
        # genre_name = 'History'
        # new_genre_name = 'Science'
        #
        # data = {'name': genre_name}
        # new_data = {'name': new_genre_name}
        #
        # response_create = self.c.post(reverse('genre-list'), data, format='json')
        # print(f'First Genre status {response_create.status_code}')
        # response_create_new = self.c.post(reverse('genre-list'), new_data, format='json')
        # print(f'Second Genre status {response_create_new.status_code}')
        #
        # assert response_create.status_code == status.HTTP_201_CREATED
        # assert response_create_new.status_code == status.HTTP_201_CREATED

        # print(Genre.objects.count())
        assert Genre.objects.count() == 2
        # print(Genre.objects.first().name)
        # print(Genre.objects.last().name)


        # genre_filter_name = {'name': new_genre_name}
        # url = f'{reverse("genre-list")}?{urlencode(genre_filter_name)}'
        # print(f'The new filter URL which we will check: {url}')
        #
        # response_filter = self.client.get(url, format='json')
        # print(f'Filer response status code {response_filter.status_code}')
        #
        # assert response_filter.status_code == status.HTTP_200_OK
        # print(response_filter.data)
        # print(response_filter.data[0]['name'])
        # print(response_filter.data[0]['pk'])
        # assert response_filter.data[0]['name'] == new_genre_name
        # try:
        #     assert response_filter.data[1].exists() == True
        #     assert False
        # except IndexError:
        #     assert True

    def test_delete_category(self):
        self.post_and_get_category({'name': 'Eastern Literature'}, 'genre-list', Genre)
        self.post_another_category({'name': 'Western Literature'}, 'genre-list', Genre)
        self.delete_category(1, 'genre-detail', Genre)
        self.delete_non_existing_category(1, 'genre-detail', Genre)

        # print(Genre.objects.count())
        # name_to_remove = 'Western Literature'
        # count_objects = Genre.objects.count()
        # url = reverse('genre-detail', kwargs={'pk': Genre.objects.get(name=name_to_remove).pk})
        # response_delete = self.c.delete(url)
        # print(f'Response delete status code {response_delete.status_code}')
        # print(Genre.objects.count())
        #
        # assert response_delete.status_code == status.HTTP_204_NO_CONTENT
        # assert Genre.objects.count() == count_objects - 1

class AuthorCategoryTest(MainTestCase):
    # pass
    def test_post_author_authenticated_user(self):
        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}
        response = self.post_category_by_authenticated_user(data, 'author-list', Author)

        for key in data:
            if key != None and response.data[key] != None:
                response_get = self.client.get(reverse('author-list'), {f'{key}': response.data[key]}, format='json')

                assert response_get.status_code == status.HTTP_200_OK
                assert data[key] == response_get.data[0][key]
                assert Author.objects.get().id == 1

    def test_post_author_incorrect_dates(self):
        data = {'first_name': 'Johny', 'last_name': 'Doed', 'date_of_birth': '20-12-21', 'date_of_death': '2012-12-12',
                'about_the_author': 'XXX Info'}
        responce = self.post_category_by_authenticated_user_incorrect_date_format(data, 'author-list', Author)

        for kye in responce.data.keys():
            # print(responce.data[kye])
            # print(responce.data[kye][0])
            # print(type(responce.data[kye]))
            # print('Date has wrong format' in responce.data[kye][0])
            assert 'Date has wrong format' in responce.data[kye][0]

    def test_post_and_get_category(self):
        data = {'first_name': 'Johns', 'about_the_author': 'XXX Info',
                'last_name': 'Doem', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        self.post_and_get_category(data, 'author-list', Author)

    def test_post_by_unanimous_user(self):
        data = {'first_name': 'Johnson', 'about_the_author': 'XXX Info',
                'last_name': 'Dodson', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        self.post_category_by_unanimous_user(data, 'author-list', Author)

    def test_update_category_by_unanimous_user(self):
        data = {'first_name': 'Update', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_update = {'first_name': 'Updated Author', 'about_the_author': 'Updated Info',
                        'last_name': 'Doe Update', 'date_of_birth': '2014-12-12', 'date_of_death': '2017-11-12'}
        response = self.post_category_by_authenticated_user( data, 'author-list', Author)
        response_updated = self.update_category_by_unanimous_user(data_update, 'author-detail', Author)

    def test_update_category_by_authorized_user(self):
        data = {'first_name': 'Updated', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_update = {'first_name': 'Updateded Author', 'about_the_author': 'Updated Info',
                        'last_name': 'Doeded Update', 'date_of_birth': '2014-12-12', 'date_of_death': '2017-11-12'}
        response = self.post_category_by_authenticated_user( data, 'author-list', Author)
        response_updated = self.update_category_by_authenticated_user(data_update, 'author-detail', Author)

        for i in data_update:
            assert response.data[i] != response_updated.data[i]

    def test_post_category_which_already_exists(self):
        data = {'first_name': 'My', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_new = {'first_name': 'My', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}

        self.post_category_by_authenticated_user(data, 'author-list', Author)
        self.post_duplicated_category(data_new, 'author-list')

    def test_filter_category_name(self):
        data = {'first_name': 'Myde', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doede', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_new = {'first_name': 'Simon', 'about_the_author': 'A new name in the Author field',
                        'last_name': 'Cussack', 'date_of_birth': '1955-10-12', 'date_of_death': '2011-01-02'}

        self.post_category_by_authenticated_user(data, 'author-list', Author)
        self.post_another_category(data_new, 'author-list', Author)
        assert Author.objects.get(first_name='Simon').first_name == 'Simon'
        response_filter = self.filter_existing_category({'first_name': 'Simon'}, 'author-list')
        self.filter_non_existing_category({'first_name': '???'}, 'author-list')
        assert Author.objects.count() == 2

    def test_delete_category(self):
        data = {'first_name': 'Mymy', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doemy', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_new = {'first_name': 'Simoned', 'about_the_author': 'A new name in the Author field',
                        'last_name': 'Cussacked', 'date_of_birth': '1955-10-21', 'date_of_death': '2011-01-02'}

        self.post_category_by_authenticated_user(data, 'author-list', Author)
        self.post_another_category(data_new, 'author-list', Author)
        assert Author.objects.count() == 2
        self.delete_category(1, 'author-detail', Author)
        assert Author.objects.count() == 1
        self.delete_non_existing_category(1, 'author-detail', Author)
        assert Author.objects.count() == 1

    def test_post_birth_date_date_in_future(self):

        date_of_birth = datetime.date.today() + datetime.timedelta(days=1)
        data = {'first_name': 'My', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': date_of_birth}

        response = self.date_in_the_future(data, 'author-list', Author)

    def test_post_death_date_date_in_future(self):

        date_of_death = datetime.date.today() + datetime.timedelta(days=1)
        data = {'first_name': 'My', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_death': date_of_death}

        response = self.date_in_the_future(data, 'author-list', Author)

    def test_post_birth_date_after_death_date(self):

        date_of_death = datetime.date.today() - datetime.timedelta(weeks=155)
        date_of_birth = datetime.date.today()

        data = {'first_name': 'My', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': date_of_birth, 'date_of_death': date_of_death}

        response = self.second_date_comes_first_incorrect(data, 'author-list', Author)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Author.objects.count() == 0

class BookCategoryTest(MainTestCase):

    def test_post_book_authenticated_user(self):

        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        response = self.post_category_by_authenticated_user(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        response_book = self.post_another_category(book_data, 'book-list', Book)
        # print(response_book.data)
        # print(date_added)
        # print(published_date)

        for key in data_author:
            if key != None and response.data[key] != None:
                response_get = self.client.get(reverse('author-list'), {f'{key}': response.data[key]}, format='json')
                assert response_get.status_code == status.HTTP_200_OK
                assert data_author[key] == response_get.data[0][key]
                assert Author.objects.get().id == 1

        assert response_book.status_code == status.HTTP_201_CREATED
        assert Book.objects.get().pk == 1
    '''This should be modified later to return unique result???'''
    def test_post_and_get_category(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        response = self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John GET AND POST', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}


        response_book = self.post_another_category(book_data, 'book-list', Book)
        url = 'book-list'
        data = {'title': 'Book of John GET AND POST'}
        response_get = self.client.get(reverse(f'{url}'), data, format='json')
        assert response_get.status_code == status.HTTP_200_OK
        assert Book.objects.get().id == 1


    def test_post_by_unanimous_user(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        response = self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John GET AND POST', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}


        response_book = self.post_category_by_unanimous_user(book_data, 'book-list', Book)

    def test_update_category_by_unanimous_user(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        response = self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John GET AND POST', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}

        book_updated_data = {'title': 'Updated Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Update Doe text', 'copies': 5, 'loaned_copies': 0, 'available_copies': 5, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        response_book = self.post_another_category(book_data, 'book-list', Book)
        response_book_update = self.update_category_by_unanimous_user(book_updated_data, 'book-detail', Book)


    def test_update_category_by_authorized_user(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        response = self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John GET AND POST', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}

        book_updated_data = {'title': 'Updated Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Update Doe text', 'copies': 5, 'loaned_copies': 0, 'available_copies': 5, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        response_book = self.post_another_category(book_data, 'book-list', Book)
        response_book_update = self.update_category_by_authenticated_user(book_updated_data, 'book-detail', Book)

    def test_post_category_which_already_exists(self):
        '''Not needed as such restriction is not presented!'''
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        response = self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John GET AND POST', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}

        new_book_data = {'title': 'Book of John GET AND POST', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}

        response_book = self.post_another_category(book_data, 'book-list', Book)
        response_book_update = self.post_duplicated_category(new_book_data, 'book-list')

    def test_filter_category_name(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        response = self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John GET AND POST', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}

        new_book_data = {'title': 'Another Book of John GET Only', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}

        response_book = self.post_another_category(book_data, 'book-list', Book)
        response_book_new = self.post_another_category(new_book_data, 'book-list', Book)

        assert Book.objects.get(title='Book of John GET AND POST').title == 'Book of John GET AND POST'
        # data = {'title': 'Book of John GET AND POST'}
        # genre_filter_name = data
        # url_list = 'book-list'
        # print(urlencode(genre_filter_name))
        # url = f'{reverse(url_list)}?{urlencode(genre_filter_name)}'
        # self.filter_existing_category({'name': 'Dancing'}, 'language-list')
        response_filter = self.filter_existing_category({'title': 'Book of John GET AND POST'}, 'book-list')
        self.filter_non_existing_category({'title': '???'}, 'book-list')
        assert Book.objects.count() == 2

    def test_delete_category(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        response = self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John GET AND POST', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}

        new_book_data = {'title': 'Another Book of John GET Only', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'published': published_date, 'date_added': date_added,
            'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}), 'genre': genred}

        response_book = self.post_another_category(book_data, 'book-list', Book)
        response_book_new = self.post_another_category(new_book_data, 'book-list', Book)

        self.delete_category(1, 'book-detail', Book)

    def test_post_date_added_in_future(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        # published_date = datetime.date.today() - datetime.timedelta(weeks=3)
        date_added = datetime.date.today() + datetime.timedelta(weeks=3, days=1)
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        responsed_book = self.date_in_the_future(book_data, 'book-list', Book)

        assert responsed_book.status_code == status.HTTP_400_BAD_REQUEST
        assert Book.objects.count() == 0

    def test_post_published_date_in_future(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() + datetime.timedelta(weeks=3)
        # date_added = datetime.date.today() - datetime.timedelta(weeks=3, days=1)
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
             'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}
        responsed_book = self.date_in_the_future(book_data, 'book-list', Book)

        assert responsed_book.status_code == status.HTTP_400_BAD_REQUEST
        assert Book.objects.count() == 0

    def test_published_date_after_date_added(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = datetime.date.today() - datetime.timedelta(weeks=3)
        date_added = datetime.date.today() - datetime.timedelta(weeks=3, days=1)
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}



        responsed_book = self.second_date_comes_first_incorrect(book_data, 'book-list', Book)

        assert responsed_book.status_code == status.HTTP_400_BAD_REQUEST
        assert Book.objects.count() == 0

    def test_post_book_incorrect_dates(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        self.create_user_and_set_token_credentials(username='myuser', email='myemail@yahoo.com', password='pass1234')
        self.post_another_category(data_author, 'author-list', Author)
        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)

        published_date = '200-12-21'
        date_added = '011-11-14'
        genre_one = reverse('genre-detail', None, {Genre.objects.get(pk=1).pk })
        genre_two = reverse('genre-detail', None, {Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        responce = self.post_category_by_authenticated_user_incorrect_date_format(book_data, 'book-list', Book)

        assert responce.status_code == status.HTTP_400_BAD_REQUEST
        assert Book.objects.count() == 0

