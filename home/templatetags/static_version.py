from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static


register = template.Library()


@register.simple_tag
def static_v(path):
    """Return a static URL with a file timestamp query string."""
    url = static(path)
    version = _static_mtime(path)
    if not version:
        return url

    scheme, netloc, url_path, query, fragment = urlsplit(url)
    query_params = dict(parse_qsl(query, keep_blank_values=True))
    query_params["v"] = version
    return urlunsplit((scheme, netloc, url_path, urlencode(query_params), fragment))


def _static_mtime(path):
    candidates = []
    found = finders.find(path)
    if found:
        if isinstance(found, (list, tuple)):
            candidates.extend(Path(item) for item in found)
        else:
            candidates.append(Path(found))

    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        candidates.append(Path(static_root) / path)

    for candidate in candidates:
        try:
            return str(int(candidate.stat().st_mtime))
        except OSError:
            continue
    return ""
