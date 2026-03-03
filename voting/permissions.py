from __future__ import annotations

from rest_framework.permissions import BasePermission

class IsAuthenticatedVoter(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class IsVerifiedVoter(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        vp = getattr(request.user, "voter_profile", None)
        return bool(vp and vp.is_verified and vp.constituency_id)