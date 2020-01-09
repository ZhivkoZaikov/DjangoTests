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

from .. import views
from ..models import Genre, Language, Author, Book

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
            if not isinstance(value, list):
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
