"""
Custom middleware for the MSR Control application.

This module contains middleware classes for security, logging, and other purposes.
"""
import time
import logging

logger = logging.getLogger('msr_control.middleware')

class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to HTTP responses.
    
    This middleware adds various security headers to HTTP responses to improve
    the security posture of the application.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        # Add Content Security Policy (CSP) header
        # Adjust this policy based on your application's needs
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp_policy
        
        return response

class RequestLoggingMiddleware:
    """
    Middleware to log HTTP requests and responses.
    
    This middleware logs information about incoming HTTP requests and outgoing
    responses, including timing information.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Start timing
        start_time = time.time()
        
        # Get request details
        method = request.method
        path = request.path
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log the request
        status_code = response.status_code
        user = request.user.username if hasattr(request.user, 'username') else 'anonymous'
        
        logger.info(
            f"Request: {method} {path} - "
            f"Status: {status_code} - "
            f"User: {user} - "
            f"Duration: {duration:.3f}s"
        )
        
        return response
