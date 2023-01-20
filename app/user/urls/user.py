from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import UserViewsets

app_name = 'user'

router = DefaultRouter()
router.register('', UserViewsets)

urlpatterns = [
    path('', include(router.urls)),
]
