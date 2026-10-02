from django.db import migrations


def backfill_revenue(apps, schema_editor):
    alias = schema_editor.connection.alias
    Entry = apps.get_model("finance", "FinanceEntry")
    Account = apps.get_model("finance", "CashAccount")
    Category = apps.get_model("finance", "FinanceCategory")

    def post(club_id, branch_id, amount, day, description, source, source_id, category_name):
        if not amount:
            return
        account = Account.objects.using(alias).filter(club_id=club_id, is_active=True).first()
        category = Category.objects.using(alias).filter(club_id=club_id, entry_type="income", name=category_name).first()
        Entry.objects.using(alias).get_or_create(
            club_id=club_id, source=source, source_id=str(source_id),
            defaults={
                "branch_id": branch_id, "account_id": account.pk if account else None,
                "category_id": category.pk if category else None, "entry_type": "income",
                "amount": amount, "occurred_on": day, "description": description,
            },
        )

    Payment = apps.get_model("membership", "Payment")
    for payment in Payment.objects.using(alias).filter(status="paid").select_related("member"):
        post(payment.club_id, payment.branch_id, payment.amount, payment.paid_on,
             "پرداخت عضویت", "membership_payment", payment.pk, "درآمد عضویت")

    Sale = apps.get_model("store", "StoreSale")
    for sale in Sale.objects.using(alias).select_related("product"):
        post(sale.club_id, sale.branch_id, sale.quantity * sale.unit_price, sale.sold_at.date(),
             "فروش فروشگاه", "store_sale", sale.pk, "فروش فروشگاه")

    Order = apps.get_model("cafe", "CafeOrder")
    for order in Order.objects.using(alias).filter(status="served").select_related("menu_item"):
        post(order.club_id, order.branch_id, order.quantity * order.unit_price, order.ordered_at.date(),
             "فروش کافی‌شاپ", "cafe_order", order.pk, "فروش کافی‌شاپ")


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),
        ("membership", "0001_initial"),
        ("store", "0001_initial"),
        ("cafe", "0001_initial"),
    ]
    operations = [migrations.RunPython(backfill_revenue, migrations.RunPython.noop)]
