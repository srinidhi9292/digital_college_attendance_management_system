"""
Custom decorators for role-based access control
Path: attendance/decorators.py
"""

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps

def role_required(roles):
    """
    Decorator to check if user has any of the specified roles
    
    Usage:
        @login_required
        @roles_required('admin', 'faculty')
        def shared_view(request):
            # View code here
            pass

    Args:
        *roles: Variable number of allowed roles
        
    Returns:
        Decorated function that checks if user has any of the specified roles
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.warning(request, 'Please login to access this page.')
                return redirect('login')

            # Check if user has any of the required roles
            if request.user.role not in roles:
                messages.error(
                    request,
                    'Access denied. You do not have permission to access this page.'
                )
                return redirect('dashboard')
                
            # User has correct role, proceed with view
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator

def admin_required(view_func):
    """
    Shortcut decorator for admin-only views
    
    Usage:
        @admin_required
        def admin_view(request):
            # View code here
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
            
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Admin access required.')
            return redirect('dashboard')
            
        return view_func(request, *args, **kwargs)
        
    return wrapper

def faculty_required(view_func):
    """
    Shortcut decorator for faculty-only views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
            
        if request.user.role != 'faculty':
            messages.error(request, 'Access denied. Faculty access required.')
            return redirect('dashboard')
            
        return view_func(request, *args, **kwargs)
        
    return wrapper

def student_required(view_func):
    """
    Shortcut decorator for student-only views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('login')
            
        if request.user.role != 'student':
            messages.error(request, 'Access denied. Student access required.')
            return redirect('dashboard')
            
        return view_func(request, *args, **kwargs)
        
    return wrapper

def ajax_required(view_func):
    """
    Decorator to check if request is AJAX
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            messages.error(request, 'Invalid request. AJAX required.')
            return redirect('dashboard')
            
        return view_func(request, *args, **kwargs)
        
    return wrapper