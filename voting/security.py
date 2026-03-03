from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    """
    Only staff users can access.
    Use for admin-only pages (not /admin/ itself).
    """
    return staff_member_required(view_func)