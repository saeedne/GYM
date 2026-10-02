from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.models import ClubMembership
from members.models import Member
from .models import AuditLog


@login_required
def dashboard(request):
    club = request.active_club
    if not club:
        return render(request, "dashboard.html", {"no_club": True})

    members_count = Member.objects.filter(club=club).count()
    active_members = Member.objects.filter(club=club, status="active").count()
    branch_count = club.branches.filter(is_active=True).count()

    return render(request, "dashboard.html", {
        "club": club,
        "members_count": members_count,
        "active_members": active_members,
        "branch_count": branch_count,
    })


@login_required
@require_POST
def switch_club(request):
    club_id = request.POST.get("club_id")
    membership = (
        ClubMembership.objects
        .select_related("club")
        .filter(user=request.user, club_id=club_id, is_active=True, club__status="active")
        .first()
    )
    if not membership:
        messages.error(request, "دسترسی شما به این باشگاه وجود ندارد.")
        return redirect("dashboard")

    request.session["active_club_id"] = membership.club_id
    AuditLog.objects.create(
        club=membership.club,
        user=request.user,
        action="switch_club",
        description=f"باشگاه فعال به «{membership.club.name}» تغییر کرد.",
    )
    return redirect("dashboard")
