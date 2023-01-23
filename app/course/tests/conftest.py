from pytest_factoryboy import register
from .factories import (
    CourseFactory, ModuleFactory
)

register(CourseFactory)
register(ModuleFactory)
