from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views



router = DefaultRouter()
router.register(r'profile', views.ProfileViewSet)
router.register(r'user', views.UserViewSet)
router.register(r'group', views.GroupViewSet)


urlpatterns = [
    path('', include(router.urls))
]
