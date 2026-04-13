import logging
import time
from collections import defaultdict
from threading import Lock
from django.http import JsonResponse
from utils.helpers import get_client_ip


logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_storage = defaultdict(list)  # {ip: [timestamp1, timestamp2, ...]}
        self.lock = Lock()
        
        # Rate limit settings
        self.max_requests = 200  # Maximum requests
        self.time_window = 60  # Time window in seconds (1 minute)
    
    def is_rate_limited(self, ip):
        """Check if IP has exceeded rate limit"""
        current_time = time.time()
        
        with self.lock:
            # Get request timestamps for this IP
            request_times = self.rate_limit_storage[ip]
            
            # Remove timestamps older than the time window
            request_times[:] = [t for t in request_times if current_time - t < self.time_window]
            
            # Check if limit exceeded
            if len(request_times) >= self.max_requests:
                return True
            
            # Add current request timestamp
            request_times.append(current_time)
            return False
    
    def __call__(self, request):
        ip = get_client_ip(request)
        
        # Skip rate limiting for camera frame endpoints (they poll frequently)
        if '/camera/sources/' in request.path and '/latest-frame' in request.path:
            return self.get_response(request)
        
        # Check rate limit
        if self.is_rate_limited(ip):
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please try again later.',
                    'retry_after': self.time_window
                },
                status=429
            )
        
        response = self.get_response(request)
        
        # Add rate limit headers
        remaining = self.max_requests - len(self.rate_limit_storage[ip])
        response['X-RateLimit-Limit'] = str(self.max_requests)
        response['X-RateLimit-Remaining'] = str(max(0, remaining))
        response['X-RateLimit-Reset'] = str(int(time.time() + self.time_window))
        
        return response


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code executed for each request before the view is called
        if ip_address := request.META.get('REMOTE_ADDR', ''):
            logger.info(f"Request from IP: {ip_address}")
        if x_forwarded_for := request.META.get('HTTP_X_FORWARDED_FOR'):
            logger.info(f"X-Forwarded-For: {x_forwarded_for}")
        logger.info(f"Incoming request: {request.method} {request.path}")

        response = self.get_response(request)

        # Code executed for each request/response after the view is called
        logger.info(f"Outgoing response: {response.status_code} for {request.method} {request.path}")
        return response