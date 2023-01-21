import pytest
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
    return user_factory.create()

@pytest.fixture
def inactive_user(db, user_factory):
    user = user_factory.create(is_active=False)
    return user

@pytest.fixture
def authenticate_user(api_client, active_user):
    """Return token needed for authentication"""
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


@pytest.fixture
def authenticate_super_user(api_client, active_user):
    active_user.is_superuser = True
    active_user.save()
    """Return token needed for authentication"""
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
        
