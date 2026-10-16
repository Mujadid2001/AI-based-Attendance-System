"""
Common response utilities to standardize API responses and reduce code duplication.
"""
from rest_framework import status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class APIResponse:
    """
    Standardized API response builder to ensure consistency across all endpoints.
    """
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = None,
        status_code: int = status.HTTP_200_OK,
        meta: Dict = None
    ) -> Response:
        """
        Create a standardized success response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            meta: Additional metadata
            
        Returns:
            Response: Standardized success response
        """
        response_data = {
            'success': True,
            'message': message or _('Operation completed successfully.'),
        }
        
        if data is not None:
            response_data['data'] = data
            
        if meta:
            response_data['meta'] = meta
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(
        message: str = None,
        errors: Union[str, Dict, list] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = None
    ) -> Response:
        """
        Create a standardized error response.
        
        Args:
            message: Error message
            errors: Detailed errors (validation errors, etc.)
            status_code: HTTP status code
            error_code: Custom error code for error handling
            
        Returns:
            Response: Standardized error response
        """
        response_data = {
            'success': False,
            'message': message or _('An error occurred.'),
        }
        
        if errors:
            response_data['errors'] = errors
            
        if error_code:
            response_data['error_code'] = error_code
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def validation_error(errors: Dict, message: str = None) -> Response:
        """
        Create a validation error response.
        
        Args:
            errors: Validation errors dictionary
            message: Custom error message
            
        Returns:
            Response: Validation error response
        """
        return APIResponse.error(
            message=message or _('Validation failed.'),
            errors=errors,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code='VALIDATION_ERROR'
        )
    
    @staticmethod
    def not_found(message: str = None, resource: str = None) -> Response:
        """
        Create a not found error response.
        
        Args:
            message: Custom error message
            resource: Resource name that was not found
            
        Returns:
            Response: Not found error response
        """
        if resource:
            message = message or _('%(resource)s not found.') % {'resource': resource}
        else:
            message = message or _('Resource not found.')
            
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code='NOT_FOUND'
        )
    
    @staticmethod
    def forbidden(message: str = None) -> Response:
        """
        Create a forbidden error response.
        
        Args:
            message: Custom error message
            
        Returns:
            Response: Forbidden error response
        """
        return APIResponse.error(
            message=message or _('Permission denied.'),
            status_code=status.HTTP_403_FORBIDDEN,
            error_code='PERMISSION_DENIED'
        )
    
    @staticmethod
    def unauthorized(message: str = None) -> Response:
        """
        Create an unauthorized error response.
        
        Args:
            message: Custom error message
            
        Returns:
            Response: Unauthorized error response
        """
        return APIResponse.error(
            message=message or _('Authentication credentials were not provided.'),
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code='AUTHENTICATION_REQUIRED'
        )
    
    @staticmethod
    def server_error(message: str = None, log_error: bool = True) -> Response:
        """
        Create a server error response.
        
        Args:
            message: Custom error message
            log_error: Whether to log the error
            
        Returns:
            Response: Server error response
        """
        error_message = message or _('Internal server error occurred.')
        
        if log_error:
            logger.error(f"Server error: {error_message}")
            
        return APIResponse.error(
            message=error_message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code='INTERNAL_SERVER_ERROR'
        )
    
    @staticmethod
    def paginated_response(
        data: Any,
        page_info: Dict,
        message: str = None
    ) -> Response:
        """
        Create a paginated response.
        
        Args:
            data: Paginated data
            page_info: Pagination information
            message: Optional message
            
        Returns:
            Response: Paginated response
        """
        return APIResponse.success(
            data=data,
            message=message,
            meta={
                'pagination': page_info
            }
        )


class ResponseMixin:
    """
    Mixin for ViewSets to provide standardized response methods.
    """
    
    def success_response(self, *args, **kwargs) -> Response:
        """Create success response."""
        return APIResponse.success(*args, **kwargs)
    
    def error_response(self, *args, **kwargs) -> Response:
        """Create error response."""
        return APIResponse.error(*args, **kwargs)
    
    def validation_error_response(self, *args, **kwargs) -> Response:
        """Create validation error response."""
        return APIResponse.validation_error(*args, **kwargs)
    
    def not_found_response(self, *args, **kwargs) -> Response:
        """Create not found response."""
        return APIResponse.not_found(*args, **kwargs)
    
    def forbidden_response(self, *args, **kwargs) -> Response:
        """Create forbidden response."""
        return APIResponse.forbidden(*args, **kwargs)


def handle_exceptions(func):
    """
    Decorator to handle common exceptions in views.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.error(f"ValueError in {func.__name__}: {str(e)}")
            return APIResponse.validation_error(
                errors={'error': str(e)},
                message=_('Invalid input provided.')
            )
        except PermissionError as e:
            logger.warning(f"PermissionError in {func.__name__}: {str(e)}")
            return APIResponse.forbidden(message=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return APIResponse.server_error(
                message=_('An unexpected error occurred. Please try again later.')
            )
    
    return wrapper


# Common error messages
class ErrorMessages:
    """
    Common error messages to maintain consistency.
    """
    PERMISSION_DENIED = _('You do not have permission to perform this action.')
    NOT_FOUND = _('The requested resource was not found.')
    INVALID_CREDENTIALS = _('Invalid credentials provided.')
    EMAIL_NOT_VERIFIED = _('Please verify your email address before proceeding.')
    ACCOUNT_NOT_APPROVED = _('Your account is pending approval.')
    INVALID_FILE_FORMAT = _('Invalid file format. Please upload a valid file.')
    FILE_TOO_LARGE = _('File size exceeds the maximum allowed limit.')
    REQUIRED_FIELD = _('This field is required.')
    INVALID_INPUT = _('Invalid input provided.')
    OPERATION_NOT_ALLOWED = _('This operation is not allowed.')
    SERVICE_UNAVAILABLE = _('Service is temporarily unavailable. Please try again later.')


# Common success messages
class SuccessMessages:
    """
    Common success messages to maintain consistency.
    """
    CREATED_SUCCESSFULLY = _('Created successfully.')
    UPDATED_SUCCESSFULLY = _('Updated successfully.')
    DELETED_SUCCESSFULLY = _('Deleted successfully.')
    OPERATION_COMPLETED = _('Operation completed successfully.')
    EMAIL_SENT = _('Email sent successfully.')
    PASSWORD_CHANGED = _('Password changed successfully.')
    LOGIN_SUCCESSFUL = _('Login successful.')
    LOGOUT_SUCCESSFUL = _('Logout successful.')
    REGISTRATION_SUCCESSFUL = _('Registration successful.')

# =============================================================================
# GLOBAL DRF EXCEPTION HANDLER
# =============================================================================
def api_exception_handler(exc, context):
    """
    DRF `EXCEPTION_HANDLER` for the whole project.

    Delegates to Django REST Framework's default handler and only adds the one
    case DRF cannot know about: application-level "this feature is switched
    off on this server" errors.

    Without this, an absent optional dependency (face_recognition, dlib,
    OpenCV) surfaces as an unhandled 500 with a stack trace, which is both
    useless to the frontend and alarming in the error log.
    """
    from rest_framework.views import exception_handler as drf_exception_handler

    response = drf_exception_handler(exc, context)

    if response is not None:
        return response

    # Imported here rather than at module scope: apps.ai_core imports this
    # module, so a top-level import would be circular.
    from apps.ai_core.services import AIFeatureUnavailable

    if isinstance(exc, AIFeatureUnavailable):
        body = {
            'error': str(exc.message),
            'code': 'feature_unavailable',
        }
        if exc.reason:
            # The underlying reason is useful in the server log and harmless in
            # the response: it names a missing package, not user data.
            body['detail'] = exc.reason
        return Response(body, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    logger.exception('Unhandled exception in API view')
    return None
