"""
Permission classes for role-based access control.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permission for admin users only."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin()


class IsTeacher(permissions.BasePermission):
    """Permission for teachers."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_teacher() or request.user.is_admin()
        )


class IsStudent(permissions.BasePermission):
    """Permission for students."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_student()


class IsAdminOrTeacher(permissions.BasePermission):
    """Permission for admin or teacher."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin() or request.user.is_teacher()
        )
