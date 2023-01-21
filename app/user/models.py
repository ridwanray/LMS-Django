import uuid
from datetime import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser
from datetime import datetime, timezone
from django.contrib.auth.models import PermissionsMixin
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from .enums import USER_ROLE, TOKEN_TYPE
from .managers import CustomUserManager
from django.utils.crypto import get_random_string


def default_role()-> list[str]:
    return ["STUDENT"]

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        _("email address"), null=True, blank=True, unique=True)
    password = models.CharField(max_length=255, null=True)
    firstname = models.CharField(max_length=255, blank=True, null=True)
    lastname = models.CharField(max_length=255, blank=True, null=True)
    image = models.FileField(upload_to="users/", blank=True, null=True)
    phone = models.CharField(max_length=17, blank=True, null=True)
    roles = ArrayField(
        models.CharField(max_length=20, blank=True, choices=USER_ROLE),
        default=default_role,
        size=4,
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified = models.BooleanField(default=False)
    failed_password_attempts = models.IntegerField(default=0)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        if self.firstname and self.lastname:
            return f"{self.firstname} {self.lastname}"
        else:
            return self.email

    def save_last_login(self):
        self.last_login = datetime.now()
        self.save()

class Token(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    token = models.CharField(max_length=255, null=True)
    token_type = models.CharField(max_length=100, choices=TOKEN_TYPE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{str(self.user)} {self.token}"

    def is_valid(self)->bool:
        lifespan_in_seconds = float(settings.TOKEN_LIFESPAN * 60 * 60)
        now = datetime.now(timezone.utc)
        time_diff = now - self.created_at
        time_diff = time_diff.total_seconds()
        if time_diff >= lifespan_in_seconds:
            return False
        return True

    def verify_user(self)-> None:
        self.user.verified = True
        self.user.is_active = True
        self.user.save()

    def generate(self) -> None:
        if not self.token:
            self.token = get_random_string(120)
            self.save()

    def reset_user_password(self, password:str) -> None:
        self.user.set_password(password)
        self.user.save()
