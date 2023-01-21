from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from rest_framework import exceptions
from decouple import config


class CustomBackend(ModelBackend):
    '''Lock user account after max login attempts'''
    def authenticate(self, request, **kwargs):
        UserModel = get_user_model()
        try:
            username = kwargs.get(UserModel.USERNAME_FIELD, None)
            password = kwargs.get("password", None)
            if username is None or password is None:
                return None
            if user := UserModel.objects.filter(Q(email__iexact=username)).first():
                if user.failed_password_attempts > config('MAX_LOGIN_ATTEMPTS', cast=int):
                    raise exceptions.ValidationError(
                                {"email": "Account locked - Maximum number of login attempts reached."}
                        )
                if user.failed_password_attempts == config('MAX_LOGIN_ATTEMPTS', cast=int):
                    user.is_active = False
                if user.is_active and user.check_password(password):
                    user.failed_password_attempts = 0
                    user.save()
                    return user
                user.failed_password_attempts += 1
                user.save()
            return None
        except UserModel.DoesNotExist:
            return None
