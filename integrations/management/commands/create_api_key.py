import hashlib,secrets
from django.core.management.base import BaseCommand,CommandError
from core.models import Club
from integrations.models import ClubApiKey

class Command(BaseCommand):
    help="Create a club-scoped read-only API key; the secret is shown only once."
    def add_arguments(self,parser):
        parser.add_argument("club_code"); parser.add_argument("name"); parser.add_argument("--scope",action="append",choices=["summary:read","members:read"],default=[])
    def handle(self,*args,**opts):
        club=Club.objects.filter(code=opts["club_code"]).first()
        if not club: raise CommandError("Club code not found")
        secret=secrets.token_urlsafe(32); prefix=secrets.token_hex(5)
        key=ClubApiKey.objects.create(club=club,name=opts["name"],prefix=prefix,secret_hash=hashlib.sha256(secret.encode()).hexdigest(),scopes=opts["scope"] or ["summary:read"])
        self.stdout.write(self.style.SUCCESS(f"API key (save now; not shown again): {key.prefix}.{secret}"))
