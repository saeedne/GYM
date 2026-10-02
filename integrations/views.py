from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from members.models import Member
from membership.models import MembershipContract
from attendance.models import AttendanceRecord
from access_control.models import AccessCredential
from trainers.models import ClassBooking
from workouts.models import WorkoutAssignment
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from .auth import authenticate_api_request

@login_required
def member_portal(request):
    return render(request,"integrations/portal.html",{"api_root":request.build_absolute_uri("/api/v1/")})

@login_required
@never_cache
def mobile_dashboard(request):
    club=request.active_club
    membership = getattr(request, "club_membership", None)
    if not membership or not membership.is_active or not membership.webapp_enabled:
        return render(request, "integrations/mobile_unlinked.html", status=403)
    member=Member.objects.filter(club=club,user=request.user).first() if club else None
    if not member:
        codes = set(membership.direct_permissions.values_list("codename", flat=True))
        if membership.club_role_id and membership.club_role.is_active and membership.club_role.club_id == club.id:
            codes.update(membership.club_role.permissions.values_list("codename", flat=True))
        from accounts.access import MODULES
        pages = [{"title": title, "url": path} for code, title, path in [
            ("dashboard", "داشبورد", "/"), ("members", "اعضا", "/members/"),
            ("membership", "عضویت و قراردادها", "/membership/contracts/"),
            ("attendance", "حضور و غیاب", "/attendance/"), ("training", "مربیان و کلاس‌ها", "/training/"),
            ("store", "فروشگاه", "/store/"), ("cafe", "کافی‌شاپ", "/cafe/"),
            ("workouts", "تمرین و ارزیابی", "/fitness/"), ("finance", "مالی و صندوق", "/finance/"),
            ("crm", "CRM و پیگیری", "/crm/"), ("reports", "گزارش‌ها", "/reports/"),
            ("equipment", "تجهیزات", "/equipment/"), ("users", "کاربران و نقش‌ها", "/accounts/users/"),
        ] if membership.is_manager or request.user.is_superuser or f"view_{code}" in codes]
        return render(request, "integrations/staff_mobile_dashboard.html", {"club": club, "pages": pages})
    today=timezone.localdate()
    contract=MembershipContract.objects.filter(club=club,member=member,status="active",start_date__lte=today,end_date__gte=today).select_related("plan").order_by("-end_date").first()
    visits=AttendanceRecord.objects.filter(club=club,member=member).order_by("-check_in")[:8]
    credential=AccessCredential.objects.filter(club=club,member=member,is_active=True).first()
    bookings=ClassBooking.objects.filter(club=club,member=member,status="booked",fitness_class__starts_at__gte=timezone.now()).select_related("fitness_class").order_by("fitness_class__starts_at")[:5]
    assignment=WorkoutAssignment.objects.filter(club=club,member=member,is_active=True,start_date__lte=today).select_related("plan").prefetch_related("plan__items__exercise").order_by("-start_date").first()
    response=render(request,"integrations/mobile_dashboard.html",{"member":member,"club":club,"contract":contract,"visits":visits,"credential":credential,"bookings":bookings,"assignment":assignment})
    response["Cache-Control"]="no-store, private"
    response["X-Content-Type-Options"]="nosniff"
    return response

@require_GET
def service_worker(request):
    response=FileResponse((settings.BASE_DIR/"static"/"service-worker.js").open("rb"),content_type="application/javascript; charset=utf-8")
    response["Service-Worker-Allowed"]="/"
    response["Cache-Control"]="no-cache"
    return response

@require_GET
def offline_page(request):
    return render(request,"integrations/offline.html")

def api_summary(request):
    key=authenticate_api_request(request,"summary:read")
    if not key: return JsonResponse({"detail":"معتبر نیست یا دسترسی کافی ندارد"},status=401)
    club=key.club; today=timezone.localdate()
    return JsonResponse({"club":{"code":club.code,"name":club.name},"date":today.isoformat(),"members":{"total":Member.objects.filter(club=club).count(),"active":Member.objects.filter(club=club,status="active").count()},"active_contracts":MembershipContract.objects.filter(club=club,status="active",start_date__lte=today,end_date__gte=today).count(),"open_visits":AttendanceRecord.objects.filter(club=club,status="open").count()})

def api_members(request):
    key=authenticate_api_request(request,"members:read")
    if not key: return JsonResponse({"detail":"معتبر نیست یا دسترسی کافی ندارد"},status=401)
    rows=Member.objects.filter(club=key.club).order_by("id")
    q=request.GET.get("q","").strip()
    if q: rows=rows.filter(mobile__icontains=q)
    return JsonResponse({"results":[{"id":m.pk,"code":m.member_code,"name":m.full_name,"mobile":m.mobile,"status":m.status} for m in rows[:100] ],"limit":100})
