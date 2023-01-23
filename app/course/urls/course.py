from rest_framework.routers import DefaultRouter
from django.urls import path, include
from ..views import CourseViewSets, EnrollStudentViewSets,TransactionViewSets

app_name = "course"
router = DefaultRouter()
router.register("", CourseViewSets)
router.register("enrollment", EnrollStudentViewSets)
router.register("transaction", TransactionViewSets)

urlpatterns = [
    path("", include(router.urls)),
]

print(router.urls)