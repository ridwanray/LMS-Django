from typing import Dict,BinaryIO
from django.template.loader import get_template
from user.utils import send_email
from .utils import generate_certificate
from core.celery import APP

@APP.task()
def process_user_course_certificate(cert_info: Dict):
    cert_file: BinaryIO =  generate_certificate(**cert_info)
    html_template = get_template("emails/send_cerficate_template.html")
    html_alternative = html_template.render(cert_info)
    mail_attachment={'name':'Course-Certifate','file':cert_file,'type':'image/png'}
    send_email(
        "Your Course Certificate", cert_info["email"], html_alternative, attachment=mail_attachment
    )

