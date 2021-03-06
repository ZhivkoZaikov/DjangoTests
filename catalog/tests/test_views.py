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
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework.test import APITestCase, APIRequestFactory, APIClient
from rest_framework.authtoken.models import Token

from .. import views
from ..models import Genre, Language, Author, Book

class MainTestCase(APITestCase):

    # @staticmethod
    # def setup_user():
    #     User = get_user_model()
    #     return User.objects.create_user(
    #         'myuser',
    #         email='testuser@test.com',
    #         password='pass1234'
    #     )
    #
    # def create_user_and_set_token_credentials(self):
    #     self.c = APIClient()
    #     self.user = self.setup_user()
    #     self.token = Token.objects.create(user=self.user)
    #     self.token.save()
    #     self.c.login(username='myuser', password='pass1234')

    # username='myuser', email='myemail@yahoo.com', password='pass1234'
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
