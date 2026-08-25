from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from subscriptions.whatsapp import WhatsAppAPIError, WhatsAppConfigurationError, get_waba_template_details


class Command(BaseCommand):
    help = "Check Fast2SMS WABA numbers and approved WhatsApp templates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            choices=("number", "template"),
            default="template",
            help="Fast2SMS DLT manager detail type to fetch.",
        )
        parser.add_argument(
            "--phone-number-id",
            default="",
            help="Optional phone number ID filter. Defaults to WHATSAPP_PHONE_NUMBER_ID.",
        )

    def handle(self, *args, **options):
        try:
            accounts = get_waba_template_details(
                options["type"],
                phone_number_id=options["phone_number_id"] or settings.WHATSAPP_PHONE_NUMBER_ID,
            )
        except (WhatsAppAPIError, WhatsAppConfigurationError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        if not accounts:
            self.stdout.write(self.style.WARNING("No WABA records returned."))
            return

        for account in accounts:
            number = account.get("number") or account.get("sender_number") or "-"
            phone_number_id = account.get("phone_number_id") or "-"
            self.stdout.write(f"Number: {number} | Phone Number ID: {phone_number_id}")
            for template in account.get("templates", []):
                self.stdout.write(
                    "  "
                    f"{template.get('template_name')} | "
                    f"{template.get('status')} | "
                    f"{template.get('language')} | "
                    f"message_id={template.get('message_id')} | "
                    f"template_id={template.get('template_id')}"
                )
