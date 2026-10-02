from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from core.models import Branch, Club, ClubModule, SystemModule
from accounts.models import ClubMembership
from members.models import Member
from membership.models import MembershipContract, MembershipPlan, Payment
from access_control.models import AccessCredential
from trainers.models import Trainer, FitnessClass
from store.models import Product
from cafe.models import MenuItem
from workouts.models import Exercise, WorkoutPlan, PlanExercise
from finance.models import FinanceCategory, CashAccount, FinanceEntry
from django.utils import timezone
from datetime import timedelta
from crm.models import Lead
from equipment.models import Equipment


MODULES = [
    ("core", "هسته سیستم", "◈", True, 10),
    ("members", "اعضا", "👤", True, 20),
    ("membership", "عضویت و قراردادها", "▣", True, 30),
    ("attendance", "حضور و غیاب", "✓", True, 40),
    ("access", "کنترل دسترسی", "▣", True, 45),
    ("trainers", "مربیان", "♟", True, 50),
    ("classes", "کلاس‌ها و رزرو", "▦", True, 60),
    ("pt", "تمرین خصوصی", "PT", False, 70),
    ("store", "فروشگاه", "▤", True, 80),
    ("cafe", "کافی‌شاپ", "☕", True, 90),
    ("workouts", "برنامه تمرینی", "W", True, 100),
    ("assessments", "ارزیابی بدنی", "A", True, 110),
    ("finance", "مالی و صندوق", "₿", True, 120),
    ("crm", "CRM و ارتباط با مشتری", "CRM", True, 130),
    ("reports", "گزارش‌ها", "▥", True, 140),
    ("api", "API و یکپارچه‌سازی", "API", True, 150),
    ("mobile", "پرتال و API اپلیکیشن", "M", True, 160),
    ("equipment", "تجهیزات و نگهداری", "⚙", True, 170),
]


class Command(BaseCommand):
    help = "ساخت داده‌های نمونه چندباشگاهی"

    def handle(self, *args, **options):
        User = get_user_model()

        modules = {}
        for code, name, icon, implemented, order in MODULES:
            module, _ = SystemModule.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "icon": icon,
                    "implemented": implemented,
                    "sort_order": order,
                },
            )
            modules[code] = module

        club1, _ = Club.objects.get_or_create(
            code="CLUB01",
            defaults={
                "name": "باشگاه نمونه اول",
                "slug": "club-one",
                "phone": "021-11111111",
                "address": "تهران - نمونه",
            },
        )
        club2, _ = Club.objects.get_or_create(
            code="CLUB02",
            defaults={
                "name": "باشگاه نمونه دوم",
                "slug": "club-two",
                "phone": "021-22222222",
                "address": "تهران - نمونه دوم",
            },
        )

        branch1, _ = Branch.objects.get_or_create(
            club=club1, code="MAIN",
            defaults={"name": "شعبه اصلی", "phone": "021-11111111"},
        )
        branch2, _ = Branch.objects.get_or_create(
            club=club2, code="MAIN",
            defaults={"name": "شعبه اصلی", "phone": "021-22222222"},
        )

        for club in [club1, club2]:
            for code, *_ in MODULES:
                if code in ("core", "members", "membership", "attendance", "access", "trainers", "classes", "store", "cafe", "workouts", "assessments", "finance", "crm", "reports", "api", "mobile", "equipment"):
                    ClubModule.objects.update_or_create(
                        club=club, module=modules[code], defaults={"enabled": True},
                    )
                else:
                    ClubModule.objects.get_or_create(
                        club=club, module=modules[code], defaults={"enabled": False},
                    )

        groups = ["مدیر سیستم", "پذیرش", "مربی", "حسابدار", "انباردار", "مدیر کافی‌شاپ"]
        for name in groups:
            Group.objects.get_or_create(name=name)

        admin, created = User.objects.get_or_create(username="admin")
        if created:
            admin.set_password("admin12345")
        admin.is_staff = True
        admin.is_superuser = True
        admin.display_name = "مدیر سامانه"
        admin.save()

        for club, branch in [(club1, branch1), (club2, branch2)]:
            ClubMembership.objects.update_or_create(
                user=admin,
                club=club,
                defaults={"branch": branch, "role": "مدیر سامانه", "is_manager": True, "is_active": True},
            )

        u1, created = User.objects.get_or_create(username="club1")
        if created:
            u1.set_password("club12345")
        u1.display_name = "مدیر باشگاه اول"
        u1.is_staff = False
        u1.save()
        ClubMembership.objects.update_or_create(
            user=u1, club=club1,
            defaults={"branch": branch1, "role": "مدیر باشگاه", "is_manager": True, "is_active": True},
        )

        u2, created = User.objects.get_or_create(username="club2")
        if created:
            u2.set_password("club12345")
        u2.display_name = "مدیر باشگاه دوم"
        u2.is_staff = False
        u2.save()
        ClubMembership.objects.update_or_create(
            user=u2, club=club2,
            defaults={"branch": branch2, "role": "مدیر باشگاه", "is_manager": True, "is_active": True},
        )

        demo_member1, _ = Member.objects.get_or_create(
            club=club1, member_code="1001",
            defaults={"branch": branch1, "first_name": "علی", "last_name": "رضایی", "mobile": "09120000001"},
        )
        demo_member2, _ = Member.objects.get_or_create(
            club=club2, member_code="2001",
            defaults={"branch": branch2, "first_name": "رضا", "last_name": "احمدی", "mobile": "09120000002"},
        )

        for club, branch, member, code in [
            (club1, branch1, demo_member1, "BASIC30"),
            (club2, branch2, demo_member2, "BASIC30"),
        ]:
            plan, _ = MembershipPlan.objects.get_or_create(
                club=club, code=code,
                defaults={"name": "ماهانه نمونه", "duration_days": 30, "price": 3000000, "description": "پلن آزمایشی"},
            )
            contract, created = MembershipContract.objects.get_or_create(
                club=club, contract_code=f"DEMO-{member.member_code}",
                defaults={
                    "branch": branch, "member": member, "plan": plan,
                    "start_date": timezone.localdate(),
                    "end_date": timezone.localdate() + timedelta(days=29),
                    "agreed_price": plan.price, "created_by": admin,
                },
            )
            if created:
                Payment.objects.create(
                    club=club, branch=branch, member=member, contract=contract,
                    amount=plan.price, method="cash", status="paid", received_by=admin,
                )
            AccessCredential.objects.get_or_create(
                club=club, token=f"QR-{member.member_code}",
                defaults={"member": member, "credential_type": "qr", "is_active": True},
            )
            Product.objects.get_or_create(
                club=club, sku="DEMO-WATER",
                defaults={"branch": branch, "name": "آب معدنی نمونه", "category": "نوشیدنی", "unit": "بطری", "cost_price": 5000, "sale_price": 10000, "stock_quantity": 25, "min_stock": 5},
            )
            MenuItem.objects.get_or_create(
                club=club, name="قهوه نمونه",
                defaults={"category": "نوشیدنی گرم", "price": 80000, "is_available": True},
            )
            exercise, _ = Exercise.objects.get_or_create(
                club=club, name="اسکوات وزن بدن",
                defaults={"muscle_group": "پا", "equipment": "بدون وسیله", "instructions": "حرکت را با کنترل انجام دهید."},
            )
            plan, _ = WorkoutPlan.objects.get_or_create(
                club=club, name="برنامه آغازین",
                defaults={"level": "beginner", "description": "برنامه نمونه باشگاه"},
            )
            PlanExercise.objects.get_or_create(
                plan=plan, exercise=exercise, day_number=1,
                defaults={"sets": 3, "repetitions": "12", "rest_seconds": 60, "sort_order": 1},
            )
            income_category, _ = FinanceCategory.objects.get_or_create(club=club, name="درآمد عضویت", entry_type="income")
            FinanceCategory.objects.get_or_create(club=club, name="فروش فروشگاه", entry_type="income")
            FinanceCategory.objects.get_or_create(club=club, name="فروش کافی‌شاپ", entry_type="income")
            FinanceCategory.objects.get_or_create(club=club, name="هزینه جاری", entry_type="expense")
            account, _ = CashAccount.objects.get_or_create(club=club, name="صندوق اصلی", defaults={"branch": branch})
            for payment in Payment.objects.filter(club=club, status="paid"):
                FinanceEntry.objects.get_or_create(
                    club=club, source="membership_payment", source_id=str(payment.pk),
                    defaults={"branch": payment.branch, "category": income_category, "account": account, "entry_type": "income", "amount": payment.amount, "occurred_on": payment.paid_on, "description": f"پرداخت عضویت {payment.member.full_name}"},
                )
            trainer, _ = Trainer.objects.get_or_create(
                club=club, display_name="مربی نمونه",
                defaults={"branch": branch, "mobile": "", "specialty": "بدنسازی"},
            )
            start = (timezone.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            FitnessClass.objects.get_or_create(
                club=club, title="کلاس بدنسازی نمونه", starts_at=start,
                defaults={"branch": branch, "trainer": trainer, "ends_at": start + timedelta(hours=1), "capacity": 12, "room": "سالن اصلی"},
            )
            Lead.objects.get_or_create(club=club,mobile=f"0912999999{member.member_code[-1]}",defaults={"first_name":"مریم","last_name":"نمونه","source":"معرفی دوستان","stage":"contacted","assigned_to":admin})
            Equipment.objects.get_or_create(club=club,asset_code="DEMO-TREADMILL",defaults={"branch":branch,"name":"تردمیل نمونه","location":"سالن اصلی","status":"active"})

        self.stdout.write(self.style.SUCCESS("Multi-club demo data is ready."))
        self.stdout.write("admin / admin12345")
        self.stdout.write("club1 / club12345")
        self.stdout.write("club2 / club12345")
