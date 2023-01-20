from .views import QuizViewSets
from rest_framework.routers import DefaultRouter
from django.urls import path, include

app_name = "quiz"

router = DefaultRouter()
router.register("", QuizViewSets)

urlpatterns = [
    path("", include(router.urls)),
]
