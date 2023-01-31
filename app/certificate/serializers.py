from typing import Dict
from rest_framework import serializers
from user.models import User
from course.models import Course
from .models import Certificate
from .utils import validate_certificate_generation
from .tasks import process_user_course_certificate


class ListCertificateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Certificate
        fields = [
            "id",
            "course",
            "user",
            "certificate_id",
            "grade",
            "file",
        ]
        extra_kwargs = {
            "pdf": {"read_only": True},
            "grade": {"read_only": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = f'{instance.user.firstname} {instance.user.lastname} '
        return data


class GenerateCertificateSerializer(serializers.Serializer):
    course =  serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), required=True
    )
    
    def validate(self, attrs):
        user = self.context["request"].user
        validate_certificate_generation(user,attrs)
        return super().validate(attrs)
    
    def create(self, validated_data):
        user: User = self.context["request"].user
        course: Course = validated_data.get("course")
        cert_info : Dict = {
            'user_id':user.id,
            'user_name':f'{user.firstname}  {user.lastname}',
            'email':user.email,
            'course_name': course.course_name,
            'course_id': course.id,
            
        }
        process_user_course_certificate.delay(cert_info)
        return validated_data
 

class VerifyCertificateResponseSerializer(serializers.ModelSerializer):
    course = serializers.CharField(source="course.course_name")
    class Meta:
        model = Certificate
        fields = [
            "course",
            "user",
            "certificate_id",
            "grade",
        ]
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = f'{instance.user.firstname} {instance.user.lastname} '
        return data
 