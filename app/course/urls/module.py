from django.urls import include, path

from rest_framework.routers import DefaultRouter

from ..views import ModuleViewSets

app_name = "modules"

router = DefaultRouter()

router.register("", ModuleViewSets)

urlpatterns = [
    path("", include(router.urls)),
]
