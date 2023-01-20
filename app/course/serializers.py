from rest_framework import serializers
from user.serializers import BasicUserInfoSerializer
from .models import Course, EnrollStudent, Module, ModuleAssignmentSubmission, Transaction
from user.models import User
from core.utils.validators import is_admin, is_course_teacher

class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        exclude = ("approved_by",)
        
        extra_kwargs = {
            "created_by": {"read_only": True},
            "is_active": {"read_only": True},
        }
        
    def validate(self, attrs):
        user: User = self.context["request"].user
        if self.instance:
            if not is_admin(user) and user not in self.instance.teachers:
                raise serializers.ValidationError({"course":"You can only edit a course you teach."})
        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['teachers'] = BasicUserInfoSerializer(
            instance=instance.teachers, many=True).data
        return data



class EnrollStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrollStudent
        fields = ['user', 'course', 'date_enrolled','amount_paid']
        extra_kwargs = {
            "amount_paid": {"read_only": True},
        }


class CreateModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

        extra_kwargs = {
            "created_by": {"read_only": True},
            "completed_by": {"read_only": True},
        }

    def validate(self, attrs):
        user: User = self.context["request"].user
        course: Course = attrs.get("course")
        if not is_course_teacher(user,course):
            raise serializers.ValidationError(
                {'course': 'You can only create a module for a course you teach.'})
        return super().validate(attrs)


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'
        

class BasicModuleSerializer(serializers.ModelSerializer):
    '''Serializer for the not enrolled user'''
    class Meta:
        fields = ['module_name','module_order','topic']
        model = Module


class ModuleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleAssignmentSubmission
        fields = '__all__'
        extra_kwargs = {
            "user": {"read_only": True},
        }


class BulkUpdateMarkAsCompletedSerializer(serializers.Serializer):
    '''Mark multiple modules as completed'''
    modules = serializers.PrimaryKeyRelatedField(
        queryset=Module.objects.all(), many=True, write_only= True)
    is_completed = serializers.BooleanField(required=True)
    
    def update(self, validated_data):
        user = self.context["request"].user
        for module in validated_data["modules"]:
            module.completed_by.add(user) if validated_data[
                "is_read"
            ] else module.completed_by.remove(user)
        _returned = {"is_read": validated_data["is_read"]}
        return _returned

class TransactionSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.course_name")
    class Meta:
        model = Transaction
        fields = '__all__'
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("user")
        data['payed_by'] = instance.user
        return data