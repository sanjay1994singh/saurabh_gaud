"""
ASGI config for dharm_raksha_sangh project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dharm_raksha_sangh.settings")

application = get_asgi_application()
