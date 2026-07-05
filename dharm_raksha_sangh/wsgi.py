"""
WSGI config for dharm_raksha_sangh project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dharm_raksha_sangh.settings")

application = get_wsgi_application()
