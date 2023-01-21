from typing import Dict, Any
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.crypto import get_random_string
from .models import Token, User


def send_email(subject:str, email_from: str, html_alternative: Any, attachment: Dict = None):
    msg = EmailMultiAlternatives(
        subject, settings.EMAIL_FROM, [email_from]
    )
    if attachment is not None:
        msg.attach(
            attachment.get('name'), attachment.get(
                'file'), attachment.get('type')
        )
    msg.attach_alternative(html_alternative, "text/html")
    msg.send(fail_silently=False)


def create_token_and_send_user_email(user: User, token_type: str)->None:
    from .tasks import send_user_creation_email
    token, _ = Token.objects.update_or_create(
        defaults={
            "user": user,
            "token_type": token_type,
            "token": get_random_string(120),
        },
    )
    user_data = {
        "email": user.email,
        "fullname": f"{user.firstname}",
        "token": token.token
    }
    send_user_creation_email.delay(user_data)
