from django.core.management.base import BaseCommand,CommandError
from django.utils import timezone
from integrations.models import ClubApiKey
class Command(BaseCommand):
    help="Revoke a club API key by prefix."
    def add_arguments(self,parser): parser.add_argument("prefix")
    def handle(self,*args,**opts):
        key=ClubApiKey.objects.filter(prefix=opts["prefix"],revoked_at__isnull=True).first()
        if not key: raise CommandError("Active API key not found")
        key.revoked_at=timezone.now(); key.save(update_fields=["revoked_at"])
        self.stdout.write(self.style.SUCCESS("API key revoked"))
