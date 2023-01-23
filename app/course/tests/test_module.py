import pytest
from django.urls import reverse
from course.models import Course, Module
from user.tests.conftest import api_client_with_credentials


pytestmark = pytest.mark.django_db


class TestCreateModule:
    
    create_module_url = reverse("modules:module-list")

    @pytest.mark.parametrize(
        'user_role',
        [["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_admin_create_module(self, user_role,course_factory, api_client, authenticate_user):
        course = course_factory()
        user = authenticate_user(roles=user_role)
        token = user['token']
        api_client_with_credentials(token, api_client)
        module_data = {
            "module_name": "MAT 101",
            "module_order": 1,
            "text_content": "Just Title",
            "course": str(course.id)
        }
        response = api_client.post(
            self.create_module_url, module_data, format="json")
        returned_json = response.json()
        assert response.status_code == 200
        assert returned_json['data']['module_name'] == 'MAT 101'
        assert returned_json['data']['text_content'] == 'Just Title'
    
    def test_course_teacher_create_module(self, course_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["TEACHER"])
        course = course_factory(teachers=[user['user_instance']])
        token = user['token']
        api_client_with_credentials(token, api_client)
        module_data = {
            "module_name": "MAT 101",
            "module_order": 1,
            "text_content": "Just Title",
            "course": str(course.id)
        }
        response = api_client.post(
            self.create_module_url, module_data, format="json")
        returned_json = response.json()
        assert response.status_code == 200
        assert returned_json['data']['module_name'] == 'MAT 101'
        assert returned_json['data']['text_content'] == 'Just Title'
    
    def test_deny_create_module_to_nonteaching(self, course_factory, api_client, authenticate_user):
        """A user can only create a module for a course he teaches"""
        user = authenticate_user(roles=["TEACHER"])
        course = course_factory()
        token = user['token']
        api_client_with_credentials(token, api_client)
        module_data = {
            "module_name": "MAT 101",
            "module_order": 1,
            "text_content": "Just Title",
            "course": str(course.id)
        }
        response = api_client.post(
            self.create_module_url, module_data, format="json")
        assert response.status_code == 400


class TestUpdateModule:

    @pytest.mark.parametrize(
        'user_role',
        [["SUPER_ADMIN"], ["SCHOOL_ADMIN"]]
    )
    def test_admin_updated_module(self, user_role,module_factory,course_factory, api_client, authenticate_user):
        course = course_factory()
        module = module_factory(course=course)
        user = authenticate_user(roles=user_role)
        token = user['token']
        api_client_with_credentials(token, api_client)
        module_data = {
            "module_name": "Updated MAT 101",
            "text_content": "Updated Just Title",
        }
        url = reverse("modules:module-detail",  kwargs={"pk": module.id})
        response = api_client.patch(url, module_data, format="json")
        returned_json = response.json()
        assert response.status_tcode == 200
        assert returned_json['module_name'] == 'Updated MAT 101'
        assert returned_json['text_content'] == 'Updated Just Title'
    
    def test_course_teacher_update_module(self, module_factory,course_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["TEACHER"])
        course = course_factory(teachers=[user['user_instance']])
        module = module_factory(course=course, module_order=1)
        
        token = user['token']
        api_client_with_credentials(token, api_client)
        module_data = {
            "module_name": "Updated MAT 101",
            "text_content": "Updated Just Title",
            "module_order":25
        }   
        url = reverse("modules:module-detail",  kwargs={"pk": module.id})
        response = api_client.patch(url, module_data, format="json")
        returned_json = response.json()
        
        assert response.status_code == 200
        assert returned_json['module_name'] == 'Updated MAT 101'
        assert returned_json['text_content'] == 'Updated Just Title'
        assert returned_json['module_order'] == 25
    
    
    def test_deny_update_module(self, module_factory,course_factory, api_client, authenticate_user):
        """A teacher can only update a course he teaches"""
        user = authenticate_user(roles=["TEACHER"])
        course = course_factory()
        module = module_factory(course=course, module_order=1) 
        token = user['token']
        api_client_with_credentials(token, api_client)
        module_data = {
            "module_name": "Updated MAT 101",
            "text_content": "Updated Just Title",
            "module_order":25
        }   
        url = reverse("modules:module-detail",  kwargs={"pk": module.id})
        response = api_client.patch(url, module_data, format="json")
        assert response.status_code == 400
    
    def test_bulk_update_module_read_status(self, user_factory,module_factory,course_factory, api_client, authenticate_user):
        user = authenticate_user(roles=["STUDENT"])
        course = course_factory()
        module = module_factory(course=course)
        token = user['token']
        api_client_with_credentials(token, api_client)
        data = {
            "is_completed": True,
            "modules": [str(module.id)],    
        }
        url = reverse("modules:module-bulk-update-complete-status")
        response = api_client.put(url, data, format="json")
        assert response.status_code == 200
        assert Module.objects.get(completed_by = user['user_instance'])
    
    
#TODO: Submit Module Assignment Test      
#TODO: Module Assignment Test  
#TODO: Quiz Test  