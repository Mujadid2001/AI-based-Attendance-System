"""
Base ViewSet classes and mixins to reduce code duplication and enforce consistent patterns.
"""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.db.models import QuerySet
from typing import Any, Dict, Optional
import logging

from utils.responses import APIResponse, ResponseMixin, handle_exceptions
from apps.authentication.permissions import IsAdmin, IsAdminOrTeacher, IsStudent

logger = logging.getLogger(__name__)


class RoleBasedQuerysetMixin:
    """
    Mixin to provide role-based queryset filtering.
    """
    
    def get_queryset_for_admin(self) -> QuerySet:
        """Get queryset for admin users - should return all objects."""
        return self.queryset or self.get_queryset()
    
    def get_queryset_for_teacher(self) -> QuerySet:
        """Get queryset for teacher users - override in subclasses."""
        return self.get_queryset_for_admin()
    
    def get_queryset_for_student(self) -> QuerySet:
        """Get queryset for student users - override in subclasses."""
        return self.get_queryset_for_admin()
    
    def get_queryset(self) -> QuerySet:
        """
        Filter queryset based on user role.
        Override the role-specific methods in subclasses.
        """
        if not hasattr(self.request, 'user') or not self.request.user.is_authenticated:
            return self.queryset.none() if self.queryset else self.model.objects.none()
        
        user = self.request.user
        
        if user.is_admin():
            return self.get_queryset_for_admin()
        elif user.is_teacher():
            return self.get_queryset_for_teacher()
        elif user.is_student():
            return self.get_queryset_for_student()
        else:
            # Default to empty queryset for unknown roles
            return self.queryset.none() if self.queryset else self.model.objects.none()


class ClientIPMixin:
    """
    Mixin to extract client IP address.
    """
    
    def get_client_ip(self, request) -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return (
            x_forwarded_for.split(',')[0].strip()
            if x_forwarded_for
            else request.META.get('REMOTE_ADDR', 'unknown')
        )


class AuditMixin:
    """
    Mixin to automatically set audit fields on create/update.
    """
    
    def perform_create(self, serializer):
        """Set created_by field on creation."""
        if hasattr(serializer.instance, 'created_by') and self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        """Set updated_by field on update."""
        if hasattr(serializer.instance, 'updated_by') and self.request.user.is_authenticated:
            serializer.save(updated_by=self.request.user)
        else:
            serializer.save()


class BaseViewSet(
    ResponseMixin,
    RoleBasedQuerysetMixin,
    ClientIPMixin,
    AuditMixin,
    viewsets.ViewSet
):
    """
    Base ViewSet with common functionality for all custom ViewSets.
    """
    permission_classes = [IsAuthenticated]
    
    @handle_exceptions
    def handle_request_with_exceptions(self, request, *args, **kwargs):
        """
        Template method for handling requests with automatic exception handling.
        Override this in subclasses instead of action methods for automatic error handling.
        """
        raise NotImplementedError("Subclasses must implement handle_request_with_exceptions")


class BaseModelViewSet(
    ResponseMixin,
    RoleBasedQuerysetMixin,
    ClientIPMixin,
    AuditMixin,
    viewsets.ModelViewSet
):
    """
    Base ModelViewSet with common functionality for CRUD operations.
    """
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Create with standardized response."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return self.success_response(
                data=serializer.data,
                message=_('Created successfully.'),
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating {self.__class__.__name__}: {str(e)}")
            return self.error_response(
                message=_('Failed to create resource.'),
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """Update with standardized response."""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            return self.success_response(
                data=serializer.data,
                message=_('Updated successfully.')
            )
        except Exception as e:
            logger.error(f"Error updating {self.__class__.__name__}: {str(e)}")
            return self.error_response(
                message=_('Failed to update resource.'),
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete with standardized response."""
        try:
            instance = self.get_object()
            
            # Check if model supports soft delete
            if hasattr(instance, 'soft_delete'):
                instance.soft_delete()
                message = _('Resource archived successfully.')
            else:
                self.perform_destroy(instance)
                message = _('Deleted successfully.')
            
            return self.success_response(message=message)
        except Exception as e:
            logger.error(f"Error deleting {self.__class__.__name__}: {str(e)}")
            return self.error_response(
                message=_('Failed to delete resource.'),
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    def list(self, request, *args, **kwargs):
        """List with standardized response and optional pagination."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(data=serializer.data)
        except Exception as e:
            logger.error(f"Error listing {self.__class__.__name__}: {str(e)}")
            return self.error_response(
                message=_('Failed to retrieve resources.'),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve with standardized response."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.success_response(data=serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving {self.__class__.__name__}: {str(e)}")
            return self.not_found_response()


class AdminOnlyMixin:
    """
    Mixin to restrict actions to admin users only.
    """
    
    def get_permissions(self):
        """
        Set admin-only permissions for create, update, delete actions.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]


class TeacherAdminMixin:
    """
    Mixin to restrict certain actions to teachers and admins.
    """
    
    def get_permissions(self):
        """
        Set teacher/admin permissions for create, update, delete actions.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdminOrTeacher]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]


class StudentOnlyMixin:
    """
    Mixin to restrict certain actions to students only.
    """
    
    def get_permissions(self):
        """
        Set student-only permissions for specific actions.
        """
        if self.action in ['create_attendance', 'mark_attendance']:
            permission_classes = [IsAuthenticated, IsStudent]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]


class BulkOperationsMixin:
    """
    Mixin to add common bulk operations.
    """
    
    def bulk_create(self, request, *args, **kwargs):
        """Create multiple instances at once."""
        try:
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            
            instances = []
            for item_data in serializer.validated_data:
                instance = self.get_serializer().Meta.model(**item_data)
                if hasattr(instance, 'created_by') and request.user.is_authenticated:
                    instance.created_by = request.user
                instances.append(instance)
            
            created_instances = self.get_serializer().Meta.model.objects.bulk_create(instances)
            
            return self.success_response(
                data=self.get_serializer(created_instances, many=True).data,
                message=_('%(count)s items created successfully.') % {'count': len(created_instances)},
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error in bulk create: {str(e)}")
            return self.error_response(
                message=_('Failed to create items in bulk.'),
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    def bulk_update(self, request, *args, **kwargs):
        """Update multiple instances at once."""
        # Implementation for bulk update
        return self.error_response(
            message=_('Bulk update not implemented.'),
            status_code=status.HTTP_501_NOT_IMPLEMENTED
        )
    
    def bulk_delete(self, request, *args, **kwargs):
        """Delete multiple instances at once."""
        try:
            ids = request.data.get('ids', [])
            if not ids:
                return self.validation_error_response(
                    errors={'ids': _('List of IDs is required.')},
                    message=_('No IDs provided for bulk delete.')
                )
            
            queryset = self.get_queryset().filter(id__in=ids)
            count = queryset.count()
            
            # Check if model supports soft delete
            if hasattr(queryset.first(), 'soft_delete'):
                for instance in queryset:
                    instance.soft_delete()
                message = _('%(count)s items archived successfully.') % {'count': count}
            else:
                queryset.delete()
                message = _('%(count)s items deleted successfully.') % {'count': count}
            
            return self.success_response(message=message)
        except Exception as e:
            logger.error(f"Error in bulk delete: {str(e)}")
            return self.error_response(
                message=_('Failed to delete items in bulk.'),
                status_code=status.HTTP_400_BAD_REQUEST
            )


class ExportMixin:
    """
    Mixin to add data export capabilities.
    """
    
    def export_csv(self, request, *args, **kwargs):
        """Export data as CSV."""
        return self.error_response(
            message=_('CSV export not implemented for this resource.'),
            status_code=status.HTTP_501_NOT_IMPLEMENTED
        )
    
    def export_excel(self, request, *args, **kwargs):
        """Export data as Excel."""
        return self.error_response(
            message=_('Excel export not implemented for this resource.'),
            status_code=status.HTTP_501_NOT_IMPLEMENTED
        )


# Specialized base classes for common patterns
class AdminModelViewSet(AdminOnlyMixin, BaseModelViewSet):
    """ViewSet restricted to admin users only."""
    pass


class TeacherAdminModelViewSet(TeacherAdminMixin, BaseModelViewSet):
    """ViewSet restricted to teachers and admin users."""
    pass


class ReadOnlyViewSet(BaseModelViewSet):
    """Read-only ViewSet with list and retrieve actions only."""
    
    http_method_names = ['get', 'head', 'options']
    
    def create(self, request, *args, **kwargs):
        return self.error_response(
            message=_('Create operation not allowed.'),
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, *args, **kwargs):
        return self.error_response(
            message=_('Update operation not allowed.'),
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        return self.error_response(
            message=_('Delete operation not allowed.'),
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED
        )