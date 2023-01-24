from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from course.models import Module
from user.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, inline_serializer
from user.permissions import IsSchoolAdmin, IsSuperAdmin, IsTeacher, IsStudent
from rest_framework.decorators import action
from core.utils.validators import is_admin
from .serializers import (
    QuizCreateSerializer, QuizUpdateSerializer,AttemptQuizSerializer,
    QuizSerializer, QuizDetailsSerializer,CreatModuleQuizQuestionSerializer)
from .models import Quiz


class QuizViewSets(viewsets.ModelViewSet):
    queryset = Quiz.objects.all().select_related("module")
    serializer_class = QuizSerializer
    http_method_names = ["get", "post", "patch", "delete", "put"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["quiz_name", "module__name"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return QuizCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return QuizUpdateSerializer
        elif self.action == "retrieve":
            return QuizDetailsSerializer
        elif self.action == "set_module_quiz_questions":
            return CreatModuleQuizQuestionSerializer
        elif self.action == "attempt_module_quiz":
            return AttemptQuizSerializer
        return self.serializer_class

    def get_permissions(self):
        permission_classes = self.permission_classes
        if self.action in ["create", "update", "partial_update","delete"]:
            permission_classes = [IsTeacher| IsSchoolAdmin | IsSuperAdmin]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [IsTeacher | IsSuperAdmin | IsStudent]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user: User = self.request.user
        if is_admin(user):
            return self.queryset.all()
        return self.queryset.filter( Q(module__course__teachers=user) | Q(module__course__enrolled_students__user=user))
    

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        responses={
            200: inline_serializer(
                name='QuestionCreateCompleteStatus',
                fields={
                    "success": serializers.BooleanField(default=True),
                    "message": serializers.CharField(default = "Module quiz's questions created!")
                }
            ),
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsTeacher | IsSuperAdmin | IsSchoolAdmin],
        url_path=r"set-questions/(?P<module_id>[\w-]+)",
    )
    def set_module_quiz_questions(self, request, module_id, pk=None):
        '''Allows a teacher to set module quiz questions'''
        module: Module =  get_object_or_404(Module, id=module_id)
        serializer =  CreatModuleQuizQuestionSerializer(
            data=request.data, context={
                "request": request, "module":module})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Successfully set module questions"}, status=200)

    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsStudent],
        url_path=r"attempt-quiz/(?P<module_id>[\w-]+)",
    )
    def attempt_module_quiz(self, request, module_id, pk=None):
        '''Allows a student to participate in a quiz'''
        module: Module =  get_object_or_404(Module, id=module_id)
        serializer =  self.get_serializer_class(
            data=request.data, context={
                "request": request, "module":module})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Successfully set module questions"}, status=200)
