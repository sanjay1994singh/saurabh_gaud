from django.core.management.base import BaseCommand

from patrika.models import Patrika
from patrika.services import convert_patrika_pdf_to_pages


class Command(BaseCommand):
    help = "Convert patrika PDFs into image pages for the e-paper reader."

    def add_arguments(self, parser):
        parser.add_argument("--id", type=int, help="Convert only one patrika by id.")
        parser.add_argument("--zoom", type=float, default=2, help="PDF render zoom. Default: 2.")
        parser.add_argument(
            "--missing-only",
            action="store_true",
            help="Skip patrika records that already have generated pages.",
        )

    def handle(self, *args, **options):
        queryset = Patrika.objects.all()
        if options["id"]:
            queryset = queryset.filter(pk=options["id"])

        converted = 0
        for patrika in queryset:
            if options["missing_only"] and patrika.pages.exists():
                self.stdout.write(f"Skipping {patrika.pk}: pages already exist")
                continue
            if not patrika.pdf:
                self.stdout.write(f"Skipping {patrika.pk}: no PDF")
                continue

            page_count = convert_patrika_pdf_to_pages(patrika, zoom=options["zoom"])
            converted += 1
            self.stdout.write(self.style.SUCCESS(f"{patrika.pk}: {page_count} page(s) generated"))

        self.stdout.write(self.style.SUCCESS(f"Converted {converted} patrika PDF(s)."))
