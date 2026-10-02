from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from core.models import AuditLog
from .forms import BookingForm, FitnessClassForm, TrainerForm
from .models import ClassBooking, FitnessClass, Trainer


@login_required
def trainer_list(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = TrainerForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="Trainer", object_id=str(obj.pk), description=f"مربی {obj.display_name} ثبت شد.")
        messages.success(request, "مربی ثبت شد.")
        return redirect("trainers:list")
    return render(request, "trainers/list.html", {"club": club, "form": form, "trainers": Trainer.objects.filter(club=club).select_related("branch")})

@login_required
def trainer_edit(request, pk):
    club = request.active_club
    trainer = get_object_or_404(Trainer, club=club, pk=pk)
    form = TrainerForm(request.POST or None, instance=trainer, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="update", model_name="Trainer", object_id=str(item.pk), description=f"مشخصات مربی {item.display_name} ویرایش شد.")
        messages.success(request, "مشخصات مربی ذخیره شد.")
        return redirect("trainers:list")
    return render(request, "trainers/trainer_form.html", {"club": club, "form": form, "title": "ویرایش مربی"})


@login_required
@require_POST
def trainer_delete(request, pk):
    item = get_object_or_404(Trainer, club=request.active_club, pk=pk)
    name = item.display_name
    try:
        item.delete()
    except ProtectedError:
        messages.error(request, "این مربی برای کلاس‌های ثبت‌شده استفاده شده است و حذف نمی‌شود.")
    else:
        messages.success(request, f"مربی «{name}» حذف شد.")
    return redirect("trainers:list")


@login_required
def class_list(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    qs = FitnessClass.objects.filter(club=club).select_related("trainer", "branch").prefetch_related("bookings")
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "trainers/classes.html", {"club": club, "items": page, "page_obj": page})


@login_required
def class_create(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = FitnessClassForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="FitnessClass", object_id=str(item.pk), description=f"کلاس {item.title} ایجاد شد.")
        messages.success(request, "کلاس ثبت شد.")
        return redirect("trainers:classes")
    return render(request, "trainers/class_form.html", {"club": club, "form": form, "title": "ثبت کلاس"})

@login_required
def class_edit(request, pk):
    club = request.active_club
    item = get_object_or_404(FitnessClass, club=club, pk=pk)
    form = FitnessClassForm(request.POST or None, instance=item, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="update", model_name="FitnessClass", object_id=str(item.pk), description=f"کلاس {item.title} ویرایش شد.")
        messages.success(request, "کلاس به‌روزرسانی شد.")
        return redirect("trainers:classes")
    return render(request, "trainers/class_form.html", {"club": club, "form": form, "title": "ویرایش کلاس"})


@login_required
@require_POST
def class_delete(request, pk):
    item = get_object_or_404(FitnessClass, club=request.active_club, pk=pk)
    title = item.title
    if item.bookings.exists():
        messages.error(request, "برای حفظ سوابق رزرو، کلاسی که رزرو دارد حذف نمی‌شود؛ وضعیت آن را ویرایش کنید.")
    else:
        item.delete()
        messages.success(request, f"کلاس «{title}» حذف شد.")
    return redirect("trainers:classes")


@login_required
def class_book(request, pk):
    club = request.active_club
    session = get_object_or_404(FitnessClass, club=club, pk=pk, status="scheduled")
    form = BookingForm(request.POST or None, club=club, fitness_class=session)
    if request.method == "POST" and form.is_valid():
        if session.starts_at <= timezone.now():
            messages.error(request, "زمان این کلاس گذشته است.")
            return redirect("trainers:classes")
        with transaction.atomic():
            member = form.cleaned_data["member"]
            booking = ClassBooking.objects.filter(fitness_class=session, member=member).first()
            next_status = "booked" if session.available_seats > 0 else "waitlist"
            if booking and booking.status != "cancelled":
                messages.error(request, "این عضو قبلاً برای این کلاس ثبت شده است.")
                return redirect("trainers:classes")
            if booking:
                booking.status = next_status
                booking.booked_at = timezone.now()
            else:
                booking = form.save(commit=False)
                booking.club, booking.fitness_class = club, session
                booking.status = next_status
            try:
                booking.save()
                messages.success(request, "رزرو ثبت شد." if booking.status == "booked" else "ظرفیت تکمیل است؛ عضو به فهرست انتظار افزوده شد.")
            except IntegrityError:
                messages.error(request, "این عضو قبلاً برای این کلاس ثبت شده است.")
        return redirect("trainers:classes")
    return render(request, "trainers/book.html", {"club": club, "session": session, "form": form})


@login_required
@require_POST
def booking_cancel(request, pk):
    club = request.active_club
    booking = get_object_or_404(ClassBooking.objects.select_related("fitness_class"), club=club, pk=pk)
    session = booking.fitness_class
    was_booked = booking.status == "booked"
    booking.status = "cancelled"
    booking.save(update_fields=["status"])
    if was_booked:
        next_up = ClassBooking.objects.filter(fitness_class=session, status="waitlist").order_by("booked_at", "pk").first()
        if next_up:
            next_up.status = "booked"
            next_up.save(update_fields=["status"])
            messages.success(request, f"رزرو لغو شد؛ {next_up.member.full_name} از فهرست انتظار به رزرو قطعی منتقل شد.")
            return redirect("trainers:classes")
    messages.success(request, "رزرو لغو شد.")
    return redirect("trainers:classes")


@login_required
@require_POST
def mark_attendance(request, pk):
    club = request.active_club
    booking = get_object_or_404(ClassBooking, club=club, pk=pk, status="booked")
    booking.status = "attended"
    booking.attended_at = timezone.now()
    booking.save(update_fields=["status", "attended_at"])
    messages.success(request, "حضور کلاس ثبت شد.")
    return redirect("trainers:classes")
