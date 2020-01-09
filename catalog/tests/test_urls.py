import datetime

from django.http import HttpRequest
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from django.utils.http import urlencode
import json

from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError, ValidationError
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework.test import APITestCase, APIRequestFactory, APIClient
from rest_framework.authtoken.models import Token

from .. import views
from ..models import Genre, Language, Author, Book


class MainTestCase(APITestCase):

    def create_user_and_set_token_credentials(self, username='test', email="test@test.com", password="test"):

        self.user = User.objects.create_user(username=username, email=email, password=password)
        self.client = APIClient()
        self.client.login(username=username, password=password)

    def post_category_by_authenticated_user(self, data, url, model_name):

        count_objects = model_name.objects.count()
        self.create_user_and_set_token_credentials()
        response = self.client.post(reverse(url), data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert model_name.objects.count() == count_objects + 1

        for each_key in data:

            assert data[each_key] == response.data[each_key]
            if response.data[each_key] != None:
                response_get = self.client.get(reverse('author-list'), {f'{each_key}': response.data[each_key]}, format='json')
                assert response_get.status_code == status.HTTP_200_OK

        return response

    def post_another_category(self, data, url_list, model_name):

        count_objects = model_name.objects.count()
        response = self.client.post(reverse(url_list), data, format='json')

        for key in data.keys():

            self.assertIn(str(data[key]), str(response.data[key]))

        assert response.status_code == status.HTTP_201_CREATED
        assert model_name.objects.count() == count_objects + 1

        return response

    def additional_declarations(self):
        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', kwargs={'pk': Genre.objects.get(pk=1).pk})
        genre_two = reverse('genre-detail', kwargs={'pk': Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        return published_date, date_added, genred

    def list_get_request(self, model_name, model_view_name):

        url_name = f'{model_name._meta.model_name}-list'
        url = reverse(url_name)

        resolver = resolve(url)

        self.assertEqual(resolver.view_name, f'{model_name._meta.model_name}-list')
        self.assertEqual(resolver.func.cls, model_view_name)

        self.assertEqual(url, f'/{model_name._meta.model_name}/')

        response = self.client.get(url)
        # objects = model_name.objects.order_by('name')
        all_fields = [f.name for f in model_name._meta.fields if f.name != 'id']

        objects = model_name.objects.all()

        # assert that the length of the response is the same as the total number of objects
        # e.g. all object are GET
        self.assertEqual(len(response.data), len(model_name.objects.all()))

        for each in range(len(response.data)):
            for breach in all_fields:
                if breach != 'image':
                    self.assertEqual(str(response.data[each][breach]), str(getattr(objects[each], breach)))
        # TEST


        # assert that the GET content equals the existing Genres
        # for each in range(len(response.data)):
        #     self.assertIn(str(response.data[each]['name']), str(objects[each]))

        url_format = f'/{model_name._meta.model_name}/?format=api'
        response_format = self.client.get(url_format)

        objects_format = model_name.objects.all()

        self.assertEqual(len(response_format.data), len(model_name.objects.all()))

        # assert that the format GET response returns the same results as the regular URL GET request
        for each in range(len(response_format.data)):
            for breach in all_fields:
                if breach != 'image':
                    self.assertEqual(str(response_format.data[each][breach]), str(getattr(objects[each], breach)))

        url_json = f'/{model_name._meta.model_name}/?format=json'
        response_json = self.client.get(url_json)

        objects_json = model_name.objects.all()

        self.assertEqual(len(response_json.data), len(model_name.objects.all()))

        # assert that the format GET response returns the same results as the regular URL GET request
        for each in range(len(response_json.data)):
            for breach in all_fields:
                if breach != 'image':
                    self.assertEqual(str(response_json.data[each][breach]), str(getattr(objects[each], breach)))

        # OLD CODE
        #
        # url_name = f'{model_name._meta.model_name}-list'
        # url = reverse(url_name)
        #
        # resolver = resolve(url)
        #
        # self.assertEqual(resolver.view_name, f'{model_name._meta.model_name}-list')
        # self.assertEqual(resolver.func.cls, model_view_name)
        #
        # self.assertEqual(url, f'/{model_name._meta.model_name}/')
        #
        # response = self.client.get(url)
        # # objects = model_name.objects.order_by('name')
        #
        # objects = model_name.objects.all()
        #
        # # assert that the length of the response is the same as the total number of objects
        # # e.g. all object are GET
        # self.assertEqual(len(response.data), len(model_name.objects.all()))
        #
        # # assert that the GET content equals the existing Genres
        # for each in range(len(response.data)):
        #     self.assertIn(str(response.data[each]['name']), str(objects[each]))
        #
        # url_format = f'/{model_name._meta.model_name}/?format=api'
        # response_format = self.client.get(url_format)
        #
        # # objects_format = model_name.objects.order_by('name')
        # objects_format = model_name.objects.all()
        #
        # self.assertEqual(len(response_format.data), len(model_name.objects.all()))
        #
        # # assert that the format GET response returns the same results as the regular URL GET request
        # for each in range(len(response_format.data)):
        #     self.assertIn(str(response_format.data[each]['name']), str(objects_format[each]))
        #     self.assertIn(str(response.data[each]['url']), str(response_format.data[each]['url']))
        #
        # url_json = f'/{model_name._meta.model_name}/?format=json'
        # response_json = self.client.get(url_json)
        #
        # # objects_json = model_name.objects.order_by('name')
        # objects_json = model_name.objects.all()
        #
        # self.assertEqual(len(response_json.data), len(model_name.objects.all()))
        #
        # # assert that the format GET response returns the same results as the regular URL GET request
        # for each in range(len(response_json.data)):
        #     self.assertIn(str(response_json.data[each]['name']), str(objects_json[each]))
        #     self.assertIn(str(response.data[each]['url']), str(response_json.data[each]['url']))

    def detail_get_request(self, model_name, model_view_name):

        objects = model_name.objects.all()
        all_fields = [f.name for f in model_name._meta.fields if f.name != 'id']

        for each in model_name.objects.all():

            url_format = f'/{model_name._meta.model_name}/{each.pk}/?format=api'
            response_format = self.client.get(url_format)
            self.assertEqual(response_format.status_code, status.HTTP_200_OK)

            for breach in all_fields :
                if breach != 'image':
                    self.assertIn(str(response_format.data[breach]), str(getattr(each, breach)))

        for each in model_name.objects.all():

            url_format = f'/{model_name._meta.model_name}/{each.pk}/?format=json'
            response_format = self.client.get(url_format)
            self.assertEqual(response_format.status_code, status.HTTP_200_OK)
            for breach in all_fields :
                if breach != 'image':
                    self.assertIn(str(response_format.data[breach]), str(getattr(each, breach)))

        for each in model_name.objects.all():

            url_name = f'{model_name._meta.model_name}-detail'
            url = reverse(url_name, args=[each.pk])
            self.assertEqual(url, f'/{model_name._meta.model_name}/{each.pk}/')

            resolver = resolve(url)
            self.assertEqual(resolver.view_name, url_name)
            self.assertEqual(resolver.func.cls, model_view_name)

            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            for breach in all_fields :
                self.assertContains(response, breach)
                if breach != 'image':
                    self.assertIn(str(response.data[breach]), str(getattr(each, breach)))

        #   THIS IS THE OLD CODE
        #
        # objects = model_name.objects.all()
        #
        # for each in model_name.objects.all():
        #
        #
        #     url_format = f'/{model_name._meta.model_name}/{each.pk}/?format=api'
        #     response_format = self.client.get(url_format)
        #     self.assertEqual(response_format.status_code, status.HTTP_200_OK)
        #     self.assertIn(str(response_format.data['name']), str(objects))
        #
        # for each in model_name.objects.all():
        #
        #     url_format = f'/{model_name._meta.model_name}/{each.pk}/?format=json'
        #     response_format = self.client.get(url_format)
        #     self.assertEqual(response_format.status_code, status.HTTP_200_OK)
        #     self.assertIn(str(response_format.data['name']), str(objects))
        #
        # for each in model_name.objects.all():
        #
        #     url_name = f'{model_name._meta.model_name}-detail'
        #     url = reverse(url_name, args=[each.pk])
        #     self.assertEqual(url, f'/{model_name._meta.model_name}/{each.pk}/')
        #
        #     resolver = resolve(url)
        #     self.assertEqual(resolver.view_name, url_name)
        #     self.assertEqual(resolver.func.cls, model_view_name)
        #
        #     response = self.client.get(url)
        #     self.assertEqual(response.status_code, status.HTTP_200_OK)
        #     self.assertIn(str(response.data['name']), str(objects))
        #     self.assertContains(response, 'name')
        #     self.assertContains(response, model_name.objects.get(pk=each.pk).name)
        #     self.assertContains(response, model_name.objects.get(pk=each.pk).view_count)


class GenreURLsTests(MainTestCase):

    def setUp(self):



            data_author = {'first_name': 'Myde', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doede', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12', 'view_count': 0}

            data_author_second = {'first_name': 'Michael', 'about_the_author': 'Michael Corrs Exclusive',
                            'last_name': 'Corrs', 'date_of_birth': '1955-12-21', 'date_of_death': '2001-11-14', 'view_count': 3}

            data_author_third = {'first_name': 'Steven', 'about_the_author': 'XXX Info',
                            'last_name': 'Gold', 'date_of_birth': '1943-12-21', 'date_of_death': '2000-11-14', 'view_count': 5}

            self.create_user_and_set_token_credentials()

            self.post_another_category(data_author, 'author-list', Author)
            self.post_another_category(data_author_second, 'author-list', Author)
            self.post_another_category(data_author_third, 'author-list', Author)

            self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
            self.post_another_category({'name': 'English'}, 'language-list', Language)
            self.post_another_category({'name': 'Japanese'}, 'language-list', Language)

            self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
            self.post_another_category({'name': 'History'}, 'genre-list', Genre)
            self.post_another_category({'name': 'Elven Literature'}, 'genre-list', Genre)
            self.post_another_category({'name': 'Medieval Literature'}, 'genre-list', Genre)

            published_date, date_added, genred = self.additional_declarations()

            book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

            self.post_another_category(book_data, 'book-list', Book)


    # genre-list
    # genre-detail
    # genre-detail format api, format json
    # genre-list format api, format json

    def test_genre_detail(self):

        self.detail_get_request(Genre, views.GenreView)

            # print(resolver.app_name)
            # print(resolver.app_names)
            # print(resolver.args)
            # print(resolver.func)
            # print(resolver.kwargs)
            # print(resolver.namespace)
            # print(resolver.namespaces)
            # print(resolver.url_name)
            # print(resolver.view_name)

    def test_genre_list(self):

        self.list_get_request(Genre, views.GenreView)

    def test_language_detail(self):

        self.detail_get_request(Language, views.LanguageView)

    def test_language_list(self):
        self.list_get_request(Language, views.LanguageView)

    def test_author_detail(self):

        self.detail_get_request(Author, views.AuthorView)

        # model_name = Author
        # model_view_name = views.AuthorView
        #
        # objects = model_name.objects.all()
        # all_fields = [f.name for f in model_name._meta.fields if f.name != 'id']
        #
        # for each in model_name.objects.all():
        #
        #     url_format = f'/{model_name._meta.model_name}/{each.pk}/?format=api'
        #     response_format = self.client.get(url_format)
        #     self.assertEqual(response_format.status_code, status.HTTP_200_OK)
        #
        #     for breach in all_fields :
        #         if breach != 'image':
        #             self.assertIn(str(response_format.data[breach]), str(getattr(each, breach)))
        #
        # for each in model_name.objects.all():
        #
        #     url_format = f'/{model_name._meta.model_name}/{each.pk}/?format=json'
        #     response_format = self.client.get(url_format)
        #     self.assertEqual(response_format.status_code, status.HTTP_200_OK)
        #     for breach in all_fields :
        #         if breach != 'image':
        #             self.assertIn(str(response_format.data[breach]), str(getattr(each, breach)))
        #
        # for each in model_name.objects.all():
        #
        #     url_name = f'{model_name._meta.model_name}-detail'
        #     url = reverse(url_name, args=[each.pk])
        #     self.assertEqual(url, f'/{model_name._meta.model_name}/{each.pk}/')
        #
        #     resolver = resolve(url)
        #     self.assertEqual(resolver.view_name, url_name)
        #     self.assertEqual(resolver.func.cls, model_view_name)
        #
        #     response = self.client.get(url)
        #     print(response)
        #     self.assertEqual(response.status_code, status.HTTP_200_OK)
        #     for breach in all_fields :
        #         self.assertContains(response, breach)
        #         if breach != 'image':
        #             self.assertIn(str(response.data[breach]), str(getattr(each, breach)))

    def test_author_list(self):

        self.list_get_request(Author, views.AuthorView)

        # model_name = Author
        # model_view_name = views.AuthorView
        #
        # url_name = f'{model_name._meta.model_name}-list'
        # url = reverse(url_name)
        #
        # resolver = resolve(url)
        #
        # self.assertEqual(resolver.view_name, f'{model_name._meta.model_name}-list')
        # self.assertEqual(resolver.func.cls, model_view_name)
        #
        # self.assertEqual(url, f'/{model_name._meta.model_name}/')
        #
        # response = self.client.get(url)
        # # objects = model_name.objects.order_by('name')
        # all_fields = [f.name for f in model_name._meta.fields if f.name != 'id']
        #
        # objects = model_name.objects.all()
        #
        # # assert that the length of the response is the same as the total number of objects
        # # e.g. all object are GET
        # self.assertEqual(len(response.data), len(model_name.objects.all()))
        #
        # for each in range(len(response.data)):
        #     for breach in all_fields:
        #         if breach != 'image':
        #             self.assertEqual(str(response.data[each][breach]), str(getattr(objects[each], breach)))
        # # TEST
        #
        #
        # # assert that the GET content equals the existing Genres
        # # for each in range(len(response.data)):
        # #     self.assertIn(str(response.data[each]['name']), str(objects[each]))
        #
        # url_format = f'/{model_name._meta.model_name}/?format=api'
        # response_format = self.client.get(url_format)
        #
        # objects_format = model_name.objects.all()
        #
        # self.assertEqual(len(response_format.data), len(model_name.objects.all()))
        #
        # # assert that the format GET response returns the same results as the regular URL GET request
        # for each in range(len(response_format.data)):
        #     for breach in all_fields:
        #         if breach != 'image':
        #             self.assertEqual(str(response_format.data[each][breach]), str(getattr(objects[each], breach)))
        #
        # url_json = f'/{model_name._meta.model_name}/?format=json'
        # response_json = self.client.get(url_json)
        #
        # objects_json = model_name.objects.all()
        #
        # self.assertEqual(len(response_json.data), len(model_name.objects.all()))
        #
        # # assert that the format GET response returns the same results as the regular URL GET request
        # for each in range(len(response_json.data)):
        #     for breach in all_fields:
        #         if breach != 'image':
        #             self.assertEqual(str(response_json.data[each][breach]), str(getattr(objects[each], breach)))
