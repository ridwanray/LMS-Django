import factory
from faker import Faker
from django.contrib.auth.models import User
from user.models import User, Token

fake = Faker()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        
    email = factory.Sequence(lambda n: 'person{}@example.com'.format(n))
    password = factory.PostGenerationMethodCall('set_password','my@pass@access')
    verified='True'
    firstname = fake.name()
    lastname = fake.name()
    
       
class SuperAdminUserFactory(UserFactory):
    """"Factory for a super admin user"""
    verified = 'True'
    is_superuser = 'True'

class TokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Token
    token = fake.md5()