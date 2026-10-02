from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from attendance.models import AttendanceRecord
from membership.models import MembershipContract
from crm.models import MessageQueue

class Command(BaseCommand):
    help="Queue club-scoped membership renewal and inactivity reminders; does not send them."
    def add_arguments(self,parser):
        parser.add_argument("--days",type=int,default=7,help="Days before contract expiry")
        parser.add_argument("--inactive-days",type=int,default=14,help="No-attendance interval")
    def handle(self,*args,**opts):
        today=timezone.localdate(); queued=0
        contracts=MembershipContract.objects.filter(status="active",end_date=today+timedelta(days=max(0,opts["days"]))).select_related("club","member")
        for contract in contracts:
            body=f"یادآوری تمدید عضویت: قرارداد {contract.contract_code} تا {contract.end_date} معتبر است."
            _,created=MessageQueue.objects.get_or_create(club=contract.club,dedupe_key=f"renewal:{contract.pk}:{contract.end_date}",defaults={"member":contract.member,"channel":"sms","recipient":contract.member.mobile,"body":body})
            queued+=int(created)
        cutoff=today-timedelta(days=opts["inactive_days"])
        eligible=MembershipContract.objects.filter(status="active",start_date__lte=today,end_date__gte=today).select_related("club","member")
        seen=set()
        for contract in eligible:
            ref=(contract.club_id,contract.member_id)
            if ref in seen: continue
            seen.add(ref)
            recent=AttendanceRecord.objects.filter(club_id=contract.club_id,member_id=contract.member_id,check_in__date__gte=cutoff).exists()
            if recent: continue
            body=f"دلمان برای دیدنتان تنگ شده؛ عضویت شما در {contract.club.name} فعال است."
            _,created=MessageQueue.objects.get_or_create(club=contract.club,dedupe_key=f"inactive:{contract.member_id}:{today:%Y-%m}",defaults={"member":contract.member,"channel":"sms","recipient":contract.member.mobile,"body":body})
            queued+=int(created)
        self.stdout.write(self.style.SUCCESS(f"{queued} reminder(s) queued. No external message was sent."))
