from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from dharm_raksha_sangh.image_utils import optimize_image_file


class Command(BaseCommand):
    help = "Compress existing uploaded images. Use --include-static to also compress project static images."

    IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

    def add_arguments(self, parser):
        parser.add_argument("--include-static", action="store_true", help="Also compress images under STATICFILES_DIRS.")

    def handle(self, *args, **options):
        roots = [Path(settings.MEDIA_ROOT)]
        if options["include_static"]:
            roots.extend(Path(path) for path in settings.STATICFILES_DIRS)

        total = 0
        for root in roots:
            if not root.exists():
                continue
            for image_path in root.rglob("*"):
                if not image_path.is_file() or image_path.suffix.lower() not in self.IMAGE_SUFFIXES:
                    continue
                before = image_path.stat().st_size
                optimize_image_file(image_path, max_size=(1800, 2400), quality=82, background="#ffffff")
                after = image_path.stat().st_size
                total += 1
                self.stdout.write(f"{image_path} {before // 1024}KB -> {after // 1024}KB")

        self.stdout.write(self.style.SUCCESS(f"Compressed {total} image(s)."))
