from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from core.models import AuditLog
from .forms import ProductForm, SaleForm, StockForm
from .models import InventoryMovement, Product, StoreSale
from finance.models import CashAccount, FinanceCategory
from finance.services import record_income


@login_required
def dashboard(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    products = Product.objects.filter(club=club, is_active=True)
    sales = StoreSale.objects.filter(club=club)
    return render(request, "store/dashboard.html", {
        "club": club, "products": products.order_by("name"),
        "low_stock": products.filter(stock_quantity__lte=F("min_stock")).count(),
        "sales_count": sales.count(),
        "sales_total": sales.aggregate(total=Sum(F("quantity") * F("unit_price")))["total"] or 0,
    })


@login_required
def product_create(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = ProductForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="StoreProduct", object_id=str(item.pk), description=f"کالای {item.name} ثبت شد.")
        messages.success(request, "کالا ثبت شد.")
        return redirect("store:dashboard")
    return render(request, "store/product_form.html", {"club": club, "form": form})

@login_required
def product_edit(request, pk):
    club = request.active_club
    item = get_object_or_404(Product, club=club, pk=pk)
    form = ProductForm(request.POST or None, instance=item, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="update", model_name="StoreProduct", object_id=str(item.pk), description=f"کالای {item.name} ویرایش شد.")
        messages.success(request, "کالا به‌روزرسانی شد.")
        return redirect("store:dashboard")
    return render(request, "store/product_form.html", {"club": club, "form": form, "title": "ویرایش کالا"})


@login_required
@require_POST
def product_delete(request, pk):
    item = get_object_or_404(Product, club=request.active_club, pk=pk)
    name = item.name
    try:
        item.delete()
    except ProtectedError:
        messages.error(request, "این کالا در فروش یا گردش انبار استفاده شده است و حذف نمی‌شود؛ آن را غیرفعال کنید.")
    else:
        messages.success(request, f"کالای «{name}» حذف شد.")
    return redirect("store:dashboard")


@login_required
def stock_adjust(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = StockForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.cleaned_data["product"]
        amount = form.cleaned_data["quantity"]
        if form.cleaned_data["movement_type"] == "out" and item.stock_quantity < amount:
            form.add_error("quantity", "موجودی کافی نیست.")
        else:
            with transaction.atomic():
                item = Product.objects.select_for_update().get(pk=item.pk, club=club)
                change = amount if form.cleaned_data["movement_type"] == "in" else -amount
                if item.stock_quantity + change < 0:
                    form.add_error("quantity", "موجودی کافی نیست.")
                else:
                    item.stock_quantity += change
                    item.save(update_fields=["stock_quantity"])
                    InventoryMovement.objects.create(club=club, product=item, movement_type=form.cleaned_data["movement_type"], quantity=amount, reason=form.cleaned_data["reason"], created_by=request.user)
                    messages.success(request, "گردش موجودی ثبت شد.")
                    return redirect("store:dashboard")
    return render(request, "store/stock_form.html", {"club": club, "form": form})


@login_required
def sell(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = SaleForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=data["product"].pk, club=club)
                if product.stock_quantity < data["quantity"]:
                    form.add_error("quantity", "موجودی کافی نیست.")
                else:
                    product.stock_quantity -= data["quantity"]
                    product.save(update_fields=["stock_quantity"])
                    sale = StoreSale.objects.create(club=club, branch=data["branch"], product=product, member=data["member"], quantity=data["quantity"], unit_price=product.sale_price, received_by=request.user)
                    record_income(
                        club=club, amount=sale.total, description=f"فروش فروشگاه: {product.name}",
                        source="store_sale", source_id=sale.pk, branch=sale.branch,
                        account=CashAccount.objects.filter(club=club, is_active=True).first(),
                        category=FinanceCategory.objects.filter(club=club, entry_type="income", name="فروش فروشگاه").first(),
                        user=request.user,
                    )
                    InventoryMovement.objects.create(club=club, product=product, movement_type="out", quantity=sale.quantity, reason=f"فروش #{sale.pk}", created_by=request.user)
                    AuditLog.objects.create(club=club, user=request.user, action="create", model_name="StoreSale", object_id=str(sale.pk), description=f"فروش {product.name} به مبلغ {sale.total} ریال.")
                    messages.success(request, f"فروش ثبت شد: {sale.total:,} ریال")
                    return redirect("store:dashboard")
        except Product.DoesNotExist:
            form.add_error("product", "کالا در این باشگاه پیدا نشد.")
    return render(request, "store/sale_form.html", {"club": club, "form": form})


@login_required
def sales(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    qs = StoreSale.objects.filter(club=club).select_related("product", "member", "branch", "received_by")
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    return render(request, "store/sales.html", {"club": club, "items": page, "page_obj": page})
