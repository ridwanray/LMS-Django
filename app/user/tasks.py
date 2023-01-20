from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import get_template
from .utils import send_email
from core.celery import APP

@APP.task()
def send_password_reset_email(email_data):
    html_template = get_template("emails/password_reset_template.html")
    html_alternative = html_template.render(email_data)
    send_email(
        "Password Reset", email_data["email"], html_alternative
    )

@APP.task()
def send_user_creation_email(email_data):
    html_template = get_template("emails/account_verification_template.html")
    html_alternative = html_template.render(email_data)
    send_email(
        "Email Confirmation", email_data["email"], html_alternative
    )

