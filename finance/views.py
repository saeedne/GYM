from datetime import timedelta
import jdatetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from core.models import AuditLog
from .forms import CashAccountForm, CategoryForm, FinanceEntryForm
from .models import CashAccount, FinanceCategory, FinanceEntry


@login_required
def dashboard(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    today = timezone.localdate()
    month_start = today.replace(day=1)
    qs = FinanceEntry.objects.filter(club=club)
    month = qs.filter(occurred_on__gte=month_start, occurred_on__lte=today)
    income = month.filter(entry_type="income").aggregate(total=Sum("amount"))["total"] or 0
    expense = month.filter(entry_type="expense").aggregate(total=Sum("amount"))["total"] or 0
    all_income = qs.filter(entry_type="income").aggregate(total=Sum("amount"))["total"] or 0
    all_expense = qs.filter(entry_type="expense").aggregate(total=Sum("amount"))["total"] or 0
    return render(request, "finance/dashboard.html", {
        "club": club, "month_income": income, "month_expense": expense,
        "month_net": income - expense, "net_balance": all_income - all_expense + sum(a.opening_balance for a in CashAccount.objects.filter(club=club, is_active=True)),
        "items": qs.select_related("branch", "category", "account")[:20],
        "accounts": CashAccount.objects.filter(club=club, is_active=True),
    })


@login_required
def entry_create(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = FinanceEntryForm(request.POST or None, club=club, user=request.user)
    if request.method == "POST" and form.is_valid():
        entry = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="FinanceEntry", object_id=str(entry.pk), description=f"سند مالی {entry.amount} ریال ثبت شد.")
        messages.success(request, "سند مالی ثبت شد.")
        return redirect("finance:dashboard")
    return render(request, "finance/entry_form.html", {"club": club, "form": form})


@login_required
def account_list(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = CashAccountForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "صندوق/حساب ثبت شد.")
        return redirect("finance:accounts")
    accounts = CashAccount.objects.filter(club=club)
    return render(request, "finance/accounts.html", {"club": club, "form": form, "accounts": accounts})

@login_required
def account_edit(request, pk):
    club=request.active_club
    item=get_object_or_404(CashAccount, club=club, pk=pk)
    form=CashAccountForm(request.POST or None, instance=item, club=club)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "حساب مالی به‌روزرسانی شد.")
        return redirect("finance:accounts")
    return render(request, "finance/accounts.html", {"club":club,"form":form,"accounts":CashAccount.objects.filter(club=club),"editing":item})


@login_required
@require_POST
def account_delete(request, pk):
    item = get_object_or_404(CashAccount, club=request.active_club, pk=pk)
    if item.entries.exists():
        messages.error(request, "این صندوق سند مالی دارد و برای حفظ سوابق حذف نمی‌شود؛ آن را غیرفعال کنید.")
    else:
        item.delete()
        messages.success(request, "صندوق/حساب حذف شد.")
    return redirect("finance:accounts")


@login_required
def category_list(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = CategoryForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "دسته مالی ثبت شد.")
        return redirect("finance:categories")
    return render(request, "finance/categories.html", {"club": club, "form": form, "items": FinanceCategory.objects.filter(club=club)})

@login_required
def category_edit(request, pk):
    club=request.active_club
    item=get_object_or_404(FinanceCategory, club=club, pk=pk)
    form=CategoryForm(request.POST or None, instance=item, club=club)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "دسته مالی به‌روزرسانی شد.")
        return redirect("finance:categories")
    return render(request, "finance/categories.html", {"club":club,"form":form,"items":FinanceCategory.objects.filter(club=club),"editing":item})


@login_required
@require_POST
def category_delete(request, pk):
    item = get_object_or_404(FinanceCategory, club=request.active_club, pk=pk)
    if item.entries.exists():
        messages.error(request, "این دسته برای اسناد مالی استفاده شده و حذف نمی‌شود؛ آن را غیرفعال کنید.")
    else:
        item.delete()
        messages.success(request, "دسته مالی حذف شد.")
    return redirect("finance:categories")


@login_required
def report(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    qs = FinanceEntry.objects.filter(club=club).select_related("category", "account", "branch")
    start, end = request.GET.get("from", ""), request.GET.get("to", "")
    try:
        if start:
            y,m,d = map(int, start.replace("-", "/").split("/")[:3])
            qs = qs.filter(occurred_on__gte=jdatetime.date(y,m,d).togregorian())
        if end:
            y,m,d = map(int, end.replace("-", "/").split("/")[:3])
            qs = qs.filter(occurred_on__lt=jdatetime.date(y,m,d).togregorian()+timedelta(days=1))
    except (ValueError, TypeError):
        messages.error(request, "بازه تاریخ شمسی معتبر نیست.")
    income = qs.filter(entry_type="income").aggregate(total=Sum("amount"))["total"] or 0
    expense = qs.filter(entry_type="expense").aggregate(total=Sum("amount"))["total"] or 0
    page = Paginator(qs, 40).get_page(request.GET.get("page"))
    return render(request, "finance/report.html", {"club": club, "items": page, "page_obj": page, "income": income, "expense": expense, "net": income-expense, "from_date": start, "to_date": end})
