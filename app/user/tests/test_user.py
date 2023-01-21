import pytest
from django.urls import reverse
from rest_framework import status
from user.models import Token, User
from user.enums import TokenTypeClass


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
        