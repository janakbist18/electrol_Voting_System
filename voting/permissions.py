from __future__ import annotations

from rest_framework.permissions import BasePermission

class IsAuthenticatedVoter(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class IsVerifiedVoter(BasePermission):
    """Only verified voters who are not admins can vote"""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        vp = getattr(request.user, "voter_profile", None)
        # Check: verified, has constituency, and is NOT an admin
        if not vp or not vp.is_verified or not vp.constituency_id or vp.is_admin:
            return False
        return True

class IsAdminUser(BasePermission):
    """Check if user is a staff/admin user"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)