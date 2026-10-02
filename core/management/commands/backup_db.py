from datetime import datetime
from pathlib import Path
import shutil
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.db import connection

class Command(BaseCommand):
    help="Create a timestamped copy of the SQLite database. Back up media separately."
    def handle(self,*args,**opts):
        if connection.vendor!="sqlite": raise CommandError("This helper supports SQLite only. For PostgreSQL use pg_dump and include media separately.")
        source=Path(connection.settings_dict["NAME"])
        if not source.exists(): raise CommandError(f"Database file not found: {source}")
        target_dir=settings.BASE_DIR/"backups"; target_dir.mkdir(exist_ok=True)
        target=target_dir/f"gym-manager-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sqlite3"
        shutil.copy2(source,target)
        self.stdout.write(self.style.SUCCESS(f"Database backup created: {target}"))
