from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage


class VersionedStaticFilesStorage(StaticFilesStorage):
    """Add a file timestamp query string so browsers fetch changed assets."""

    def url(self, name, force=False):
        try:
            url = super().url(name, force=force)
        except TypeError:
            url = super().url(name)
        version = self._asset_version(name)
        if not version:
            return url

        scheme, netloc, path, query, fragment = urlsplit(url)
        query_params = dict(parse_qsl(query, keep_blank_values=True))
        query_params["v"] = version
        return urlunsplit((scheme, netloc, path, urlencode(query_params), fragment))

    def _asset_version(self, name):
        candidates = []

        try:
            candidates.append(Path(self.path(name)))
        except (NotImplementedError, ValueError):
            pass

        found = finders.find(name)
        if found:
            if isinstance(found, (list, tuple)):
                candidates.extend(Path(path) for path in found)
            else:
                candidates.append(Path(found))

        for candidate in candidates:
            try:
                return str(int(candidate.stat().st_mtime))
            except OSError:
                continue
        return ""
