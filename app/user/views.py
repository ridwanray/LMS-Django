from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.settings import api_settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from user.models import User,Token
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.views import ObtainAuthToken
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets, status,  serializers
from django_filters.rest_framework import DjangoFilterBackend
from .tasks import send_password_reset_email
from .serializers import (
    CustomObtainTokenPairSerializer, EmailSerializer,CreatePasswordFromTokenSerializer,
    PasswordChangeSerializer,AuthTokenSerializer,ListUserSerializer,CreateUserSerializer, TokenDecodeSerializer)
from .permissions import IsStudent, IsSuperAdmin, IsTeacher
from .utils import create_token_and_send_user_email
from .enums import TokenTypeClass

class CustomObtainTokenPairView(TokenObtainPairView):
    """Authentice with email and password"""

    serializer_class = CustomObtainTokenPairSerializer
    

class AuthViewsets(viewsets.GenericViewSet):
    """Auth viewsets"""

    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        permission_classes = self.permission_classes
        if self.action in ["initiate_password_reset", "create_password","verify_account"]:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(
        methods=["POST"],
        detail=False,
        serializer_class=EmailSerializer,
        url_path="initiate-password-reset",
    )
    def initiate_password_reset(self, request, pk=None):
        """Send temporary password to user email"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data["email"].lower().strip()
        user = get_user_model().objects.filter(email=email, is_active=True).first()
        if not user:
            return Response({"success": False,"message": "User not found or deactivated"},status=400)        
        
        token, _ = Token.objects.update_or_create(
                    user=user,
                    defaults={
                        "user": user,
                        "token_type": TokenTypeClass.PASSWORD_RESET,
                        "token": get_random_string(20)
                        }
                )
        email_data = {
                    "fullname": user.firstname,
                    "email": user.email,
                    "token": f"{token.token}",
                }
        send_password_reset_email.delay(email_data)
        
        return Response({"success": True,
                         "message": "Temporary password sent to your email!"},status=200)

    @action(methods=['POST'], detail=False, serializer_class=CreatePasswordFromTokenSerializer, url_path='create-password')
    def create_password(self, request, pk=None):
        """Create a new password given the reset token"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token: Token = Token.objects.filter(token=request.data['token'],  token_type=TokenTypeClass.PASSWORD_RESET).first()
        if not token or not token.is_valid():
            return Response({'success': False, 'errors': 'Invalid token specified'}, status=400)
        token.reset_user_password(request.data['new_password'])
        token.delete()
        return Response({'success': True, 'message': 'Password successfully reset'}, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: inline_serializer(
                name='AccountVerificationStatus',
                fields={
                    "success": serializers.BooleanField(default=True),
                    "message": serializers.CharField(default="Acount Verification Successful")
                }
            ),
        },
    )
    @action(
        methods=["POST"],
        detail=False,
        serializer_class=TokenDecodeSerializer,
        url_path="verify-account",
    )
    def verify_account(self, request, pk=None):
        """Activate a user acount using the token send to the user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token: Token = Token.objects.filter(token=request.data['token'],  token_type=TokenTypeClass.ACCOUNT_VERIFICATION).first()
        if not token or not token.is_valid():
            return Response({'success': False, 'errors': 'Invalid token specified'}, status=400)
        token.verify_user()
        token.delete()
        return Response({"success": True, "message": "Acount Verification Successful"},status=200)
   
   
class PasswordChangeView(viewsets.GenericViewSet):
    '''Allows password change to authenticated user.'''
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        context = {"request": request}
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Your password has been updated."}, status.HTTP_200_OK)


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user"""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        try:
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {"token": token.key, "created": created, "roles": user.roles},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"message": str(e)}, 500)



class UserViewsets(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = ListUserSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active"]
    search_fields = ["email", "firstname", "lastname", "phone"]
    ordering_fields = [
        "created_at",
        "last_login",
        "email",
        "firstname",
        "lastname",
        "phone",
    ]

    def get_queryset(self):
        user_role = self.request.user.roles
        if "SUPER_ADMIN" in user_role:
            return self.queryset.all()
        elif "TEACHER" in user_role:
            return self.queryset.filter(roles__in = ["STUDENT"])
        elif "STUDENT" in user_role:
            return self.queryset.filter(user = self.request.user)
        return get_user_model().objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        permission_classes = self.permission_classes
        if self.action in ["create","reinvite_user"]:
            permission_classes = [AllowAny]
        elif self.action in ["destroy", "partial_update","update"]:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def _reinvite_check(self, request):
        email: str  = request.data["email"].lower().strip()
        user: User = get_object_or_404(User, email=email)
        if user.verified:
            return None
        else: 
            return user

    @action(
        methods=["POST"],
        detail=False,
        serializer_class=EmailSerializer,
        url_path="reinvite-user",
    )
    def reinvite_user(self, request, *args,**kwargs):
        '''Resend verification email to a user'''
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self._reinvite_check(request)
        if not user:
           return Response({"success": False, "message": "User already verified"},status.HTTP_400_BAD_REQUEST)
        create_token_and_send_user_email(user =user, token_type=TokenTypeClass.ACCOUNT_VERIFICATION )
        return Response({"success":True, "message":"Verification mail sent successfully."},status.HTTP_200_OK)
