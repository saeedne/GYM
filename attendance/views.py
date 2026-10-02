from datetime import datetime, time, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone
from core.models import AuditLog
from membership.models import MembershipContract
from members.models import Member
from access_control.models import AccessCredential, AccessPolicy
from .forms import AttendanceReportFilter, CheckInForm
from .models import AttendanceRecord


@login_required
def checkin(request):
    club = request.active_club
    if not club:
        return redirect("dashboard")
    form = CheckInForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        token = form.cleaned_data["credential_value"].strip()
        credential = AccessCredential.objects.filter(club=club, token=token, is_active=True).select_related("member").first()
        member = credential.member if credential else Member.objects.filter(club=club, member_code=token).first()
        if not member:
            messages.error(request, "کد عضویت در این باشگاه پیدا نشد.")
        elif AttendanceRecord.objects.filter(club=club, member=member, status="open").exists():
            messages.warning(request, f"{member.full_name} هم‌اکنون ورود باز دارد؛ برای ثبت خروج، دکمه خروج را بزنید.")
        else:
            now = timezone.now()
            valid_contract = MembershipContract.objects.filter(
                club=club, member=member, status="active",
                start_date__lte=timezone.localdate(), end_date__gte=timezone.localdate(),
            ).exists()
            active_member = member.status == "active"
            allowed = active_member and valid_contract
            reason = "" if allowed else ("وضعیت عضو فعال نیست." if not active_member else "عضویت معتبر و فعال ندارد.")
            contract = MembershipContract.objects.filter(
                club=club, member=member, status="active",
                start_date__lte=timezone.localdate(), end_date__gte=timezone.localdate(),
            ).select_related("plan").order_by("-end_date").first()
            local_now = timezone.localtime(now)
            policy = AccessPolicy.objects.filter(club=club).first()
            if allowed and contract and contract.plan.max_checkins is not None:
                used = AttendanceRecord.objects.filter(
                    club=club, member=member, status__in=("open", "closed"),
                    check_in__date__gte=contract.start_date, check_in__date__lte=timezone.localdate(),
                ).count()
                if used >= contract.plan.max_checkins:
                    allowed, reason = False, "سهمیه ورود این قرارداد به پایان رسیده است."
            if allowed and policy and policy.enforce_days:
                persian_weekday = (timezone.localdate().weekday() + 2) % 7
                if persian_weekday not in policy.allowed_weekdays:
                    allowed, reason = False, "ورود در این روز مجاز نیست."
            if allowed and policy and policy.enforce_hours:
                if not policy.opening_time or not policy.closing_time or not (policy.opening_time <= local_now.time() <= policy.closing_time):
                    allowed, reason = False, "ورود خارج از ساعت مجاز باشگاه است."
            if credential:
                credential.last_used_at = now
                credential.save(update_fields=["last_used_at"])
            record = AttendanceRecord(
                club=club, branch=form.cleaned_data.get("branch"), member=member,
                check_in=now, status="open" if allowed else "denied",
                source=(credential.credential_type if credential else "reception"),
                denial_reason=reason, created_by=request.user,
            )
            try:
                record.save()
                AuditLog.objects.create(
                    club=club, user=request.user, action="create", model_name="AttendanceRecord",
                    object_id=str(record.pk), description=f"ورود {member.full_name}: {'پذیرفته شد' if allowed else 'رد شد'}",
                )
                (messages.success if allowed else messages.error)(request, f"{member.full_name}: {'ورود ثبت شد.' if allowed else reason}")
            except IntegrityError:
                messages.warning(request, "برای این عضو ورود باز ثبت شده است.")
        return redirect("attendance:checkin")
    open_records = AttendanceRecord.objects.filter(club=club, status="open").select_related("member", "branch")[:10]
    return render(request, "attendance/checkin.html", {"club": club, "form": form, "open_records": open_records})


@login_required
def checkout(request, pk):
    club = request.active_club
    record = AttendanceRecord.objects.filter(club=club, pk=pk, status="open").first()
    if record:
        record.check_out = timezone.now()
        record.status = "closed"
        record.save(update_fields=["check_out", "status"])
        AuditLog.objects.create(club=club, user=request.user, action="update", model_name="AttendanceRecord", object_id=str(record.pk), description=f"خروج {record.member.full_name} ثبت شد.")
        messages.success(request, f"خروج {record.member.full_name} ثبت شد.")
    else:
        messages.error(request, "تردد باز در این باشگاه پیدا نشد.")
    return redirect("attendance:checkin")


@login_required
def report(request):
    club = request.active_club
    if not club:
        return redirect("dashboard")
    form = AttendanceReportFilter(request.GET or None)
    if not request.GET:
        form.initial_today()
    qs = AttendanceRecord.objects.filter(club=club).select_related("member", "branch")
    if request.GET and form.is_valid():
        start, end = form.cleaned_data.get("start"), form.cleaned_data.get("end")
        if start:
            qs = qs.filter(check_in__date__gte=start)
        if end:
            qs = qs.filter(check_in__lt=end + timedelta(days=1))
    total = qs.count()
    admitted = qs.exclude(status="denied").count()
    denied = qs.filter(status="denied").count()
    open_count = qs.filter(status="open").count()
    daily = list(qs.values("check_in__date").annotate(
        visits=Count("id"), denied=Count("id", filter=Q(status="denied"))
    ).order_by("-check_in__date")[:31])
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    return render(request, "attendance/report.html", {
        "club": club, "form": form, "records": page, "page_obj": page,
        "total": total, "admitted": admitted, "denied": denied,
        "open_count": open_count, "daily": daily,
    })
