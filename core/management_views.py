from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import BranchForm, ClubForm
from .models import Branch, Club


def _require_superuser(request):
    if not request.user.is_superuser:
        raise PermissionDenied("مدیریت باشگاه‌ها فقط در اختیار مدیر کل سامانه است.")


@login_required
def club_management(request):
    _require_superuser(request)
    return render(request, "core/club_management.html", {"clubs": Club.objects.prefetch_related("branches")})


@login_required
@require_http_methods(["GET", "POST"])
def club_form(request, pk=None):
    _require_superuser(request)
    instance = get_object_or_404(Club, pk=pk) if pk else None
    form = ClubForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        club = form.save()
        if instance is None:
            from accounts.models import ClubMembership
            ClubMembership.objects.update_or_create(
                user=request.user, club=club,
                defaults={"role": "مدیر باشگاه", "is_manager": True, "is_active": True},
            )
            request.session["active_club_id"] = club.pk
        messages.success(request, "اطلاعات باشگاه ذخیره شد.")
        return redirect("club_management")
    return render(request, "core/club_form.html", {"form": form, "title": "ویرایش باشگاه" if instance else "ثبت باشگاه جدید"})


@login_required
@require_POST
def club_delete(request, pk):
    _require_superuser(request)
    club = get_object_or_404(Club, pk=pk)
    club_name = club.name
    try:
        club.delete()
        messages.success(request, f"باشگاه «{club_name}» و تمام اطلاعات وابسته حذف شد.")
    except ProtectedError:
        messages.error(request, "این باشگاه دارای سوابق محافظت‌شده است و حذف نشد. ابتدا سوابق وابسته را بررسی کنید.")
    return redirect("club_management")


@login_required
@require_http_methods(["GET", "POST"])
def branch_form(request, club_pk, pk=None):
    _require_superuser(request)
    club = get_object_or_404(Club, pk=club_pk)
    instance = get_object_or_404(Branch, pk=pk, club=club) if pk else None
    form = BranchForm(request.POST or None, instance=instance, club=club)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "اطلاعات شعبه ذخیره شد.")
        return redirect("club_management")
    title = f"ویرایش شعبه: {instance.name}" if instance else f"شعبه جدید برای {club.name}"
    return render(request, "core/branch_form.html", {"form": form, "title": title, "club": club})


@login_required
@require_POST
def branch_delete(request, club_pk, pk):
    _require_superuser(request)
    branch = get_object_or_404(Branch, pk=pk, club_id=club_pk)
    name = branch.name
    try:
        branch.delete()
        messages.success(request, f"شعبه «{name}» حذف شد.")
    except ProtectedError:
        messages.error(request, "این شعبه به سوابق عملیاتی متصل است؛ به‌جای حذف، آن را غیرفعال کنید.")
    return redirect("club_management")
