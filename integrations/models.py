from django.conf import settings
from django.db import models
class ClubApiKey(models.Model):
    club=models.ForeignKey("core.Club",on_delete=models.CASCADE,related_name="api_keys")
    name=models.CharField("نام کلید",max_length=100)
    prefix=models.CharField(max_length=12,db_index=True)
    secret_hash=models.CharField(max_length=64)
    scopes=models.JSONField("دسترسی‌ها",default=list)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    last_used_at=models.DateTimeField(null=True,blank=True)
    expires_at=models.DateTimeField(null=True,blank=True)
    revoked_at=models.DateTimeField(null=True,blank=True)
    class Meta: verbose_name="کلید API باشگاه"; verbose_name_plural="کلیدهای API باشگاه"
    def __str__(self): return f"{self.name} ({self.club.name})"
