from accounts.models import ClubMembership

def club_context(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"active_club": None, "available_clubs": [], "club_permissions": []}

    memberships = (
        ClubMembership.objects
        .select_related("club")
        .filter(user=request.user, is_active=True, club__status="active")
        .order_by("club__name")
    )
    club_membership = getattr(request, "club_membership", None)
    club_permissions = []
    if club_membership and club_membership.is_active:
        club_permissions = ["all"] if (club_membership.is_manager or request.user.is_superuser) else list(
            club_membership.club_role.permissions.values_list("codename", flat=True)
        ) if (club_membership.club_role_id and club_membership.club_role.is_active and club_membership.club_role.club_id == club_membership.club_id) else []
        if club_membership and club_membership.is_active and club_permissions != ["all"]:
            club_permissions = sorted(set(club_permissions) | set(club_membership.direct_permissions.values_list("codename", flat=True)))
    return {
        "active_club": getattr(request, "active_club", None),
        "available_clubs": [m.club for m in memberships],
        "club_permissions": club_permissions,
    }
