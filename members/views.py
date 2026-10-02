from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from core.models import AuditLog
from .forms import MemberForm
from .models import Member
from membership.models import MembershipContract, Payment
from attendance.models import AttendanceRecord


def _club(request):
    return request.active_club


@login_required
def member_list(request):
    club = _club(request)
    if not club:
        return redirect("dashboard")

    q = request.GET.get("q", "").strip()
    qs = Member.objects.filter(club=club).select_related("branch")
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(member_code__icontains=q) |
            Q(mobile__icontains=q) |
            Q(national_id__icontains=q)
        )

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "members/list.html", {
        "members": page_obj,
        "page_obj": page_obj,
        "q": q,
        "club": club,
    })


@login_required
def member_create(request):
    club = _club(request)
    if not club:
        return redirect("dashboard")

    if request.method == "POST":
        form = MemberForm(request.POST, request.FILES, club=club)
        if form.is_valid():
            member = form.save()
            AuditLog.objects.create(
                club=club, user=request.user, action="create",
                model_name="Member", object_id=str(member.pk),
                description=f"عضو «{member.full_name}» ایجاد شد.",
            )
            messages.success(request, "عضو با موفقیت ثبت شد.")
            return redirect("member_detail", pk=member.pk)
    else:
        form = MemberForm(club=club)

    return render(request, "members/form.html", {"form": form, "title": "ثبت عضو جدید", "club": club})


@login_required
def member_detail(request, pk):
    club = _club(request)
    member = get_object_or_404(Member.objects.select_related("branch"), pk=pk, club=club)
    contracts = MembershipContract.objects.filter(club=club, member=member).select_related("plan")
    payments = Payment.objects.filter(club=club, member=member).select_related("contract")[:10]
    visits = AttendanceRecord.objects.filter(club=club, member=member)[:10]
    return render(request, "members/detail.html", {"member": member, "club": club, "contracts": contracts, "payments": payments, "visits": visits})


@login_required
def member_edit(request, pk):
    club = _club(request)
    member = get_object_or_404(Member, pk=pk, club=club)

    if request.method == "POST":
        form = MemberForm(request.POST, request.FILES, instance=member, club=club)
        if form.is_valid():
            member = form.save()
            AuditLog.objects.create(
                club=club, user=request.user, action="update",
                model_name="Member", object_id=str(member.pk),
                description=f"عضو «{member.full_name}» ویرایش شد.",
            )
            messages.success(request, "اطلاعات عضو ویرایش شد.")
            return redirect("member_detail", pk=member.pk)
    else:
        form = MemberForm(instance=member, club=club)

    return render(request, "members/form.html", {"form": form, "title": "ویرایش عضو", "club": club, "member": member})


@login_required
def member_delete(request, pk):
    club = _club(request)
    member = get_object_or_404(Member, pk=pk, club=club)

    if request.method == "POST":
        name = member.full_name
        try:
            member.delete()
        except ProtectedError:
            messages.error(request, "این عضو سوابق قرارداد، پرداخت، حضور یا رزرو دارد و قابل حذف نیست. برای نگهداری سوابق، وضعیت عضو را غیرفعال کنید.")
            return redirect("member_list")
        AuditLog.objects.create(
            club=club, user=request.user, action="delete",
            model_name="Member", object_id=str(pk),
            description=f"عضو «{name}» حذف شد.",
        )
        messages.success(request, "عضو حذف شد.")
        return redirect("member_list")

    return render(request, "members/delete.html", {"member": member, "club": club})
