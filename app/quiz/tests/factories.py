import factory
from faker import Faker
from django.contrib.auth.models import User
from quiz.models import (Quiz, Question, Answer, TakenQuiz,)

fake = Faker()


class QuizFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quiz

    quiz_name = fake.name()


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question

    prompt_question = fake.name()
    

class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Answer

    text = fake.name()


class TakenQuizFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TakenQuiz


