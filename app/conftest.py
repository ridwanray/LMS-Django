from typing import List
import pytest
from user.models import User
from rest_framework.test import APIClient
from django.urls import reverse
from pytest_factoryboy import register
from user.tests.factories import (
    UserFactory, TokenFactory
)

register(UserFactory)
register(TokenFactory)

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def active_user(db, user_factory):
    return user_factory.create(is_active=True)

@pytest.fixture
def inactive_user(db, user_factory):
    user = user_factory.create(is_active=False)
    return user

@pytest.fixture
def authenticate_user(api_client, active_user):
    """Return token needed for authentication"""
    def _user(roles:List[str], verified=True, is_active = True):
        active_user.verified = verified
        active_user.is_active = is_active
        active_user.roles = roles
        active_user.save(update_fields=["roles","verified","is_active"])
        active_user.refresh_from_db()
        url = reverse("auth:login")
        data = {
           "email": active_user.email,
           "password": "my@pass@access",
        }
        response = api_client.post(url, data)
        token = response.json()["access"]
        return {
             "token": token,
             "user_email": active_user.email,
             "user_instance": active_user,
        }
         
    return _user

# @pytest.fixture
# def authenticate_user(api_client, active_user):
#     """Return token needed for authentication"""
#     url = reverse("auth:login")
#     data = {
#         "email": active_user.email,
#         "password": "my@pass@access",
#     }
#     response = api_client.post(url, data)
#     token = response.json()["access"]
#     return {
#         "token": token,
#         "user_email": active_user.email,
#         "user_instance": active_user,
#     }

#[*] Fixtures for users with specific permissions/roles
@pytest.fixture
def mock_auth_user_with_specific_role(mocker):
    '''Mock authentication&return user with specific role/permission'''
    def _user(role_list:List[str], is_admin=False):
        mock_auth = mocker.patch('authentication.get_auth_user')
        mocked_user_data = {
        "id":  '',
        "username": "tehamod306",
        "email": "tehamod306@dnitem.com",
        "firstname": "Ray",
        "lastname": "Inc",
        "is_admin": is_admin,
        "roles": role_list,
        }
        mock_auth.return_value = mocked_user_data
        return mocked_user_data
    return _user