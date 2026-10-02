from django.conf import settings
from django.db import models
from django.db.models import Q

class Lead(models.Model):
    STAGES = [("new", "جدید"), ("contacted", "تماس گرفته شد"), ("trial", "جلسه آزمایشی"), ("won", "ثبت‌نام شد"), ("lost", "از دست رفته")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE, related_name="leads")
    branch = models.ForeignKey("core.Branch", on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField("نام", max_length=80)
    last_name = models.CharField("نام خانوادگی", max_length=100, blank=True)
    mobile = models.CharField("موبایل", max_length=20)
    email = models.EmailField("ایمیل", blank=True)
    source = models.CharField("منبع آشنایی", max_length=100, blank=True)
    stage = models.CharField("مرحله", max_length=16, choices=STAGES, default="new")
    notes = models.TextField("یادداشت", blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    converted_member = models.ForeignKey("members.Member", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["club", "stage"]), models.Index(fields=["club", "mobile"])]
    def __str__(self): return f"{self.first_name} {self.last_name}".strip()

class LeadActivity(models.Model):
    TYPES = [("call", "تماس"), ("meeting", "جلسه"), ("message", "پیام"), ("note", "یادداشت")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField("نوع پیگیری", max_length=12, choices=TYPES, default="call")
    summary = models.CharField("شرح", max_length=240)
    due_at = models.DateTimeField("زمان پیگیری", null=True, blank=True)
    completed_at = models.DateTimeField("انجام‌شده در", null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]

class MessageQueue(models.Model):
    CHANNELS = [("sms", "پیامک"), ("email", "ایمیل"), ("push", "اعلان")]
    STATUSES = [("queued", "در صف"), ("sent", "ارسال‌شده"), ("failed", "ناموفق"), ("cancelled", "لغوشده")]
    club = models.ForeignKey("core.Club", on_delete=models.CASCADE)
    member = models.ForeignKey("members.Member", on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.CharField("کانال", max_length=8, choices=CHANNELS, default="sms")
    recipient = models.CharField("گیرنده", max_length=160)
    body = models.TextField("متن پیام")
    scheduled_at = models.DateTimeField("زمان‌بندی", null=True, blank=True)
    status = models.CharField("وضعیت", max_length=12, choices=STATUSES, default="queued")
    provider_ref = models.CharField("شناسه سرویس", max_length=160, blank=True)
    dedupe_key = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["club", "dedupe_key"], condition=~Q(dedupe_key=""), name="uniq_message_dedupe_per_club")]
