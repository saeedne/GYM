from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST
from core.models import AuditLog
from .forms import CafeOrderForm, MenuItemForm
from .models import CafeOrder, MenuItem
from finance.models import CashAccount, FinanceCategory
from finance.services import record_income


@login_required
def dashboard(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    items = MenuItem.objects.filter(club=club)
    orders = CafeOrder.objects.filter(club=club).select_related("member", "menu_item", "branch")
    page = Paginator(orders, 30).get_page(request.GET.get("page"))
    return render(request, "cafe/dashboard.html", {"club": club, "menu": items, "orders": page})


@login_required
def menu_item_create(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = MenuItemForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="CafeMenuItem", object_id=str(item.pk), description=f"محصول منو {item.name} ثبت شد.")
        messages.success(request, "محصول به منو افزوده شد.")
        return redirect("cafe:dashboard")
    return render(request, "cafe/menu_form.html", {"club": club, "form": form})

@login_required
def menu_item_edit(request, pk):
    club = request.active_club
    item = get_object_or_404(MenuItem, club=club, pk=pk)
    form = MenuItemForm(request.POST or None, instance=item, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="update", model_name="CafeMenuItem", object_id=str(item.pk), description=f"محصول منو {item.name} ویرایش شد.")
        messages.success(request, "آیتم منو به‌روزرسانی شد.")
        return redirect("cafe:dashboard")
    return render(request, "cafe/menu_form.html", {"club": club, "form": form, "title": "ویرایش آیتم منو"})


@login_required
@require_POST
def menu_item_delete(request, pk):
    item = get_object_or_404(MenuItem, club=request.active_club, pk=pk)
    name = item.name
    try:
        item.delete()
    except ProtectedError:
        messages.error(request, "این آیتم در سفارش‌های ثبت‌شده استفاده شده و حذف نمی‌شود؛ آن را ناموجود کنید.")
    else:
        messages.success(request, f"آیتم «{name}» حذف شد.")
    return redirect("cafe:dashboard")


@login_required
def order_create(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = CafeOrderForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        order = form.save(commit=False)
        order.club, order.created_by = club, request.user
        order.unit_price = order.menu_item.price
        order.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="CafeOrder", object_id=str(order.pk), description=f"سفارش {order.menu_item.name} به مبلغ {order.total} ریال.")
        messages.success(request, "سفارش ثبت شد.")
        return redirect("cafe:dashboard")
    return render(request, "cafe/order_form.html", {"club": club, "form": form})


@login_required
@require_POST
def order_status(request, pk, status):
    club = request.active_club
    order = get_object_or_404(CafeOrder, club=club, pk=pk)
    if status in dict(CafeOrder.STATUS):
        was_served = order.status == "served"
        order.status = status
        order.save(update_fields=["status"])
        if status == "served" and not was_served:
            record_income(
                club=club, amount=order.total, description=f"فروش کافی‌شاپ: {order.menu_item.name}",
                source="cafe_order", source_id=order.pk, branch=order.branch,
                account=CashAccount.objects.filter(club=club, is_active=True).first(),
                category=FinanceCategory.objects.filter(club=club, entry_type="income", name="فروش کافی‌شاپ").first(),
                user=request.user,
            )
        messages.success(request, "وضعیت سفارش به‌روز شد.")
    return redirect("cafe:dashboard")
