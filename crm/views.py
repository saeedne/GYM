from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from core.models import AuditLog
from .forms import LeadForm, ActivityForm, MessageForm
from .models import Lead, LeadActivity, MessageQueue

@login_required
def leads(request):
    club = request.active_club
    if not club: return render(request, "crm/leads.html", {"no_club": True})
    qs = Lead.objects.filter(club=club).select_related("assigned_to")
    stage = request.GET.get("stage")
    if stage: qs = qs.filter(stage=stage)
    q = request.GET.get("q", "").strip()
    if q: qs = qs.filter(mobile__icontains=q) | qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q)
    return render(request, "crm/leads.html", {"leads": qs[:250], "stage_choices": Lead.STAGES, "stage": stage, "q": q})

@login_required
def lead_create(request):
    if not request.active_club: return redirect("dashboard")
    form = LeadForm(request.POST or None)
    if form.is_valid():
        lead = form.save(commit=False); lead.club = request.active_club; lead.assigned_to = request.user; lead.save()
        AuditLog.objects.create(club=lead.club,user=request.user,action="create",model_name="Lead",object_id=str(lead.pk),description=f"سرنخ {lead}")
        messages.success(request, "سرنخ ثبت شد."); return redirect("crm:lead_detail", pk=lead.pk)
    return render(request,"crm/lead_form.html",{"form":form})

@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(Lead, club=request.active_club, pk=pk)
    form = LeadForm(request.POST or None, instance=lead)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "اطلاعات سرنخ به‌روزرسانی شد.")
        return redirect("crm:lead_detail", pk=lead.pk)
    return render(request, "crm/lead_form.html", {"form": form, "title": "ویرایش سرنخ"})


@login_required
@require_POST
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, club=request.active_club, pk=pk)
    name = str(lead)
    if lead.activities.exists():
        messages.error(request, "این سرنخ سوابق پیگیری دارد و حذف نمی‌شود تا تاریخچه تماس‌ها حفظ شود.")
    else:
        lead.delete()
        messages.success(request, f"سرنخ «{name}» حذف شد.")
    return redirect("crm:leads")

@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead.objects.filter(club=request.active_club), pk=pk)
    activity_form = ActivityForm(request.POST or None, prefix="activity")
    message_form = MessageForm(request.POST or None, prefix="message")
    if request.method == "POST" and "add_activity" in request.POST and activity_form.is_valid():
        item = activity_form.save(commit=False); item.club=lead.club; item.lead=lead; item.created_by=request.user; item.save()
        return redirect("crm:lead_detail", pk=lead.pk)
    if request.method == "POST" and "queue_message" in request.POST and message_form.is_valid():
        item=message_form.save(commit=False); item.club=lead.club; item.save()
        messages.info(request,"پیام در صف قرار گرفت؛ برای ارسال واقعی باید سرویس پیام‌رسان تنظیم شود.")
        return redirect("crm:lead_detail", pk=lead.pk)
    return render(request,"crm/lead_detail.html",{"lead":lead,"activity_form":activity_form,"message_form":message_form,"activities":lead.activities.all()})

@login_required
@require_POST
def complete_activity(request, pk):
    activity=get_object_or_404(LeadActivity.objects.filter(club=request.active_club),pk=pk)
    activity.completed_at=timezone.now(); activity.save(update_fields=["completed_at"])
    return redirect("crm:lead_detail",pk=activity.lead_id)

@login_required
def message_queue(request):
    return render(request,"crm/messages.html",{"items":MessageQueue.objects.filter(club=request.active_club)[:200]})
