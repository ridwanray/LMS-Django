import factory
from faker import Faker
from certificate.models import Certificate

fake = Faker()


class CertificateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Certificate

    grade = fake.name()
    certificate_id = fake.random_int(1000, 99999)


