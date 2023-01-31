from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from user.models import  User
from course.models import Course, Transaction
from rest_framework import serializers
from user.permissions import  IsSuperAdmin,IsTeacher, IsStudent,IsSchoolAdmin
from core.utils.validators import is_admin
from .models import Certificate
from .serializers import (
    GenerateCertificateSerializer, ListCertificateSerializer,
    VerifyCertificateResponseSerializer
    )


class CertificateViewSets(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Certificate.objects.all().select_related('course','user')
    http_method_names = ["get","post"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    ordering_fields = ["user"]
    search_fields = ["certificate_id", "course__course_name",]
    serializer_class = ListCertificateSerializer
    
    def get_queryset(self):
        auth_user: User = self.request.user
        if is_admin(auth_user):
            return self.queryset.all()
        return self.queryset.filter(user=auth_user)
    
    def get_permissions(self):
        permission_classes = self.permission_classes
        if self.action == "verify_certificate":
            permission_classes = [AllowAny]
        if self.action == "create":
            permission_classes = [IsStudent | IsTeacher]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == "create":
            return GenerateCertificateSerializer
        if self.action == "list":
            return ListCertificateSerializer
        if self.action == "verify_certificate":
            return VerifyCertificateResponseSerializer
        return self.serializer_class
    
    def create(self, request, *args, **kwargs):
        """Allows a student to generate certificate"""
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={"success": True, "message": "Your certificate is being processed. It will be sent to your mail shortly."}, status=200)

    @action(
        detail=False,
        methods=["GET"],
        url_path=r"verify/(?P<certificate_id>[\w-]+)",
    )
    def verify_certificate(self, request, certificate_id, pk=None):
        '''Checks if a certificate is real'''
        instance = get_object_or_404(Certificate,certificate_id=certificate_id)
       
        data =VerifyCertificateResponseSerializer(instance=instance).data
        return Response({"success": True, "data": data}, status.HTTP_200_OK)
   