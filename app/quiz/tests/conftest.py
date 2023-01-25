from pytest_factoryboy import register
from .factories import ( QuizFactory,QuestionFactory)

register(QuizFactory)
register(QuestionFactory)
