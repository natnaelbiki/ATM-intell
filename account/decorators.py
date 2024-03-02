from django.shortcuts import render

def role_required(*allowed_roles):
    """
    Decorator to allow access only to users with a specified role.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return render(request, 'error_page.html', {'e': "You must be logged in to view this page." })
            if hasattr(request.user, 'role') and request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return render(request, 'error_page.html', {'e': "You do not have permission to view this page."})
        return _wrapped_view
    return decorator
