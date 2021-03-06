from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views



router = DefaultRouter()
router.register(r'genre', views.GenreView)
router.register(r'language', views.LanguageView)
router.register(r'author', views.AuthorView)
router.register(r'book', views.BookView)
router.register(r'bookinstance', views.BookInstanceView)
router.register(r'users', views.UserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('simpletest/', views.GenerateRandomUserView.as_view()),
]
