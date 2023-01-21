from django.contrib.auth import get_user_model, authenticate
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers, exceptions
from .models import  User
from django.conf import settings


class CustomObtainTokenPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        options = {"hours": settings.TOKEN_LIFESPAN}
        refresh = self.get_token(self.user)
        access_token = refresh.access_token
        access_token.set_exp(lifetime=timedelta(**options))
        self.user.save_last_login()
        data['refresh'] = str(refresh)
        data['access'] = str(access_token)
        return data

    @classmethod
    def get_token(cls, user):
        if not user.verified:
            raise exceptions.AuthenticationFailed(_('Account not verified.'), code='authentication')
        token = super().get_token(user)
        token.id = user.id
        token['firstname'] = user.firstname
        token['lastname'] = user.lastname
        token["email"] = user.email
        token["roles"] = user.roles
        if user.image:
            token["image"] = user.image.url
        return token


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for user authentication object"""

    email = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"}, trim_whitespace=False)

    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get("email")
        password = attrs.get("password")
        if email:
            user = authenticate(request=self.context.get("request"), username=email.lower().strip(), password=password)

        if not user:
            msg = _("Unable to authenticate with provided credentials")
            raise serializers.ValidationError(msg, code="authentication")
        attrs["user"] = user
        return attrs
    

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128, required=False)
    new_password = serializers.CharField(max_length=128, min_length=5)

    def validate_old_password(self, value):
        request = self.context["request"]

        if not request.user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self):
        user: User = self.context["request"].user
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save(update_fields=["password"])

class CreatePasswordFromTokenSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class TokenDecodeSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class ListUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "firstname",
            "lastname",
            "email",
            "roles",
            "image",
            "verified",
            "last_login",
            "created_at",
        ]
        
class BasicUserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "firstname",
            "lastname",
            "email",
        ]

class CreateUserSerializer(serializers.ModelSerializer):
    """Serializer for creating user object"""

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "password",
            "firstname",
            "lastname",
            "verified",
            "phone",
            "image",
            "roles",
        )
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 5},
            "last_login": {"read_only": True},
            "verified":{"read_only": True},
            "firstname": {"required": True},
            "lastname": {"required": True},
            "roles":{"required": True},
        }

    def validate_roles(self, roles : list) -> None:
        allowable_roles : list[str]= ["STUDENT", "TEACHER"]
        valid : bool = all(role in allowable_roles for role in roles)
        if not valid:
            raise serializers.ValidationError("Roles can only be STUDENT or TEACHER")
        return roles
    
    def validate(self, attrs):
        email = attrs.get("email", None)
        if email:
            email = attrs["email"].lower().strip()
            if get_user_model().objects.filter(email=email).exists():
                raise serializers.ValidationError("Email already exists")
        return super().validate(attrs)

    def create(self, validated_data):
        #print("first validated", validated_data)
        validated_data["password"] = make_password(validated_data["password"])
        #print("validated", validated_data)
        user = User.objects.create_app_user(**validated_data)
        return user 

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if validated_data.get("password", False):
            instance.set_password(validated_data.get("password"))
            instance.save()
        return instance
