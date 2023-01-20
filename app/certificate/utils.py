from typing import Dict, List,BinaryIO
from rest_framework import serializers
from course.models import EnrollStudent, Course
from random import choice
from django.utils.crypto import get_random_string
from django.db.models.fields.files import File
from PIL import Image, ImageFont, ImageDraw
from user.models import User
from .models import Certificate
from .enums import CERTIFICATE_PREFIX


def validate_certificate_generation(user: User, attrs: Dict) -> None:
    course = attrs.get("course")
    enrolled_students: List(EnrollStudent) = course.enrolled_students
    if user not in enrolled_students:
        raise serializers.ValidationError(
            {"course": "Enroll for course to generate certificate."})
    if Certificate.objects.filter(course=course, user=user).exists():
        raise serializers.ValidationError(
            {"course": "You already have a certificate for this course."})
    return


def generate_certificate(**kwargs)->BinaryIO:
    FONT_FILE = ImageFont.truetype(r'font/Roboto-Black.ttf', 180)
    FONT_COLOR: str = "#FFFFFF"
    is_unique: bool = True
    while is_unique:
        cert_prefix = choice(CERTIFICATE_PREFIX)
        unique_number = get_random_string(10)
        certificate_id = f'{cert_prefix}-{unique_number}'
        is_unique = Certificate.objects.filter(
            certificate_id=certificate_id).exists()

    with Image.open(r'extra/template.png') as image_source:
        WIDTH, HEIGHT = image_source.size
        draw = ImageDraw.Draw(image_source)
        name_width, name_height = draw.textsize(
            kwargs['user_name'], font=FONT_FILE)
        draw.text(((WIDTH - name_width) / 2, (HEIGHT - name_height) / 2 - 30),
                  kwargs['user_name'], fill=FONT_COLOR, font=FONT_FILE)

    course_instance = Course.objects.get(id=kwargs['course_id'])
    user_instance = User.objects.get(id=kwargs['user_id'])
    new_certificate: Certificate = Certificate.objects.create(course=course_instance, user=user_instance, certificate_id=certificate_id,
                               pdf=image_source)
    return new_certificate.pdf