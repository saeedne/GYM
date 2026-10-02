from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
import re
from members.models import Member
from .forms import ClubRoleForm, ClubUserAssignmentForm, ClubUserCreateForm, ClubUserProfileForm
from .models import ClubMembership, ClubRole

class GymLoginView(LoginView):
    template_name = "registration/login.html"
    def get_success_url(self):
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        is_mobile = bool(re.search(r"android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile", user_agent, re.I))
        if not is_mobile:
            return super().get_success_url()
        webapp_membership = ClubMembership.objects.filter(user=self.request.user, is_active=True, webapp_enabled=True, club__status="active").select_related("club").order_by("club__name").first()
        if webapp_membership:
            self.request.session["active_club_id"] = webapp_membership.club_id
            return "/mobile/"
        return super().get_success_url()

def _require_club_permission(request, codename):
    membership = getattr(request, "club_membership", None)
    if request.user.is_superuser or (membership and membership.is_active and membership.is_manager):
        return
    if membership and membership.is_active and membership.direct_permissions.filter(codename=codename, content_type__app_label="accounts").exists():
        return
    if (membership and membership.is_active and membership.club_role_id
            and membership.club_role.is_active and membership.club_role.club_id == membership.club_id
            and membership.club_role.permissions.filter(codename=codename, content_type__app_label="accounts").exists()):
        return
    raise PermissionDenied("نقش شما اجازه‌ی انجام این عملیات را در باشگاه فعال نمی‌دهد.")

@login_required
def user_list(request):
    _require_club_permission(request, "view_users")
    rows = ClubMembership.objects.filter(club=request.active_club).select_related("user", "branch", "club_role").order_by("user__username")
    return render(request, "accounts/users.html", {"memberships": rows})

@login_required
@require_http_methods(["GET", "POST"])
def user_create(request):
    _require_club_permission(request, "add_users")
    form = ClubUserCreateForm(request.POST or None, club=request.active_club)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"کاربر «{user.display_name or user.username}» ساخته شد.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": "تعریف کاربر جدید"})

@login_required
@require_http_methods(["GET", "POST"])
def user_edit(request, pk):
    _require_club_permission(request, "change_users")
    membership = get_object_or_404(ClubMembership.objects.select_related("user"), club=request.active_club, pk=pk)
    form = ClubUserProfileForm(request.POST or None, user=membership.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "مشخصات کاربر به‌روزرسانی شد.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": f"ویرایش مشخصات: {membership.user}"})

@login_required
@require_http_methods(["GET", "POST"])
def user_access_edit(request, pk):
    _require_club_permission(request, "change_users")
    membership = get_object_or_404(ClubMembership.objects.select_related("user"), club=request.active_club, pk=pk)
    form = ClubUserAssignmentForm(request.POST or None, instance=membership, club=request.active_club)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.role = updated.club_role.name if updated.club_role else ("مدیر باشگاه" if updated.is_manager else "")
        updated.save()
        form.save_m2m()
        member = form.cleaned_data.get("member_profile")
        trainer = form.cleaned_data.get("trainer_profile")
        Member.objects.filter(club=request.active_club, user=updated.user).exclude(pk=member.pk if member else None).update(user=None)
        from trainers.models import Trainer
        Trainer.objects.filter(club=request.active_club, user=updated.user).exclude(pk=trainer.pk if trainer else None).update(user=None)
        if member:
            member.user = updated.user
            member.save(update_fields=["user"])
        if trainer:
            trainer.user = updated.user
            trainer.save(update_fields=["user"])
        messages.success(request, "دسترسی کاربر به‌روزرسانی شد.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": f"دسترسی: {membership.user}"})


@login_required
@require_http_methods(["POST"])
def user_membership_delete(request, pk):
    _require_club_permission(request, "delete_users")
    membership = get_object_or_404(ClubMembership, club=request.active_club, pk=pk)
    if membership.is_manager:
        messages.error(request, "عضویت مدیر را از این صفحه حذف نکنید؛ ابتدا نقش مدیریتی را تغییر دهید.")
    else:
        name = membership.user.display_name or membership.user.username
        membership.delete()
        messages.success(request, f"دسترسی «{name}» به این باشگاه حذف شد.")
    return redirect("accounts:user_list")

@login_required
def role_list(request):
    _require_club_permission(request, "view_users")
    return render(request, "accounts/roles.html", {"roles": ClubRole.objects.filter(club=request.active_club).prefetch_related("permissions")})

@login_required
@require_http_methods(["GET", "POST"])
def role_create(request):
    _require_club_permission(request, "add_users")
    form = ClubRoleForm(request.POST or None, club=request.active_club)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "نقش و دسترسی‌های آن ذخیره شد.")
        return redirect("accounts:role_list")
    return render(request, "accounts/role_form.html", {"form": form, "title": "تعریف نقش دسترسی"})

@login_required
@require_http_methods(["GET", "POST"])
def role_edit(request, pk):
    _require_club_permission(request, "change_users")
    role = get_object_or_404(ClubRole, club=request.active_club, pk=pk)
    form = ClubRoleForm(request.POST or None, instance=role, club=request.active_club)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "نقش و دسترسی‌های آن به‌روزرسانی شد.")
        return redirect("accounts:role_list")
    return render(request, "accounts/role_form.html", {"form": form, "title": f"ویرایش نقش: {role.name}"})


@login_required
@require_http_methods(["POST"])
def role_delete(request, pk):
    _require_club_permission(request, "delete_users")
    role = get_object_or_404(ClubRole, club=request.active_club, pk=pk)
    name = role.name
    role.assignments.update(club_role=None, role="")
    role.delete()
    messages.success(request, f"نقش «{name}» حذف شد.")
    return redirect("accounts:role_list")
