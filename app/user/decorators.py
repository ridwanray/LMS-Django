from django.db.models import Q
from rest_framework import serializers

#TODO : Add make app multitenancy
#TODO : Add school schemas
#TODO : from school.models import School

def is_school_active(func):
    """
    Checks if a school is active.
    """

    def wrapper(request, *args, **kwargs):
        if request.user.school.status == "ACTIVE":
            return func(request, *args, **kwargs)
        else:
            return serializers.ValidationError(
                {"error": f"School is not active."}
            )

    return wrapper


@is_school_active
def is_school_user(func):
    """
    Checks if a user belongs to the school
    """

    def wrapper(request, *args, **kwargs):
        # Check if the user is part of the school.
        if (
            request.user.school
            and School.objects.filter(admin=request.user).exists()
        ):
            return func(request, *args, **kwargs)
        else:
            return serializers.ValidationError(
                {"error": f"User has no record in {request.user.school}."}
            )

    return wrapper


