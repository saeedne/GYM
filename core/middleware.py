from django.utils.deprecation import MiddlewareMixin
from .models import Club
from accounts.models import ClubMembership


class ActiveClubMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.active_club = None
        request.club_membership = None

        if not request.user.is_authenticated:
            return

        club_id = request.session.get("active_club_id")
        membership = None

        if club_id:
            membership = (
                ClubMembership.objects
                .select_related("club", "club_role")
                .filter(user=request.user, club_id=club_id, is_active=True)
                .first()
            )

        if membership:
            request.club_membership = membership
            request.active_club = membership.club
            return

        first_membership = (
            ClubMembership.objects
            .select_related("club", "club_role")
            .filter(user=request.user, is_active=True, club__status="active")
            .order_by("club__name")
            .first()
        )
        if first_membership:
            request.club_membership = first_membership
            request.active_club = first_membership.club
            request.session["active_club_id"] = first_membership.club_id
