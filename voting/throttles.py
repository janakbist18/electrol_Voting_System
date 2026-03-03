from rest_framework.throttling import SimpleRateThrottle

class VoteRateThrottle(SimpleRateThrottle):
    scope = "vote"

    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            ident = self.get_ident(request)
            return self.cache_format % {"scope": self.scope, "ident": ident}
        return self.cache_format % {"scope": self.scope, "ident": f"user:{request.user.pk}"}