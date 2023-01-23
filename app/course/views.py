from typing import List
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Exists, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from user.serializers import BasicUserInfoSerializer
from core.utils.validators import is_admin, is_course_teacher
from user.models import User
from course.models import Course, Transaction
from rest_framework import serializers
from user.permissions import IsSuperAdmin, IsTeacher, IsStudent, IsSchoolAdmin
from .models import Course, EnrollStudent, Module
from .serializers import (BulkUpdateMarkAsCompletedSerializer, CourseSerializer, EnrollStudentSerializer,
                          ModuleAssignmentSerializer, ModuleSerializer, TransactionSerializer,
                          CreateModuleSerializer, BasicModuleSerializer,CourseUpdateSerializer)


class CourseViewSets(viewsets.ModelViewSet):
    queryset = Course.objects.all().prefetch_related("teachers").select_related("created_by")
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "put"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active"]
    search_fields = ["course_name", "display_title",
                     "short_description", "long_description"]
    ordering_fields = ["created_at", "display_title",
                       "short_description", "is_active"]

    def list(self, request, *args, **kwargs):
        '''Returns all courses available'''
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        '''Returns details of a single course'''
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        '''Create a new course '''
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ["partial_update", "update"]:
            return CourseUpdateSerializer
        return self.serializer_class

    def get_permissions(self):
        permission_classes = self.permission_classes
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        elif self.action in ["create", "partial_update", "update"]:
            permission_classes = [IsTeacher | IsSuperAdmin | IsSchoolAdmin]
        elif self.action in ["destroy"]:
            permission_classes = [IsSuperAdmin | IsSchoolAdmin]
        return [permission() for permission in permission_classes]

    def update(self, request, *args, **kwargs):
        """This endpoint updates a course"""
        partial = kwargs.pop("partial", False)
        course_instance:  Course = self.get_object()
        serializer = CourseUpdateSerializer(
            data=request.data, instance=course_instance, partial=partial,
            context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data}, status=200)

    @action(
        detail=True,
        methods=["GET"],
        permission_classes=[AllowAny],
        serializer_class=BasicModuleSerializer,
        url_path="modules",
    )
    def get_course_modules(self, request, *args, **kwargs):
        '''Returns all modules available for course'''
        user = self.request.user
        course_instance: Course = self.get_object()
        modules: List(Module) = course_instance.modules
        enrolled_students_qs = course_instance.enrolled_students.all()
        is_enrolled_student =enrolled_students_qs.filter(user=user).exists()
        serializer_class_ = ModuleSerializer if is_admin(
            user) or is_enrolled_student or user in course_instance.teachers.all() else BasicModuleSerializer
        data = serializer_class_(
            instance=modules, context={"request": request}, many=True
        ).data
        return Response({"success": True, "data": data}, status.HTTP_200_OK)


class EnrollStudentViewSets(viewsets.ModelViewSet):
    queryset = EnrollStudent.objects.all().select_related("user", "course")
    serializer_class = EnrollStudentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["course", "user"]
    ordering_fields = ["created_at", ]

    def get_queryset(self):
        '''Returns enrolled students base on permission'''
        auth_user: User = self.request.user
        if is_admin(auth_user):
            return self.queryset.all()
        if "TEACHER" in auth_user.roles:
            return self.queryset.filter(Q(course__teachers=auth_user) & Q(user=auth_user))
        if "STUDENT" in auth_user.roles:
            return self.queryset.filter(user=auth_user)
        return self.queryset.none()

    def get_permissions(self):
        permission_classes = self.permission_classes
        if self.action in "create":
            permission_classes = [IsStudent]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [IsTeacher, IsSchoolAdmin, IsStudent]
        elif self.action in ["destroy"]:
            permission_classes = [IsSuperAdmin]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        '''Returns all enrolled students'''
        return super().list(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def retrieve(self, request, *args, **kwargs):
        '''A unique identifier for this enrolled student'''
        return super().retrieve(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsSchoolAdmin | IsSuperAdmin | IsTeacher],
        serializer_class=BasicUserInfoSerializer,
        url_path=r"(?P<course_id>[\w-]+)",
    )
    def get_enrolled_students(self, request, course_id, pk=None):
        '''Returns all students enrolled for this course'''
        auth_user = self.request.user
        course_instance = get_object_or_404(Course, course_id)
        if not is_admin(auth_user) and not is_course_teacher(auth_user, course_instance):
            return Response({"success": False, "message": "You cannot retrieve students for a course you are don't teach"}, 400)
        students: User = course_instance.enrolled_students
        serializer = BasicUserInfoSerializer(instance=students, many=True)
        return Response({"success": True, "data": serializer.data}, status.HTTP_200_OK)


class ModuleViewSets(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Module.objects.all().select_related('course')
    http_method_names = ["post", "put", "delete"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    ordering_fields = ["name"]
    search_fields = ["module_name", "topic", "text_cotent"]
    pagination_class = None
    serializer_class = ModuleSerializer

    def get_permissions(self):
        permission_classes = self.permission_classes
        if self.action in ["create", "update", "delete"]:
            permission_classes = [IsTeacher | IsSchoolAdmin | IsSuperAdmin]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return CreateModuleSerializer
        return self.serializer_class

    def create(self, request, **kwargs):
        '''Create a new module for a course'''
        serializer = self.get_serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(data={"success": True, "data": serializer.data}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["POST"],
        permission_classes=[IsStudent],
        serializer_class=ModuleAssignmentSerializer,
        url_path="submit-assignment",
    )
    def submit_module_assignment(self, request, *args, **kwargs):
        '''Allows student to submit module assignment'''
        course_instance = self.get_object()
        modules = course_instance.modules
        data = ModuleSerializer(
            instance=modules, context={"request": request}, many=True
        ).data
        return Response({"success": True, "data": data}, status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: inline_serializer(
                name='CompleteStatus',
                fields={
                    "success": serializers.BooleanField(default=True),
                    "message": serializers.CharField(default="Module marked as completed")
                }
            ),
        },
    ) 
    @action(methods=['PUT'], detail=False, serializer_class=BulkUpdateMarkAsCompletedSerializer, url_path="mark-complete")
    def bulk_update_complete_status(self, request, pk=None):
        """Allows a user  to mark multiple modules as completed & undo"""
        serializer = BulkUpdateMarkAsCompletedSerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)
        return Response({'success': False, 'errors': serializer.errors}, status.HTTP_400_BAD_REQUEST)


class TransactionViewSets(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().select_related("user", "course")
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["course", "user", ]
    ordering_fields = ["created_at", ]

    def get_queryset(self):
        auth_user: User = self.request.user
        if is_admin(auth_user):
            return self.queryset.all()
        return self.queryset.filter(user=auth_user)
    
    def list(self, request, *args, **kwargs):
        """Returns all transactions"""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(exclude=True)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsSchoolAdmin | IsSuperAdmin],
        serializer_class=TransactionSerializer,
        url_path=r"(?P<course_id>[\w-]+)",
    )
    def get_course_transactions(self, request, course_id, pk=None):
        '''Returns all transactions for this course'''
        course_instance = get_object_or_404(Course, course_id)
        transactions: Transaction = course_instance.transactions
        serializer = TransactionSerializer(instance=transactions, many=True)
        return Response({"success": True, "data": serializer.data}, status.HTTP_200_OK)