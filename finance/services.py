from django.utils import timezone
from .models import FinanceEntry


def record_income(*, club, amount, description, source, source_id, branch=None, account=None, category=None, user=None, occurred_on=None):
    if amount <= 0:
        return None
    entry, _ = FinanceEntry.objects.get_or_create(
        club=club, source=source, source_id=str(source_id),
        defaults={
            "branch": branch, "account": account, "category": category,
            "entry_type": "income", "amount": amount,
            "occurred_on": occurred_on or timezone.localdate(),
            "description": description, "created_by": user,
        },
    )
    return entry
