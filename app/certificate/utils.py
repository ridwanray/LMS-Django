from typing import Dict, List,BinaryIO
from rest_framework import serializers
from course.models import EnrollStudent, Course
from random import choice
from django.utils.crypto import get_random_string
from django.core.files import File
from django.core.files.base import ContentFile

from PIL import Image, ImageFont, ImageDraw
from user.models import User
from .models import Certificate
from .enums import CERTIFICATE_PREFIX


def validate_certificate_generation(user: User, attrs: Dict) -> None:
    course = attrs.get("course")
    enrolled_students_qs: List(EnrollStudent) = course.enrolled_students.all()
    is_enrolled = enrolled_students_qs.filter(user = user).exists()
    if not is_enrolled:
        raise serializers.ValidationError(
            {"course": "Enroll for course to generate certificate."})
    if Certificate.objects.filter(course=course, user=user).exists():
        raise serializers.ValidationError(
            {"course": "You already have a certificate for this course."})
    return


def generate_certificate(**kwargs)->BinaryIO:
    FONT_FILE = ImageFont.truetype(r'certificate/font/Roboto-Black.ttf', 180)
    FONT_COLOR: str = "#FFFFFF"
    is_unique: bool = True
    while is_unique:
        cert_prefix = choice(CERTIFICATE_PREFIX)
        unique_number = get_random_string(10)
        certificate_id = f'{cert_prefix}-{unique_number}'
        is_unique = Certificate.objects.filter(
            certificate_id=certificate_id).exists()
        
    with Image.open('certificate/extra/template.png') as image_source:
        image_source.convert('RGB') 
        WIDTH, HEIGHT = image_source.size
        draw = ImageDraw.Draw(image_source)
        name_width, name_height = draw.textsize(
            kwargs['user_name'], font=FONT_FILE)
        draw.text(((WIDTH - name_width) / 2, (HEIGHT - name_height) / 2 - 30),
                  kwargs['user_name'], fill=FONT_COLOR, font=FONT_FILE)
        
        from io import BytesIO
        buffer = BytesIO()
        image_source.save(buffer, format="PNG", quality=85)
        buffer.seek(0)

        course_instance = Course.objects.get(id=kwargs['course_id'])
        user_instance = User.objects.get(id=kwargs['user_id'])  
        new_certificate: Certificate = Certificate(course=course_instance, 
                                                                user=user_instance, 
                                                                certificate_id=certificate_id, 
                                                               
        )
        new_certificate.file = File(buffer, name="sample.png" )
        new_certificate.save()
       
    return new_certificate