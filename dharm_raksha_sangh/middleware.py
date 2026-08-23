from django.utils.cache import patch_cache_control


class NoCacheHtmlMiddleware:
    """Force browsers to revalidate HTML while static assets use versioned URLs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get("Content-Type", "")
        if content_type.startswith("text/html"):
            patch_cache_control(response, no_cache=True, must_revalidate=True)
        return response
