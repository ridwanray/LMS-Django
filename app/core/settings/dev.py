from .base import *
from decouple import config

ALLOWED_HOSTS = ['*']

# EMAIL CONFIG
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

PASSWORD_RESET_TIMEOUT_DAYS = 1

LOGGING = {}