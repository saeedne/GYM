from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from core.models import AuditLog
from members.models import Member
from .forms import ContractForm, MembershipPlanForm, PaymentForm
from .models import MembershipContract, MembershipPlan, Payment
from finance.models import CashAccount, FinanceCategory
from finance.services import record_income


def _club(request):
    return request.active_club


def _page(request, qs, template, context):
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, template, {**context, "page_obj": page, "items": page})


@login_required
def plan_list(request):
    club = _club(request)
    if not club: return redirect("dashboard")
    plans = MembershipPlan.objects.filter(club=club)
    if request.method == "POST":
        form = MembershipPlanForm(request.POST, club=club)
        if form.is_valid():
            obj = form.save()
            AuditLog.objects.create(club=club, user=request.user, action="create", model_name="MembershipPlan", object_id=str(obj.pk), description=f"پلن «{obj.name}» ایجاد شد.")
            messages.success(request, "پلن ثبت شد.")
            return redirect("membership:plans")
    else:
        form = MembershipPlanForm(club=club)
    return render(request, "membership/plans.html", {"club": club, "plans": plans, "form": form})


@login_required
def plan_edit(request, pk):
    club = _club(request)
    plan = get_object_or_404(MembershipPlan, club=club, pk=pk)
    form = MembershipPlanForm(request.POST or None, instance=plan, club=club)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="update", model_name="MembershipPlan", object_id=str(obj.pk), description=f"پلن «{obj.name}» ویرایش شد.")
        messages.success(request, "پلن به‌روزرسانی شد.")
        return redirect("membership:plans")
    return render(request, "membership/plan_form.html", {"club": club, "form": form, "title": "ویرایش پلن"})


@login_required
@require_POST
def plan_delete(request, pk):
    club = _club(request)
    plan = get_object_or_404(MembershipPlan, club=club, pk=pk)
    name = plan.name
    try:
        plan.delete()
    except ProtectedError:
        messages.error(request, "برای حفظ قراردادهای ثبت‌شده، پلنِ استفاده‌شده حذف نمی‌شود؛ آن را غیرفعال کنید.")
    else:
        AuditLog.objects.create(club=club, user=request.user, action="delete", model_name="MembershipPlan", object_id=str(pk), description=f"پلن «{name}» حذف شد.")
        messages.success(request, f"پلن «{name}» حذف شد.")
    return redirect("membership:plans")


@login_required
def contract_list(request):
    club = _club(request)
    if not club: return redirect("dashboard")
    qs = MembershipContract.objects.filter(club=club).select_related("member", "plan", "branch")
    return _page(request, qs, "membership/contracts.html", {"club": club})


@login_required
def contract_create(request):
    club = _club(request)
    if not club: return redirect("dashboard")
    form = ContractForm(request.POST or None, club=club, user=request.user)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="MembershipContract", object_id=str(obj.pk), description=f"قرارداد {obj.contract_code} ایجاد شد.")
        messages.success(request, "قرارداد ثبت شد.")
        return redirect("membership:contracts")
    return render(request, "membership/contract_form.html", {"club": club, "form": form, "title": "ثبت قرارداد"})


@login_required
def contract_edit(request, pk):
    club = _club(request)
    obj = get_object_or_404(MembershipContract, club=club, pk=pk)
    form = ContractForm(request.POST or None, instance=obj, club=club, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        AuditLog.objects.create(club=club, user=request.user, action="update", model_name="MembershipContract", object_id=str(obj.pk), description=f"قرارداد {obj.contract_code} ویرایش شد.")
        messages.success(request, "قرارداد ویرایش شد.")
        return redirect("membership:contracts")
    return render(request, "membership/contract_form.html", {"club": club, "form": form, "title": "ویرایش قرارداد"})


@login_required
@require_POST
def contract_delete(request, pk):
    club = _club(request)
    obj = get_object_or_404(MembershipContract, club=club, pk=pk)
    code = obj.contract_code
    try:
        obj.delete()
    except ProtectedError:
        messages.error(request, "این قرارداد پرداخت ثبت‌شده دارد و برای حفظ سوابق مالی حذف نمی‌شود.")
    else:
        AuditLog.objects.create(club=club, user=request.user, action="delete", model_name="MembershipContract", object_id=str(pk), description=f"قرارداد {code} حذف شد.")
        messages.success(request, f"قرارداد {code} حذف شد.")
    return redirect("membership:contracts")


@login_required
def payment_list(request):
    club = _club(request)
    if not club: return redirect("dashboard")
    qs = Payment.objects.filter(club=club).select_related("member", "contract", "branch")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(member__first_name__icontains=q) | qs.filter(member__last_name__icontains=q) | qs.filter(reference__icontains=q)
    total = Payment.objects.filter(club=club, status="paid").aggregate(total=Sum("amount"))["total"] or 0
    return _page(request, qs, "membership/payments.html", {"club": club, "q": q, "total": total})


@login_required
def payment_create(request):
    club = _club(request)
    if not club: return redirect("dashboard")
    member_id = request.GET.get("member")
    initial = {"member": member_id} if member_id and Member.objects.filter(club=club, pk=member_id).exists() else {}
    form = PaymentForm(request.POST or None, club=club, user=request.user, initial=initial)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        if obj.status == "paid":
            record_income(
                club=club, amount=obj.amount, description=f"پرداخت عضویت {obj.member.full_name}",
                source="membership_payment", source_id=obj.pk, branch=obj.branch,
                account=CashAccount.objects.filter(club=club, is_active=True).first(),
                category=FinanceCategory.objects.filter(club=club, entry_type="income", name="درآمد عضویت").first(),
                user=request.user, occurred_on=obj.paid_on,
            )
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="Payment", object_id=str(obj.pk), description=f"پرداخت {obj.amount} ریال برای {obj.member} ثبت شد.")
        messages.success(request, "پرداخت ثبت شد.")
        return redirect("membership:payments")
    return render(request, "membership/payment_form.html", {"club": club, "form": form, "title": "ثبت پرداخت"})


@login_required
@require_POST
def contract_renew(request, pk):
    club = _club(request)
    old = get_object_or_404(MembershipContract, club=club, pk=pk)
    from datetime import timedelta
    start = max(timezone.localdate(), old.end_date + timedelta(days=1))
    code = f"{old.contract_code}-R{old.pk}-{MembershipContract.objects.filter(club=club).count()+1}"
    new = MembershipContract.objects.create(club=club, branch=old.branch, member=old.member, plan=old.plan, contract_code=code, start_date=start, end_date=start + timedelta(days=old.plan.duration_days - 1), agreed_price=old.plan.price, created_by=request.user)
    messages.success(request, f"قرارداد تمدید شد: {new.contract_code}")
    return redirect("membership:contracts")
