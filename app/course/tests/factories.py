import factory
from faker import Faker
from django.contrib.auth.models import User
from course.models import (Course,EnrollStudent,Module, 
                           Transaction,ModuleAssignmentSubmission)

fake = Faker()

class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course
         
    course_name = fake.name()
    course_price = fake.random_int(10, 90)
    display_title = fake.name()
    approved = 'True'
    
    @factory.post_generation
    def teachers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for each in extracted:
                self.teachers.add(each)
    
class EnrollStudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EnrollStudent
        

class ModuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Module
    module_name = fake.name()
    video_link =  fake.url()
    text_content =  fake.text()
    topic = fake.name()
    module_order = factory.Sequence(lambda n: n)


class ModuleAssignmentSubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ModuleAssignmentSubmission


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction