import pytest
from django.urls import reverse
from user.tests.conftest import api_client_with_credentials

pytestmark = pytest.mark.django_db


class TestCertificate:
    certificate_list = reverse("certificates:certificate-list")

    @pytest.mark.parametrize(
        'user_role',
        [["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_admin_retrieves_certificate(self, user_role,user_factory,certificate_factory,course_factory, api_client, authenticate_user):
        user = authenticate_user(roles=user_role)
        certificate_factory.create_batch(5, user=user_factory(), course = course_factory())
        token = user['token']
        api_client_with_credentials(token, api_client)
        response = api_client.get(self.certificate_list)
        assert response.status_code == 200
        assert response.json()['total'] == 5
    
    def test_student_retrieves_only_personal_certificate(self,user_factory,certificate_factory,course_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["STUDENT"])
        token = user['token']
        certificate_factory.create_batch(5, user=user_factory(), course = course_factory())
        certificate_factory(user = user['user_instance'], course = course_factory())
        api_client_with_credentials(token, api_client)
        response = api_client.get(self.certificate_list)
        assert response.status_code == 200
        assert response.json()['total'] == 1

    
    def test_verify_certificate(self,user_factory,certificate_factory,course_factory, api_client):
        certificate = certificate_factory(user = user_factory(), course = course_factory())
        url = reverse("certificates:certificate-verify-certificate", kwargs={'certificate_id':certificate.certificate_id})
        response = api_client.get(url)
        retuned_response = response.json()['data']
        assert response.status_code == 200
        assert "course" in retuned_response
        assert "user" in retuned_response
        assert "certificate_id" in retuned_response
        
    def test_enrolled_student_generate_certificate(self,mocker,enroll_student_factory,course_factory, api_client, authenticate_user):
        mock_process_certificate_in_background = mocker.patch(
            'certificate.tasks.process_user_course_certificate.delay')
        user = authenticate_user(roles=["STUDENT"])
        token = user['token']
        course = course_factory()
        enroll_student_factory(user=user['user_instance'], course=course)
        api_client_with_credentials(token, api_client)
        data = {
            "course": str(course.id)
        }
        response = api_client.post(self.certificate_list, data, format="json")
        assert response.status_code == 200
        mock_process_certificate_in_background.side_effect = print(
            "Sent to celery task:Certificate Processing!")
        
        background_process_data = {
            'user_id':user['user_instance'].id,
            'user_name':user['user_instance'].firstname + " " + user['user_instance'].lastname,
            'email':user['user_instance'].email,
            'course_name': course.course_name,
            'course_id': course.id,
        }
        
        mock_process_certificate_in_background.assert_called_once_with(background_process_data)
    
    def test_prevent_duplicate_certificate_generation(self,enroll_student_factory,user_factory,certificate_factory,course_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["STUDENT"])
        token = user['token']
        course = course_factory()
        enroll_student_factory(user=user['user_instance'], course=course)
        certificate_factory(user=user['user_instance'], course =  course)
        api_client_with_credentials(token, api_client)
        data = {
            "course": str(course.id)
        }
        response = api_client.post(self.certificate_list, data, format="json")
        assert response.status_code == 400
    
    def test_prevent_generate_certificate_to_nonenrolled(self,course_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["STUDENT"])
        token = user['token']
        course = course_factory()
        api_client_with_credentials(token, api_client)
        data = {
            "course": str(course.id)
        }
        response = api_client.post(self.certificate_list, data, format="json")
        assert response.status_code == 400
    