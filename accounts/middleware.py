from django.utils.deprecation import MiddlewareMixin

class TenantMiddleware(MiddlewareMixin):
    """
    Adds request.tenant = user.tenant for authenticated users.
    All tenant-scoped queries will rely on this.
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            request.tenant = request.user.tenant
        else:
            request.tenant = None
