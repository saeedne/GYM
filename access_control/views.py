import secrets
from datetime import datetime, time, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from core.models import AuditLog
from .forms import AccessPolicyForm, CredentialForm, GuestPassForm
from .models import AccessCredential, AccessPolicy, GuestPass


def _club(request):
    return request.active_club


@login_required
def credentials(request):
    club = _club(request)
    if not club:
        return redirect("dashboard")
    form = CredentialForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="AccessCredential", object_id=str(item.pk), description=f"شناسه ورود برای {item.member} ثبت شد.")
        messages.success(request, "شناسه ورود ثبت شد.")
        return redirect("access_control:credentials")
    items = AccessCredential.objects.filter(club=club).select_related("member")
    return render(request, "access_control/credentials.html", {"club": club, "form": form, "items": items})


@login_required
@require_POST
def credential_toggle(request, pk):
    club = _club(request)
    item = get_object_or_404(AccessCredential, club=club, pk=pk)
    item.is_active = not item.is_active
    item.save(update_fields=["is_active"])
    messages.success(request, "وضعیت شناسه تغییر کرد.")
    return redirect("access_control:credentials")


@login_required
def policy(request):
    club = _club(request)
    if not club:
        return redirect("dashboard")
    instance, _ = AccessPolicy.objects.get_or_create(club=club)
    form = AccessPolicyForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "قوانین دسترسی ذخیره شد.")
        return redirect("access_control:policy")
    return render(request, "access_control/policy.html", {"club": club, "form": form})


@login_required
def guests(request):
    club = _club(request)
    if not club:
        return redirect("dashboard")
    form = GuestPassForm(request.POST or None, club=club, initial={"valid_on": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="GuestPass", object_id=str(item.pk), description=f"مجوز مهمان {item.guest_name} ایجاد شد.")
        messages.success(request, f"مجوز مهمان صادر شد. کد: {item.pass_code}")
        return redirect("access_control:guests")
    items = GuestPass.objects.filter(club=club).select_related("host_member", "branch")
    page = Paginator(items, 25).get_page(request.GET.get("page"))
    return render(request, "access_control/guests.html", {"club": club, "form": form, "items": page})


@login_required
@require_POST
def guest_checkin(request, pk):
    club = _club(request)
    item = get_object_or_404(GuestPass, club=club, pk=pk)
    if item.status != "issued" or item.valid_on != timezone.localdate():
        messages.error(request, "مجوز مهمان معتبر یا قابل استفاده نیست.")
    else:
        item.status = "used"
        item.checked_in_at = timezone.now()
        item.save(update_fields=["status", "checked_in_at"])
        messages.success(request, f"ورود مهمان {item.guest_name} ثبت شد.")
    return redirect("access_control:guests")


@login_required
@require_POST
def guest_create_token(request):
    club = _club(request)
    guest = get_object_or_404(GuestPass, club=club, pk=request.POST.get("guest_id"), status="issued", valid_on=timezone.localdate())
    messages.info(request, f"کد مهمان: {guest.pass_code}")
    return redirect("access_control:guests")
