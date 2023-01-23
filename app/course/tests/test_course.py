import pytest
from django.urls import reverse
from rest_framework import status
from user.tests.conftest import api_client_with_credentials


pytestmark = pytest.mark.django_db


class TestRetrieveCourse:
    course_list_url = reverse("course:course-list")

    def test_user_retrieve_course(self, api_client, course_factory, user_factory, active_user):
        '''Allows all user type(auth&unauth) to see course list'''
        teachers = user_factory.create_batch(2)
        course_factory.create_batch(
            2, teachers=teachers, created_by=active_user)
        response = api_client.get(self.course_list_url)
        assert response.status_code == 200
        returned_response = response.json()
        assert returned_response['total'] == 2
        # confirm number of teachers in created course
        teachers_in_response = returned_response['results'][0]['teachers']
        assert len(teachers_in_response) == 2

    def test_retrieve_course_details(self , api_client, course_factory, user_factory, active_user):
        """Any person can retrieve course details"""
        teachers = user_factory.create_batch(3)
        course = course_factory(teachers=teachers, created_by=active_user)
        url = reverse("course:course-detail", kwargs={"pk": course.id})
        response = api_client.get(url)
        assert response.status_code == 200
        returned_response = response.json()
        assert returned_response['course_name'] == course.course_name
        assert returned_response['id'] == str(course.id)
        assert len(returned_response['teachers']) == len(teachers)

    @pytest.mark.parametrize(
        'user_role',
        [["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_retrieve_all_module_content_for_admin_or_teacher(self, api_client, user_role, authenticate_user, course_factory, module_factory, user_factory, active_user):
        user = authenticate_user(roles=user_role)
        token = user['token']
        api_client_with_credentials(token, api_client)
        course = course_factory()
        module_factory.create_batch(3, course=course)
        url = reverse("course:course-get-course-modules",
                      kwargs={"pk": course.id})
        response = api_client.get(url)
        returned_json = response.json()
        assert response.status_code == 200
        assert len(returned_json['data']) == 3
        for module in returned_json['data']:
            assert "video_link" in module
            assert "text_cotent" in module
            assert "practical_work_sheet" in module

    def test_retrieve_all_module_content_for_enrolled_student(self, api_client, enroll_student_factory, module_factory, course_factory, authenticate_user):
        user = authenticate_user(roles=["STUDENT"])
        token = user['token']
        api_client_with_credentials(token, api_client)
        course = course_factory()
        module_factory.create_batch(3, course=course)
        enroll_student_factory.create(
            user=user['user_instance'], course=course)
        url = reverse("course:course-get-course-modules",
                      kwargs={"pk": course.id})
        response = api_client.get(url)
        returned_json = response.json()
        assert response.status_code == 200
        assert len(returned_json['data']) == 3
        for module in returned_json['data']:
            assert "video_link" in module
            assert "text_cotent" in module
            assert "practical_work_sheet" in module

    def test_retrieve_basic_module_content_for_unenrolled_student(self, api_client, module_factory, course_factory, authenticate_user):
        user = authenticate_user(roles=["STUDENT"])
        token = user['token']
        api_client_with_credentials(token, api_client)
        course = course_factory()
        module_factory.create_batch(3, course=course)
        url = reverse("course:course-get-course-modules",
                      kwargs={"pk": course.id})
        response = api_client.get(url)
        returned_json = response.json()
        assert response.status_code == 200
        assert len(returned_json['data']) == 3
        for module in returned_json['data']:
            assert "video_link" not in module
            assert "text_cotent" not in module
            assert "practical_work_sheet" not in module
    
    def test_course_teacher_retrieves_all_module_details(self, api_client, module_factory, course_factory, authenticate_user):
        user = authenticate_user(roles=["TEACHER"])
        token = user['token']
        api_client_with_credentials(token, api_client)
        course = course_factory(teachers= [user['user_instance']])
        module_factory.create_batch(2, course=course)
        url = reverse("course:course-get-course-modules",
                      kwargs={"pk": course.id})
        response = api_client.get(url)
        returned_json = response.json()
        assert len(returned_json['data']) == 2
        for module in returned_json['data']:
            assert "video_link"  in module
            assert "text_cotent"  in module
            assert "practical_work_sheet"  in module
            
    def test_retrieves_basic_module_details_to_non_teaching_teacher(self, api_client, module_factory, course_factory, authenticate_user):
        """Only retrieve basic module detail to a teacher not teaching the course"""
        user = authenticate_user(roles=["TEACHER"])
        token = user['token']
        api_client_with_credentials(token, api_client)
        course = course_factory()
        module_factory.create_batch(2, course=course)
        url = reverse("course:course-get-course-modules",
                      kwargs={"pk": course.id})
        response = api_client.get(url)
        returned_json = response.json()
        assert len(returned_json['data']) == 2
        for module in returned_json['data']:
            assert "video_link" not in module
            assert "text_cotent" not in module
            assert "practical_work_sheet" not   in module

class TestCreateCourse:
    course_list = reverse("course:course-list")

    @pytest.mark.parametrize(
        'user_role',
        [["TEACHER"], ["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_create_course(self, user_role, api_client, authenticate_user):
        user = authenticate_user(roles=user_role)
        token = user['token']
        api_client_with_credentials(token, api_client)
        course_data = {
            "course_name": "MAT 101",
            "course_price": 90,
            "display_title": "Just Title",
        }
        response = api_client.post(
            self.course_list, course_data, format="json")
        returned_json = response.json()
        assert response.status_code == status.HTTP_201_CREATED
        assert returned_json['course_name'] == "MAT 101"
        assert returned_json['course_price'] == '90.00'
        assert returned_json['display_title'] == "Just Title"
        assert returned_json['teachers'] == []
        assert returned_json['created_by']['email'] == user['user_email']

    def test_deny_create_course(self, api_client, authenticate_user):
        """A student cannot create a course"""
        user = authenticate_user(roles=["STUDENT"])
        token = user['token']
        api_client_with_credentials(token, api_client)
        course_data = {
            "course_name": "MAT 101",
            "course_price": 90,
            "display_title": "Just Title",
        }
        response = api_client.post(
            self.course_list, course_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_deny_create_course_unauthenticated(self, api_client):
        course_data = {
            "course_name": "MAT 101",
            "course_price": 90,
            "display_title": "Just Title",
        }
        response = api_client.post(
            self.course_list, course_data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateDeleteCourse:

    @pytest.mark.parametrize(
        'user_role',
        [["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_update_course(self, user_role, api_client, course_factory, authenticate_user):
        """Allows superadmin/schooladmin to update course"""
        user = authenticate_user(roles=user_role)
        user_id = user['user_instance'].id
        token = user['token']
        course = course_factory()

        api_client_with_credentials(token, api_client)
        new_course_data = {
            "course_name": "Updated course Name",
            "course_price": 750,
            "display_title": "Updated title",
            "teachers": [str(user_id)]
        }
        url = reverse("course:course-detail", kwargs={"pk": course.id})
        response = api_client.patch(url, new_course_data)
        assert response.status_code == 200
        returned_json = response.json()['data']
        assert returned_json['course_name'] == new_course_data["course_name"]
        assert returned_json['course_price'] == "750.00"
        assert returned_json['display_title'] == new_course_data["display_title"]
        assert returned_json['teachers'] == new_course_data["teachers"]

    def test_course_teacher_update_course(self, api_client, course_factory, authenticate_user):
        """A teacher can update a course he teaches"""
        user = authenticate_user(roles=["TEACHER"])
        course = course_factory(teachers=[user['user_instance']])
        token = user['token']

        api_client_with_credentials(token, api_client)
        new_course_data = {
            "course_name": "Updated course Name",
            "course_price": 750,
            "display_title": "Updated title",
        }
        url = reverse("course:course-detail", kwargs={"pk": course.id})
        response = api_client.patch(url, new_course_data)
        assert response.status_code == 200
        returned_json = response.json()['data']
        assert returned_json['course_name'] == new_course_data["course_name"]
        assert returned_json['course_price'] == "750.00"
        assert returned_json['display_title'] == new_course_data["display_title"]

    def test_deny_course_update_for_non_teacher(self, api_client, course_factory, authenticate_user):
        """A teacher cannont update a course he's not teaching"""
        user = authenticate_user(roles=["TEACHER"])
        course = course_factory()
        token = user['token']

        api_client_with_credentials(token, api_client)
        new_course_data = {
            "course_name": "Updated course Name",
            "course_price": 750,
            "display_title": "Updated title",
        }
        url = reverse("course:course-detail", kwargs={"pk": course.id})
        response = api_client.patch(url, new_course_data)
        assert response.status_code == 400

    @pytest.mark.parametrize(
        'user_role, request_status',
        [(["TEACHER"], 403), (["SUPER_ADMIN"], 204),
         (["SCHOOL_ADMIN"], 204), (["TEACHER"], 403)]
    )
    def test_course_delete(self, api_client, user_role, request_status, course_factory, authenticate_user):
        """Only Superadmin and school admin can delete a course"""
        user = authenticate_user(roles=user_role)
        course = course_factory()
        token = user['token']
        api_client_with_credentials(token, api_client)
        url = reverse("course:course-detail", kwargs={"pk": course.id})
        response = api_client.delete(url)
        assert response.status_code == request_status
