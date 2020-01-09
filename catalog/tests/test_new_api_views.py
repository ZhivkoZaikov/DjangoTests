import datetime

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.utils import IntegrityError
from django.db import transaction

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

        # for each_key in data:
        #     assert data[each_key] == response.data[each_key]

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

    def post_duplicated_category(self, data, url_list, model_name):

        count_objects = model_name.objects.count()
        url = reverse(f'{url_list}')
        response = self.client.post(url, data, format='json')

        assert model_name.objects.count() == count_objects
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        return response

    def post_category_by_unanimous_user(self, data, url, model_name):

        count_objects = model_name.objects.count()
        url = reverse(f'{url}')
        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert model_name.objects.count() == count_objects
        self.assertIn('Authentication credentials were not provided.', response.data.values())

        return response

    def update_category_by_unanimous_user(self, data, url_detail, model_name):

        model_obj = model_name.objects.get()
        response_update_by_unanimous_user = self.client.patch(reverse(url_detail,
                        kwargs={'pk': model_name.objects.get().pk}), data, format='json')
        assert response_update_by_unanimous_user.status_code == status.HTTP_401_UNAUTHORIZED
        assert model_name.objects.get().id == 1
        self.assertIn('Authentication credentials were not provided.', response_update_by_unanimous_user.data.values())

        for key in data.keys():
            self.assertNotEqual(data[key], getattr(model_obj, key))

        return response_update_by_unanimous_user

    def update_category_by_authenticated_user(self, data, url_detail, model_name):

        response_update = self.client.patch(reverse(url_detail,
                    kwargs={'pk': model_name.objects.get().pk}), data, format='json')

        assert response_update.status_code == status.HTTP_200_OK
        assert model_name.objects.get().id == 1

        url_get_genre = reverse(url_detail, None, {model_name.objects.get().pk})
        get_responce = self.client.get(url_get_genre, format='json')
        assert get_responce.status_code == status.HTTP_200_OK

        model_obj = model_name.objects.get()

        for key in data.keys():
            self.assertEqual(str(data[key]), str(getattr(model_obj, key)))
        return response_update

    def filter_existing_category(self, data, url_list):

        url = f'{reverse(url_list)}?{urlencode(data)}'
        response_filter = self.client.get(url, format='json')

        assert response_filter.status_code == status.HTTP_200_OK

        for key in data:
            assert data[key] == response_filter.data[0][key]

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

        # url = reverse(url_detail, kwargs={'pk': model_name.objects.get(pk=pk).pk})
        url = reverse(url_detail, kwargs={'pk': model_name.objects.get(pk=pk).pk})
        response_delete = self.client.delete(url)

        assert response_delete.status_code == status.HTTP_204_NO_CONTENT
        assert model_name.objects.count() == count_objects - 1

        try:
            url = reverse(url_detail, kwargs={'pk': model_name.objects.get(pk=pk).pk})
            assert False
        except model_name.DoesNotExist:
            assert True

    def delete_category_by_unauthorized_user(self, pk, url_detail, model_name):

        count_objects = model_name.objects.count()

        # url = reverse(url_detail, kwargs={'pk': model_name.objects.get(pk=pk).pk})
        url = reverse(url_detail, kwargs={'pk': model_name.objects.get(pk=pk).pk})
        response_delete = self.client.delete(url)

        assert response_delete.status_code == status.HTTP_401_UNAUTHORIZED
        assert model_name.objects.count() == count_objects
        self.assertIn('Authentication credentials were not provided.', response_delete.data.values())

    def delete_non_existing_category(self, pk, url_detail, model_name):

        count_objects = model_name.objects.count()
        try:
            url = reverse(url_detail, kwargs={'pk': model_name.objects.get(pk=pk).pk})
            response_delete = self.client.delete(url)
            assert False
        except model_name.DoesNotExist:
            assert True

        assert model_name.objects.count() == count_objects

    def post_category_by_authenticated_user_incorrect_date_format(self, data, url, model_name):

        self.create_user_and_set_token_credentials()
        response = self.client.post(reverse(f'{url}'), data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert model_name.objects.count() == 0
        for key in response.data.keys():
            assert 'Date has wrong format' in response.data[key][0]

        return response

    def date_in_the_future(self, data, url_lst, model_name):

        self.create_user_and_set_token_credentials()
        response = self.client.post(reverse(f'{url_lst}'), data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert model_name.objects.count() == 0

        for key in response.data.keys():
            assert 'Invalid date' in response.data[key][0]
        return response

    def second_date_comes_first_incorrect(self, data, url_list, model_name):
        '''Check for incorrect date assignment logic, e.g. date of death is before date of birth'''
        self.create_user_and_set_token_credentials()
        response = self.client.post(reverse(f'{url_list}'), data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert model_name.objects.count() == 0

        for key in response.data.keys():
            assert 'Incorrect date logic assignment! Check how the dates are set and reconfigure them accordingly!' in response.data[key][0]

        return response

class LanguageApiViewTest(MainTestCase):

    def test_list_language(self):
        self.create_user_and_set_token_credentials()
        response = self.client.get(reverse('language-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_by_authenticated_user(self):

        self.post_category_by_authenticated_user({'name': 'Spanish', 'view_count': 5}, 'language-list', Language)

    def test_post_by_unauthorized_user(self):

        response = self.post_category_by_unanimous_user({'name': 'Spanish', 'view_count': 5}, 'language-list', Language)

    def test_update_category_by_unanimous_user(self):

        self.post_category_by_authenticated_user({'name': 'Japanese!', 'view_count': 7}, 'language-list', Language)
        self.client.logout()
        self.update_category_by_unanimous_user({'name': 'Japanese UPDATED!', 'view_count': 11}, 'language-detail', Language)

    def test_update_category_by_authorized_user(self):
        self.post_category_by_authenticated_user({'name': 'Japanese!', 'view_count': 7}, 'language-list', Language)

        self.update_category_by_authenticated_user({'name': 'Japanese updated!', 'view_count': 17},
                                                   'language-detail', Language)

    def test_post_category_which_already_exists(self):
        self.post_category_by_authenticated_user({'name': 'Japanese!', 'view_count': 7}, 'language-list', Language)
        self.post_another_category({'name': 'Chinese 2!', 'view_count': 17}, 'language-list', Language)
        duplicated_language = self.post_duplicated_category({'name': 'Japanese!', 'view_count': 7}, 'language-list', Language)

        self.assertIn('Language with this name already exists.', list(duplicated_language.data.values())[0])

    def test_filter_category(self):
        self.post_category_by_authenticated_user({'name': 'Japanese!', 'view_count': 7}, 'language-list', Language)
        self.post_another_category({'name': 'Chinese 2!', 'view_count': 17}, 'language-list', Language)
        self.filter_existing_category({'name': 'Japanese!'}, 'language-list')
        self.filter_non_existing_category({'name': 'Japanesedd!'}, 'language-list')

    def test_delete_category(self):
        self.post_category_by_authenticated_user({'name': 'British English', 'view_count': 11}, 'language-list', Language)
        self.post_another_category({'name': 'Bengal', 'view_count': 11}, 'language-list', Language)
        self.delete_category(1, 'language-detail', Language)
        self.delete_non_existing_category(1, 'language-detail', Language)

    def test_delete_category_unauthorized_user(self):
        self.post_category_by_authenticated_user({'name': 'British English', 'view_count': 11}, 'language-list', Language)
        self.post_another_category({'name': 'Bengal', 'view_count': 11}, 'language-list', Language)
        self.client.logout()
        self.delete_category_by_unauthorized_user(1, 'language-detail', Language)

    def test_post_and_get_category(self):

        query_1 = self.post_category_by_authenticated_user({'name': 'British English', 'view_count': 11}, 'language-list', Language)
        query_2 = self.post_another_category({'name': 'Bengal', 'view_count': 11}, 'language-list', Language)
        query_3 = self.post_another_category({'name': 'English', 'view_count': 11}, 'language-list', Language)

        query_data = (query_1.data['name'], query_2.data['name'], query_3.data['name'])

        for each in Language.objects.all():
            self.assertIn(each.name, query_data)
            self.assertEqual(each.view_count, 11)

        self.assertEqual(Language.objects.count(), 3)


class GenreAPIViewTest(MainTestCase):

    def test_list_genre(self):
        self.create_user_and_set_token_credentials()
        response = self.client.get(reverse('genre-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_by_authenticated_user(self):
        self.post_category_by_authenticated_user({'name': 'Etno', 'view_count': 5}, 'genre-list', Genre)

    def test_post_by_unauthorized_user(self):
        response = self.post_category_by_unanimous_user({'name': 'Etno', 'view_count': 5}, 'genre-list', Genre)

    def test_update_category_by_unanimous_user(self):
        self.post_category_by_authenticated_user({'name': 'Etno!', 'view_count': 7}, 'genre-list', Genre)
        self.client.logout()
        self.update_category_by_unanimous_user({'name': 'Etno UPDATED!', 'view_count': 11}, 'genre-detail', Genre)

    def test_update_category_by_authorized_user(self):
        self.post_category_by_authenticated_user({'name': 'ETNO!', 'view_count': 7}, 'genre-list', Genre)
        self.update_category_by_authenticated_user({'name': 'ETNO updated!', 'view_count': 17},
                                                   'genre-detail', Genre)

    def test_post_category_which_already_exists(self):
        self.post_category_by_authenticated_user({'name': 'ETNO!', 'view_count': 7}, 'genre-list', Genre)
        self.post_another_category({'name': 'Ancient!', 'view_count': 17}, 'genre-list', Genre)
        duplicated_genre = self.post_duplicated_category({'name': 'ETNO!', 'view_count': 7}, 'genre-list', Genre)

        self.assertIn('genre with this name already exists.', list(duplicated_genre.data.values())[0])

    def test_filter_category_name(self):
        self.post_category_by_authenticated_user({'name': 'ETNO!', 'view_count': 7}, 'genre-list', Genre)
        self.post_another_category({'name': 'Ancient Literature', 'view_count': 17}, 'genre-list', Genre)
        self.filter_existing_category({'name': 'ETNO!'}, 'genre-list')
        self.filter_non_existing_category({'name': 'ETNOETNO!'}, 'genre-list')

    def test_delete_category(self):
        self.post_category_by_authenticated_user({'name': 'British Litearature', 'view_count': 11}, 'genre-list', Genre)
        self.post_another_category({'name': 'Russian Literature', 'view_count': 11}, 'genre-list', Genre)
        self.delete_category(1, 'genre-detail', Genre)
        self.delete_non_existing_category(1, 'genre-detail', Genre)

    def test_delete_category_unauthorized_user(self):
        self.post_category_by_authenticated_user({'name': 'British Literature', 'view_count': 11}, 'genre-list', Genre)
        self.post_another_category({'name': 'Russian Literature', 'view_count': 11}, 'genre-list', Genre)
        self.client.logout()
        self.delete_category_by_unauthorized_user(1, 'genre-detail', Genre)

    def test_post_and_get_category(self):
        query_1 = self.post_category_by_authenticated_user({'name': 'British Literature', 'view_count': 11},
                                                           'genre-list', Genre)
        query_2 = self.post_another_category({'name': 'Bengal', 'view_count': 11}, 'genre-list', Genre)
        query_3 = self.post_another_category({'name': 'English', 'view_count': 11}, 'genre-list', Genre)

        query_data = (query_1.data['name'], query_2.data['name'], query_3.data['name'])

        for each in Genre.objects.all():
            self.assertIn(each.name, query_data)
            self.assertEqual(each.view_count, 11)

        self.assertEqual(Genre.objects.count(), 3)


class AuthorAPIViewTest(MainTestCase):

    def test_list_author(self):
        self.create_user_and_set_token_credentials()
        response = self.client.get(reverse('author-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_by_authenticated_user(self):
        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        response = self.post_category_by_authenticated_user(data, 'author-list', Author)

        self.assertEqual(response.data['url'], f'http://testserver/author/{Author.objects.count()}/')

    def test_post_by_unauthorized_user(self):
        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}
        result = self.post_category_by_unanimous_user(data, 'author-list', Author)

    def test_update_category_by_unanimous_user(self):

        data = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}
        data_update = {'first_name': 'Updated Author', 'about_the_author': 'Updated Info',
                        'last_name': 'Doe Update', 'date_of_birth': '2014-12-12', 'date_of_death': '2017-11-12'}

        response = self.post_category_by_authenticated_user(data, 'author-list', Author)
        self.client.logout()

        model_obj = Author.objects.first()
        for key in data.keys():
            self.assertEqual(str(data[key]), str(getattr(model_obj, key)))

        response_update = self.update_category_by_unanimous_user(data_update, 'author-detail', Author)

    def test_update_category_by_authorized_user(self):

        data = {'first_name': 'Updated', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_update = {'first_name': 'Updateded Author', 'about_the_author': 'Updated Info',
                        'last_name': 'Doeded Update', 'date_of_birth': '2014-12-12', 'date_of_death': '2017-11-12'}

        response = self.post_category_by_authenticated_user( data, 'author-list', Author)
        response_updated = self.update_category_by_authenticated_user(data_update, 'author-detail', Author)

    def test_post_category_which_already_exists(self):
        # author category should be compared for unique together first name and last name
        data = {'first_name': 'Updated', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_second_author = {'first_name': 'Updated', 'about_the_author': 'Updated Info',
                        'last_name': 'Doe', 'date_of_birth': '2014-12-12', 'date_of_death': '2017-11-12'}

        response = self.post_category_by_authenticated_user( data, 'author-list', Author)
        response_second = self.post_duplicated_category(data_second_author, 'author-list', Author)

        # there should be a better way to do this?
        self.assertIn('The fields first_name, last_name must make a unique set.', list(response_second.data.values())[0])

    def test_filter_category_name(self):
        data = {'first_name': 'Myde', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doede', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_new = {'first_name': 'Simon', 'about_the_author': 'A new name in the Author field',
                        'last_name': 'Cussack', 'date_of_birth': '1955-10-12', 'date_of_death': '2011-01-02'}

        self.post_category_by_authenticated_user(data, 'author-list', Author)
        self.post_another_category(data_new, 'author-list', Author)
        response_filter = self.filter_existing_category({'first_name': 'Simon'}, 'author-list')
        self.filter_non_existing_category({'first_name': '???'}, 'author-list')

    def test_delete_category(self):

        data = {'first_name': 'Myde', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doede', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_new = {'first_name': 'Simon', 'about_the_author': 'A new name in the Author field',
                        'last_name': 'Cussack', 'date_of_birth': '1955-10-12', 'date_of_death': '2011-01-02'}

        self.post_category_by_authenticated_user(data, 'author-list', Author)
        self.post_another_category(data_new, 'author-list', Author)

        self.delete_category(1, 'author-detail', Author)

        self.delete_non_existing_category(1, 'author-detail', Author)

    def test_delete_category_unauthorized_user(self):

        data = {'first_name': 'Myde', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doede', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        data_new = {'first_name': 'Simon', 'about_the_author': 'A new name in the Author field',
                        'last_name': 'Cussack', 'date_of_birth': '1955-10-12', 'date_of_death': '2011-01-02'}

        self.post_category_by_authenticated_user(data, 'author-list', Author)
        self.post_another_category(data_new, 'author-list', Author)
        self.client.logout()
        self.delete_category_by_unauthorized_user(1, 'author-detail', Author)

    def test_post_and_get_category(self):

        query_1 = {'first_name': 'Myde', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doede', 'date_of_birth': '2000-12-12', 'date_of_death': '2012-11-12'}
        query_2 = {'first_name': 'Simon', 'about_the_author': 'A new name in the Author field',
                        'last_name': 'Cussack', 'date_of_birth': '1955-10-12', 'date_of_death': '2011-01-02'}
        query_3 = {'first_name': 'Cole', 'about_the_author': 'My Authy',
                        'last_name': 'Joel', 'date_of_birth': '1975-10-12', 'date_of_death': '2015-01-02'}
        self.post_category_by_authenticated_user(query_1, 'author-list', Author)
        self.post_another_category(query_2, 'author-list', Author)
        self.post_another_category(query_3, 'author-list', Author)

        query_data = {}
        for key in query_1.keys():
            query_data[f'{key}'] = (query_1[f'{key}'], query_2[f'{key}'], query_3[f'{key}'])

        for each in Author.objects.all():
            for key in query_1.keys():
                self.assertIn(str(getattr(each, key)), str(query_data[f'{key}']))

        self.assertEqual(Author.objects.count(), 3)

    def test_post_author_incorrect_date_of_birth(self):
        data = {'first_name': 'Johny', 'last_name': 'Doed', 'date_of_birth': '20-12-21', 'date_of_death': '2012-12-12',
                'about_the_author': 'XXX Info'}
        responce = self.post_category_by_authenticated_user_incorrect_date_format(data, 'author-list', Author)

    def test_post_author_incorrect_date_death(self):
        data = {'first_name': 'Johny', 'last_name': 'Doed', 'date_of_birth': '2011-12-21', 'date_of_death': '20xx-12-12',
                'about_the_author': 'XXX Info'}
        responce = self.post_category_by_authenticated_user_incorrect_date_format(data, 'author-list', Author)

    def test_post_birth_date_date_in_future(self):
        date_of_birth = datetime.date.today() + datetime.timedelta(days=1)
        data = {'first_name': 'My', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': date_of_birth}

        response = self.date_in_the_future(data, 'author-list', Author)

    def test_post_death_date_date_in_future(self):
        date_of_birth = datetime.date.today() - datetime.timedelta(weeks=10)
        date_of_death = datetime.date.today() + datetime.timedelta(days=1)
        data = {'first_name': 'My', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': date_of_birth, 'date_of_death': date_of_death}

        response = self.date_in_the_future(data, 'author-list', Author)

    def test_post_birth_date_after_death_date(self):
        date_of_birth = datetime.date.today() - datetime.timedelta(weeks=10)
        date_of_death = datetime.date.today() - datetime.timedelta(weeks=10, days=1)
        data = {'first_name': 'My', 'about_the_author': 'About to be updated Info',
                        'last_name': 'Doe', 'date_of_birth': date_of_birth, 'date_of_death': date_of_death}

        response = self.second_date_comes_first_incorrect(data, 'author-list', Author)


class BookAPIViewTest(MainTestCase):

    def setUp(self):
        data_author = {'first_name': 'John', 'about_the_author': 'XXX Info',
                        'last_name': 'Doe', 'date_of_birth': '2000-12-21', 'date_of_death': '2011-11-14'}

        response = self.post_category_by_authenticated_user(data_author, 'author-list', Author)

        self.post_another_category({'name': 'Spanish'}, 'language-list', Language)
        self.post_another_category({'name': 'English'}, 'language-list', Language)
        self.post_another_category({'name': 'Japanese'}, 'language-list', Language)

        self.post_another_category({'name': 'Literatures'}, 'genre-list', Genre)
        self.post_another_category({'name': 'History'}, 'genre-list', Genre)
        self.post_another_category({'name': 'Elven Literature'}, 'genre-list', Genre)
        self.post_another_category({'name': 'Medieval Literature'}, 'genre-list', Genre)

    def additional_declarations(self):
        published_date = datetime.date.today() - datetime.timedelta(weeks=155)
        date_added = datetime.date.today()
        genre_one = reverse('genre-detail', kwargs={'pk': Genre.objects.get(pk=1).pk})
        genre_two = reverse('genre-detail', kwargs={'pk': Genre.objects.get(pk=2).pk})
        genred = [genre_one, genre_two]

        return published_date, date_added, genred

    def test_list_book(self):

        published_date, date_added, genred = self.additional_declarations()

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        assert response_book.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_get = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_get.status_code == status.HTTP_200_OK

    def test_post_by_authenticated_user(self):

        published_date, date_added, genred = self.additional_declarations()

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        assert response_book.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_get = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_get.status_code == status.HTTP_200_OK

    def test_post_by_unauthorized_user(self):

        published_date, date_added, genred = self.additional_declarations()

        book_data = {'title': 'Book of Johnah', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        self.client.logout()
        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        assert response_book.status_code == status.HTTP_401_UNAUTHORIZED
        assert Book.objects.count() == count_objects

    def test_update_category_by_unanimous_user(self):

        published_date, date_added, genred = self.additional_declarations()

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        assert response_book.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_get = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_get.status_code == status.HTTP_200_OK

        self.client.logout()
        genre_one = reverse('genre-detail', kwargs={'pk': Genre.objects.get(pk=3).pk})
        genre_two = reverse('genre-detail', kwargs={'pk': Genre.objects.get(pk=4).pk})
        genred = [genre_one, genre_two]

        book_updated_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=2).pk}),
                     'genre': genred}

        ################################
        model_obj = Book.objects.get()
        response_update_by_unanimous_user = self.client.patch(reverse('book-detail',
                        kwargs={'pk': Book.objects.get().pk}), book_updated_data, format='json')

        assert response_update_by_unanimous_user.status_code == status.HTTP_401_UNAUTHORIZED
        self.assertIn('Authentication credentials were not provided.', response_update_by_unanimous_user.data.values())

    def test_update_category_by_authorized_user(self):

        published_date, date_added, genred = self.additional_declarations()

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        assert response_book.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_get = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_get.status_code == status.HTTP_200_OK

        genre_one = reverse('genre-detail', kwargs={'pk': Genre.objects.get(pk=3).pk})
        genre_two = reverse('genre-detail', kwargs={'pk': Genre.objects.get(pk=4).pk})
        genred = [genre_one, genre_two]

        book_updated_data = {'title': 'Book of Johnah', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=2).pk}),
                     'genre': genred}

        ################################
        response_update = self.client.patch(reverse('book-detail',
                        kwargs={'pk': Book.objects.get(pk=1).pk}), book_updated_data, format='json')

        assert response_update.status_code == status.HTTP_200_OK

        url_get_genre = reverse('book-detail', None, {Book.objects.get().pk})
        get_responce = self.client.get(url_get_genre, format='json')
        assert get_responce.status_code == status.HTTP_200_OK

        model_obj = Book.objects.get(title = 'Book of Johnah')

    def test_post_category_which_already_exists(self):
        # "The fields title, author must make a unique set."
        published_date, date_added, genred = self.additional_declarations()

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        assert response_book.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_get = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_get.status_code == status.HTTP_200_OK

        book_new_data = {'title': 'Book of John', 'author': Author.objects.get(pk=1),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': Language.objects.get(pk=1),
                     }

        new_object = Book()
        for field, value in book_new_data.items():
                setattr(new_object, field, value)

        try:
            new_object.full_clean()
        except DjangoValidationError as e:
            self.assertIn('Book with this Title and Author already exists.', str(e.args[0]))

    def test_filter_category_name(self):

        published_date, date_added, genred = self.additional_declarations()

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        assert response_book.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_get = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_get.status_code == status.HTTP_200_OK

        book_data_new = {'title': 'Booked of Johned', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 5, 'loaned_copies': 2, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=2).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book_new = self.client.post(reverse('book-list'), book_data_new, format='json')

        assert response_book_new.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_book_new = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_book_new.status_code == status.HTTP_200_OK

        filter_data = {'title': 'Booked of Johned',
            'summary': 'Doe', 'copies': 5, 'loaned_copies': 2, 'available_copies': 3, 'published': published_date,
            'date_added': date_added}

        url = f'{reverse("book-list")}?{urlencode(filter_data)}'
        response_filter = self.client.get(url, format='json')

        assert response_filter.status_code == status.HTTP_200_OK

        for key in filter_data:
            self.assertIn(str(filter_data[key]), str(response_filter.data[0][key]))

        try:
            assert response_filter.data[1].exists() == True
            # assert False
        except IndexError:
            assert True

    def test_delete_category(self):
        published_date, date_added, genred = self.additional_declarations()

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        assert response_book.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_get = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_get.status_code == status.HTTP_200_OK

        book_data_new = {'title': 'Booked of Johned', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 5, 'loaned_copies': 2, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=2).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book_new = self.client.post(reverse('book-list'), book_data_new, format='json')

        assert response_book_new.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_book_new = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_book_new.status_code == status.HTTP_200_OK

        count_objects = Book.objects.count()

        url = reverse('book-detail', kwargs={'pk': Book.objects.get(pk=1).pk})
        response_delete = self.client.delete(url)

        assert response_delete.status_code == status.HTTP_204_NO_CONTENT
        assert Book.objects.count() == count_objects - 1

        try:
            url = reverse('book-detail', kwargs={'pk': Book.objects.get(pk=1).pk})
            # assert False
        except Book.DoesNotExist:
            assert True

    def test_delete_category_unauthorized_user(self):
        published_date, date_added, genred = self.additional_declarations()

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        assert response_book.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_get = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_get.status_code == status.HTTP_200_OK

        book_data_new = {'title': 'Booked of Johned', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 5, 'loaned_copies': 2, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=2).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book_new = self.client.post(reverse('book-list'), book_data_new, format='json')

        assert response_book_new.status_code == status.HTTP_201_CREATED
        assert Book.objects.count() == count_objects + 1

        for each_key in book_data:
            response_book_new = self.client.get(reverse('book-list'), {f'{each_key}': book_data[each_key]}, format='json')
            assert response_book_new.status_code == status.HTTP_200_OK

        self.client.logout()

        count_objects = Book.objects.count()

        url = reverse('book-detail', kwargs={'pk': Book.objects.get(pk=1).pk})
        response_delete = self.client.delete(url)

        assert response_delete.status_code == status.HTTP_401_UNAUTHORIZED
        assert Book.objects.count() == count_objects

        try:
            url = reverse('book-detail', kwargs={'pk': Book.objects.get(pk=1).pk})
            # assert False
        except Book.DoesNotExist:
            assert True

    def test_post_book_incorrect_date_added(self):
        published_date, date_added, genred = self.additional_declarations()

        date_added = '2000-xx-21'

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        self.assertIn('Date has wrong format. Use one of these formats instead: YYYY-MM-DD.', list(response_book.data.values())[0])
        assert response_book.status_code == status.HTTP_400_BAD_REQUEST
        assert Book.objects.count() == count_objects

    def test_post_book_incorrect_date_published(self):

        published_date, date_added, genred = self.additional_declarations()

        published_date = '2000-xx-21'

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')
        
        self.assertIn('Date has wrong format. Use one of these formats instead: YYYY-MM-DD.', list(response_book.data.values())[0])
        assert response_book.status_code == status.HTTP_400_BAD_REQUEST
        assert Book.objects.count() == count_objects

    def test_post_date_added_in_future(self):

        published_date, date_added, genred = self.additional_declarations()

        date_added = '2020-11-21'

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        self.assertEqual(response_book.status_code, status.HTTP_400_BAD_REQUEST)
        assert Book.objects.count() == count_objects
        self.assertIn('Invalid date logic declaration! Check the dates and reconfigure them accordingly!',
                      str(response_book.data.values()))

    def test_post_date_published_in_future(self):

        published_date, date_added, genred = self.additional_declarations()

        published_date = '2020-11-21'

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        self.assertEqual(response_book.status_code, status.HTTP_400_BAD_REQUEST)
        assert Book.objects.count() == count_objects
        self.assertIn('Invalid date logic declaration! Check the dates and reconfigure them accordingly!',
                      str(response_book.data.values()))

    def test_date_added_prior_to_date_published(self):

        published_date, date_added, genred = self.additional_declarations()

        published_date = '2001-11-21'
        date_added = '2000-11-21'

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 0, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        self.assertEqual(response_book.status_code, status.HTTP_400_BAD_REQUEST)
        assert Book.objects.count() == count_objects
        self.assertIn('Incorrect date logic assignment! Check how the dates are set and reconfigure them accordingly!',
                      str(response_book.data.values()))

    def test_post_incorrect_copies_number(self):

        published_date, date_added, genred = self.additional_declarations()

        published_date = '2011-11-21'
        date_added = '2000-11-21'

        book_data = {'title': 'Book of John', 'author': reverse('author-detail', None, {Author.objects.get(pk=1).pk}),
            'summary': 'Doe', 'copies': 3, 'loaned_copies': 1, 'available_copies': 3, 'published': published_date,
            'date_added': date_added, 'language': reverse('language-detail', None, {Language.objects.get(pk=1).pk}),
                     'genre': genred}

        count_objects = Book.objects.count()
        response_book = self.client.post(reverse('book-list'), book_data, format='json')

        self.assertEqual(response_book.status_code, status.HTTP_400_BAD_REQUEST)
        assert Book.objects.count() == count_objects
        self.assertIn('Incorrect values. Total copies should match the aggregate of available and loaned copies',
                      str(response_book.data.values()))
























