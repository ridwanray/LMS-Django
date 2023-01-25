from typing import List
from user.models import User
from course.models import Course,Module
from rest_framework import serializers

def is_admin(user: User)->bool:
    '''Checks if a user is a superadmin or school admin'''
    user_roles: List[str]  = user.roles
    if "SUPER_ADMIN" in user_roles:
        return True
    
    if "SCHOOL_ADMIN" in user_roles:
        return True
    return False

def is_course_teacher(user: User, course:Course)->bool:
    """Checks if auth user is a teacher of this course"""
    course_teachers: User = course.teachers.all()
    if user in course_teachers:
        return True
    return False
 
def is_course_student(user: User, module: Module)->bool:
    enrolled_students_qs = module.course.enrolled_students.all()
    if not enrolled_students_qs.filter(user=user).exists():
            raise serializers.ValidationError({"module": "You are not enrolled for this course."})
    return True