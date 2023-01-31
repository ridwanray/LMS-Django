import pytest
from certificate.utils import generate_certificate

pytestmark = pytest.mark.django_db

def test_generate_certificate_task(user_factory, course_factory):
    user =  user_factory()
    course = course_factory()
    cert_info = {
        'user_id' : user.id,
        'user_name' : user.firstname,
        'email': user.email,
        'course_name': course.course_name,
        'course_id': course.id,
    }
    generate_certificate(**cert_info)