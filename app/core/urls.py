from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/doc/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/api-auth/', include('rest_framework.urls')),
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
    path('api/v1/users/', include('user.urls.user')),
    path('api/v1/auth/', include('user.urls.auth')),  
    path('api/v1/courses/', include('course.urls.course')),  
    path('api/v1/modules/', include('course.urls.module')),
    path('api/v1/transactions/', include('course.urls.transaction')),
    path('api/v1/quizzes/', include('quiz.urls')),
    path('api/v1/certificates/', include('certificate.urls')),
  

]
