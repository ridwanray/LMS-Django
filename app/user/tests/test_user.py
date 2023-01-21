import pytest
from django.urls import reverse
from rest_framework import status
from user.models import Token, User
from user.enums import TokenTypeClass
from .conftest import api_client_with_credentials

pytestmark = pytest.mark.django_db

class TestUserRegistration:
    user_register_url = reverse("user:user-list")
    reinvite_user_url = reverse("user:user-reinvite-user")
    
    @pytest.mark.parametrize(
        'user_roles',
        [["STUDENT"],["TEACHER"],["STUDENT", "TEACHER"]]
    )
    def test_user_register(self,user_roles,api_client, mocker):
        mock_send_account_verification_email = mocker.patch(
            'user.tasks.send_user_creation_email.delay')
        data = {
            "email":"ray@gmail.com",
            "password":"mypass",
            "firstname":"First",
            "lastname":"Last",
            "roles":user_roles
        }
        response = api_client.post(self.user_register_url, data, format="json")
        returned_json =  response.json()
        assert response.status_code == status.HTTP_201_CREATED
        assert data.get('email') == returned_json.get('email')
        assert data.get('roles') == returned_json.get('roles')
        assert User.objects.count() == 1

        verification_token = Token.objects.get(user__email=data["email"],  token_type=TokenTypeClass.ACCOUNT_VERIFICATION)
        
        email_data = {  
            'fullname': f'{data["firstname"]}',
            'email': data.get('email'),
            'token': verification_token.token,
        }
        mock_send_account_verification_email.assert_called_once_with(email_data)
        
    
    @pytest.mark.parametrize(
        'invalid_roles',
        [["STUDENT","SUPER_ADMIN"],["TEACHER","SCHOOL_ADMIN"],["AGENT", "TEACHER"]]
    )
    def test_deny_user_creation_for_invalid_roles(self, invalid_roles, api_client):
        data = {
            "email":"ray@gmail.com",
            "password":"mypass",
            "firstname":"First",
            "lastname":"Last",
            "roles": invalid_roles
        }
        response = api_client.post(self.user_register_url, data, format="json")
        assert response.status_code == 400
    
    def test_deny_user_creation_duplicate_mail(self, active_user, api_client):
        data = {
            "email":active_user.email,
            "password":"mypass",
            "firstname":"First",
            "lastname":"Last",
            "roles":["STUDENT"]
        }
        response = api_client.post(self.user_register_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_reinvite_unverified_user(self, api_client, user_factory, mocker):
        mock_send_account_verification_email = mocker.patch(
            'user.tasks.send_user_creation_email.delay')
        unverified_user: User = user_factory.create(verified= False)
        data = {"email":unverified_user.email}
        response =  api_client.post(self.reinvite_user_url, data)
        assert response.status_code == 200
    
        verification_token =  verification_token = Token.objects.get(user=unverified_user,  token_type=TokenTypeClass.ACCOUNT_VERIFICATION)
        email_data = {  
            'fullname': unverified_user.firstname,
            'email': unverified_user.email,
            'token': verification_token.token,
        }
        
        mock_send_account_verification_email.assert_called_once_with(email_data)
    
    def test_deny_reinvite_to_unexist_user(self, api_client):
        data = {"email":"randomemail@gmail.com"}
        response =  api_client.post(self.reinvite_user_url, data)
        assert response.status_code == 404
    
    def test_deny_reinvite_to_verified_user(self, api_client, active_user):
        data = {"email":active_user.email}
        response =  api_client.post(self.reinvite_user_url, data)
        assert response.status_code == 400

class TestRetriveUsers:
    user_list_url = reverse("user:user-list")
    @pytest.mark.parametrize(
        'user_role',
        [["SCHOOL_ADMIN"],["SUPER_ADMIN"],["SCHOOL_ADMIN", "SUPER_ADMIN"]]
    )
    def test_admin_retrieve_users(self, user_role, api_client, user_factory, authenticate_user):
        """Admin retrieves all users on the platform"""
        user_factory.create_batch(3)
        user = authenticate_user(roles=user_role)
        token = user['token']
        api_client_with_credentials(token, api_client)
        response = api_client.get(self.user_list_url)
        assert response.status_code == 200
        assert response.json()['total'] == 4
    
    @pytest.mark.parametrize(
        'user_role',
        [["TEACHER"],["STUDENT"]]
    )
    def test_non_admin_retrieves_user(self, api_client, user_role, user_factory, authenticate_user):
        """Non Admin(i.e. Student/Teacher retrieves only their data)"""
        user_factory.create_batch(3)
        user = authenticate_user(roles = user_role)
        token = user['token']
        api_client_with_credentials(token, api_client)
        response = api_client.get(self.user_list_url)
        assert response.status_code == 200
        assert response.json()['total'] == 1
        
    def test_retrieve_user_details(self, api_client, user_factory, authenticate_user):
        user = user_factory()
        auth_user = authenticate_user(roles = ["SUPER_ADMIN"])
        url = reverse("user:user-detail", kwargs={"pk": user.id})
        api_client_with_credentials(auth_user["token"], api_client)
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()['email'] == user.email
    
    @pytest.mark.parametrize(
        'user_role',
        [["TEACHER"],["STUDENT"]]
    ) 
    def test_deny_retrieve_someone_else_details(self, user_role,api_client, user_factory, authenticate_user):
        """Teacher/Student can only retrieve ther data"""
        user = user_factory()
        auth_user = authenticate_user(roles = user_role)
        url = reverse("user:user-detail", kwargs={"pk": user.id})
        api_client_with_credentials(auth_user["token"], api_client)
        response = api_client.get(url)
        assert response.status_code == 400
    
    def test_deny_user_retrieval_to_unauth_user(self, api_client):
        response = api_client.get(self.user_list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateDeleteUsers:
    def test_admin_update_user_details(self,api_client, user_factory, authenticate_user):
        user = user_factory(firstname="Namer")
        auth_user = authenticate_user(roles = ["SUPER_ADMIN"])
        url = reverse("user:user-detail", kwargs={"pk": user.id})
        api_client_with_credentials(auth_user["token"], api_client)
        data= {"roles":["SCHOOL_ADMIN","STUDENT"],"firstname":"New name"}
        response = api_client.patch(url, data)
        assert response.status_code == 200
        response_data = response.json()
        assert data['roles'] == response_data['roles']
        assert data['firstname'] == response_data['firstname']
    
    @pytest.mark.parametrize(
        'user_role',
        [["TEACHER"],["STUDENT"]]
    ) 
    def test_non_admin_cannot_assign_admin_permission(self,api_client,user_role, authenticate_user):
        auth_user = authenticate_user(roles = user_role)
        url = reverse("user:user-detail", kwargs={"pk": auth_user['user_instance'].id})
        api_client_with_credentials(auth_user["token"], api_client)
        data= {"roles":["SCHOOL_ADMIN","SUPER_ADMIN"]}
        response = api_client.patch(url, data)
        print(response.json())
        assert response.status_code == 400
    
    @pytest.mark.parametrize(
        'user_role',
        [["TEACHER"],["STUDENT"]]
    )     
    def test_non_admin_update_personal_info(self,api_client,user_role, authenticate_user):
        auth_user = authenticate_user(roles = user_role)
        url = reverse("user:user-detail", kwargs={"pk": auth_user['user_instance'].id})
        api_client_with_credentials(auth_user["token"], api_client)
        data= {"roles":["TEACHER"], "firstname":"New"}
        response = api_client.patch(url, data)
        assert response.status_code == 200
        assert response.json()['firstname'] =="New"
    
    def test_superadmin_delete_user_account(self,api_client,user_factory, authenticate_user):
        user = user_factory()
        auth_user = authenticate_user(roles = ["SUPER_ADMIN"])
        url = reverse("user:user-detail", kwargs={"pk": user.id})
        api_client_with_credentials(auth_user["token"], api_client)
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    @pytest.mark.parametrize(
        'user_role',
        [["TEACHER"],["STUDENT"]]
    )   
    def test_deny_delete_user_account(self,api_client,user_role,user_factory, authenticate_user):
        """Only super admin can delete a user on the system;"""
        auth_user = authenticate_user(roles = user_role)
        url = reverse("user:user-detail", kwargs={"pk": auth_user['user_instance'].id})
        api_client_with_credentials(auth_user["token"], api_client)
        response = api_client.delete(url)
        print(response.json())
        assert response.status_code == status.HTTP_403_FORBIDDEN