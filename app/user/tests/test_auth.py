import pytest
from django.urls import reverse
from rest_framework import status
from user.models import Token
from user.enums import TokenTypeClass
from .conftest import api_client_with_credentials
from datetime import datetime, timedelta
import time_machine

pytestmark = pytest.mark.django_db


class TestAuthEndpoints:
    initiate_password_reset_url = reverse(
        'auth:auth-initiate-password-reset')
    password_change_url = reverse('auth:password-change-list')
    
    login_url = reverse("auth:login")
    verify_account_url = reverse("auth:auth-verify-account")
    
    def test_user_login(self,api_client,active_user):
        data = {
            "email": active_user.email,
            "password": "my@pass@access"}
        response = api_client.post(self.login_url, data)
        assert response.status_code == status.HTTP_200_OK
        returned_json = response.json()
        assert 'refresh'  in returned_json
        assert 'access'  in returned_json
        
    def test_deny_login_to_inactive_user(self,api_client, inactive_user):
        data = {
            "email":inactive_user.email,
            "password": "my@pass@access"}
        response = api_client.post(self.login_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_deny_login_invalid_credentials(self,api_client,active_user):
        data = {
            "email":active_user.email,
            "password": "wrong@pass"}
        response = api_client.post(self.login_url, data)
        print(response.json())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_password_reset_initiate(self, mocker, api_client, active_user):
        """Initiate a password reset for not authenticated user"""
        mock_send_temporary_password_email = mocker.patch(
            'user.tasks.send_password_reset_email.delay')
        data = {
            'email': active_user.email,
            'token': '123456'
        }
        response = api_client.post(
            self.initiate_password_reset_url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        mock_send_temporary_password_email.side_effect = print(
            "Sent to celery task:Password Reset Mail!")
        
        token: Token = Token.objects.get(user=active_user,  token_type=TokenTypeClass.PASSWORD_RESET)
        email_token =  token.token         
        email_data = {
            'fullname': active_user.firstname,
            'email': active_user.email,
            'token': email_token
        }
        mock_send_temporary_password_email.assert_called_once_with(email_data)

    def test_deny_initiate_password_reset_to_inactive_user(self, api_client, inactive_user):
        data = {
            'email': inactive_user.email,
        }
        response = api_client.post(
            self.initiate_password_reset_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_using_valid_old_password(self, api_client, authenticate_user):
        token = authenticate_user['token']
        user_instance = authenticate_user['user_instance']
        data = {
            'old_password': 'my@pass@access',
            'new_password': 'newpass@@',
        }
        api_client_with_credentials(token, api_client)
        response = api_client.post(
            self.password_change_url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        user_instance.refresh_from_db()
        assert user_instance.check_password('newpass@@')

    def test_deny_change_password_using_invalid_old_password(self, api_client, authenticate_user):
        token = authenticate_user['token']
        data = {
            'old_password': 'invalidpass',
            'new_password': 'New87ge&nerated',
        }
        api_client_with_credentials(token, api_client)
        response = api_client.post(
            self.password_change_url, data, format="json")
        print(response.json())
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deny_change_password_for_unathenticated_user(self, api_client):
        """Only Authenticated User can change password using old valid password"""
        data = {
            'old_password': 'invalidpass',
            'new_password': 'New87ge&nerated',
        }
        response = api_client.post(
            self.password_change_url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_verify_account_using_verification_token(self, api_client,user_factory, token_factory):
        unverified_user = user_factory(verified = False, is_active = False)
        verification_token: Token  = token_factory(user = unverified_user, token_type=TokenTypeClass.ACCOUNT_VERIFICATION)
        request_payload = {'token':verification_token.token}
        response = api_client.post(self.verify_account_url, request_payload)
        assert response.status_code == 200
        unverified_user.refresh_from_db()
        assert unverified_user.verified == True
        assert unverified_user.is_active == True
    
    def test_deny_verify_using_invalid_token(self, api_client,user_factory):
        unverified_user = user_factory(verified = False, is_active = False)
        token = "sampletoken" 
        request_payload = {'token':token}
        response = api_client.post(self.verify_account_url, request_payload)
        assert response.status_code == 400
        unverified_user.refresh_from_db()
        assert unverified_user.verified == False
        assert unverified_user.is_active == False
    
    def test_create_password_using_valid_reset_token():
        pass
    
    



class TestAuthSessionSecurity:
    verity_token_url = reverse('auth:verify-token')

    @time_machine.travel(datetime.now() + timedelta(hours=22))
    def test_token_session_not_expires(self, api_client, authenticate_user):
        token = authenticate_user['token']
        response = api_client.post(self.verity_token_url, {
                                   'token': token}, format='json')
        assert response.status_code == status.HTTP_200_OK

    @time_machine.travel(datetime.now() + timedelta(hours=25))
    def test_token_session_expires(self, api_client, authenticate_user):
        """Token expires after TOKEN_LIFESPAN in config:24 hours"""
        token = authenticate_user['token']
        response = api_client.post(self.verity_token_url, {
                                   'token': token}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_account_locked_after_max_login_attempt(self, api_client, active_user):
        url = reverse('auth:login')
        assert active_user.is_active
        data = {
            'email': active_user.email,
            'password': 'wrongpass'
        }

        for _ in range(0, 6):
            api_client.post(url, data, format='json')
        active_user.refresh_from_db()
        assert active_user.is_active == False

        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
