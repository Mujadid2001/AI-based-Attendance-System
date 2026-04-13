"""
Enterprise security middleware for government-level compliance.
"""
import json
import time
import hashlib
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from .models import SecurityAuditLog, SessionSecurity, SecurityIncident
from .services import SecurityService
from utils.helpers import get_client_ip
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SecurityAuditMiddleware(MiddlewareMixin):
    """Comprehensive security audit middleware."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Add security metadata to request
        request.security_metadata = {
            'start_time': time.time(),
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'device_fingerprint': self.generate_device_fingerprint(request),
        }
        
        # Check for suspicious activity
        if self.is_suspicious_request(request):
            self.log_security_event(
                request,
                'SECURITY_VIOLATION',
                'Suspicious request detected',
                SecurityAuditLog.RiskLevel.HIGH
            )
            
            # Optional: Block the request
            if getattr(settings, 'BLOCK_SUSPICIOUS_REQUESTS', False):
                return JsonResponse({
                    'error': 'Request blocked due to security policy'
                }, status=403)
    
    def process_response(self, request, response):
        if hasattr(request, 'security_metadata'):
            # Log the request
            self.log_request(request, response)
            
            # Update session security if user is authenticated
            if hasattr(request, 'user') and request.user.is_authenticated:
                self.update_session_security(request)
        
        return response
    
    def generate_device_fingerprint(self, request):
        """Generate a device fingerprint for tracking."""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        fingerprint_data = f"{user_agent}{accept_language}{accept_encoding}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    def is_suspicious_request(self, request):
        """Check if request shows suspicious patterns."""
        ip = request.security_metadata['ip_address']
        
        # Check rate limiting
        cache_key = f"rate_limit:{ip}"
        requests_count = cache.get(cache_key, 0)
        if requests_count > getattr(settings, 'MAX_REQUESTS_PER_MINUTE', 100):
            return True
        
        # Check for known attack patterns
        path = request.get_full_path().lower()
        suspicious_patterns = [
            'admin/', '../', 'union select', 'script>', 'javascript:',
            'eval(', 'base64_decode', 'file_get_contents', 'shell_exec'
        ]
        
        for pattern in suspicious_patterns:
            if pattern in path:
                return True
        
        return False
    
    def log_request(self, request, response):
        """Log the request for audit purposes."""
        try:
            # Determine risk level
            risk_level = SecurityAuditLog.RiskLevel.LOW
            if response.status_code >= 400:
                risk_level = SecurityAuditLog.RiskLevel.MEDIUM
            if response.status_code >= 500:
                risk_level = SecurityAuditLog.RiskLevel.HIGH
            
            # Create audit log entry
            SecurityAuditLog.objects.create(
                user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                session_id=request.session.session_key if hasattr(request, 'session') else None,
                action_type='DATA_ACCESS',
                risk_level=risk_level,
                description=f"{request.method} {request.get_full_path()}",
                ip_address=request.security_metadata['ip_address'],
                user_agent=request.security_metadata['user_agent'],
                endpoint=request.get_full_path(),
                http_method=request.method,
                response_code=response.status_code,
                metadata={
                    'processing_time': time.time() - request.security_metadata['start_time'],
                    'device_fingerprint': request.security_metadata['device_fingerprint']
                }
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
    
    def log_security_event(self, request, action_type, description, risk_level):
        """Log a security event."""
        try:
            SecurityAuditLog.objects.create(
                user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                action_type=action_type,
                risk_level=risk_level,
                description=description,
                ip_address=request.security_metadata['ip_address'],
                user_agent=request.security_metadata['user_agent'],
                endpoint=request.get_full_path(),
                http_method=request.method
            )
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
    
    def update_session_security(self, request):
        """Update session security information."""
        try:
            session_key = request.session.session_key
            if session_key:
                SessionSecurity.objects.update_or_create(
                    session_key=session_key,
                    defaults={
                        'user': request.user,
                        'ip_address': request.security_metadata['ip_address'],
                        'user_agent': request.security_metadata['user_agent'],
                        'device_fingerprint': request.security_metadata['device_fingerprint'],
                        'last_activity': timezone.now(),
                        'expires_at': timezone.now() + timezone.timedelta(
                            seconds=settings.SESSION_COOKIE_AGE
                        )
                    }
                )
        except Exception as e:
            logger.error(f"Failed to update session security: {str(e)}")


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware for DDoS protection."""
    
    def process_request(self, request):
        ip = get_client_ip(request)
        
        # Different limits for different endpoints
        if request.path.startswith('/api/auth/'):
            max_requests = getattr(settings, 'AUTH_RATE_LIMIT', 20)
            window = 300  # 5 minutes
        elif request.path.startswith('/api/'):
            max_requests = getattr(settings, 'API_RATE_LIMIT', 100)
            window = 60  # 1 minute
        else:
            max_requests = getattr(settings, 'GENERAL_RATE_LIMIT', 200)
            window = 60  # 1 minute
        
        cache_key = f"rate_limit:{ip}:{request.path}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= max_requests:
            # Log the rate limit violation
            SecurityAuditLog.objects.create(
                action_type='SECURITY_VIOLATION',
                risk_level=SecurityAuditLog.RiskLevel.HIGH,
                description=f"Rate limit exceeded for {ip}",
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                endpoint=request.path,
                http_method=request.method
            )
            
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after': window
            }, status=429)
        
        # Increment the counter
        cache.set(cache_key, current_count + 1, window)
        return None


class DataProtectionMiddleware(MiddlewareMixin):
    """Data protection and privacy middleware."""
    
    def process_request(self, request):
        # Add data protection headers
        if hasattr(request, 'META'):
            # Check for data protection compliance
            if 'HTTP_DNT' in request.META and request.META['HTTP_DNT'] == '1':
                request.do_not_track = True
            else:
                request.do_not_track = False
    
    def process_response(self, request, response):
        # Add privacy and security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        
        # GDPR compliance headers
        if hasattr(request, 'do_not_track') and request.do_not_track:
            response['Tk'] = 'N'
        
        return response