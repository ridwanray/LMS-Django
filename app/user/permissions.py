from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """Allows access only to super admin users."""
    message = "Only Super Admins are authorized to perform this action."
    
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated and "SUPER_ADMIN" in request.user.roles
        )

class IsStudent(permissions.BasePermission):
    """Allows access only to students."""
    message = "Only Students are authorized to perform this action."

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and "STUDENT" in request.user.roles)

class IsTeacher(permissions.BasePermission):
    """Allows access only to teachers"""
    message = "Only teachers are authorized to perform this action."
    
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and "TEACHER" in request.user.roles)


class IsSchoolAdmin(permissions.BasePermission):
    """Allows access only to teachers"""
    message = "Only teachers are authorized to perform this action."
    
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and "SCHOOL_ADMIN" in request.user.roles)
