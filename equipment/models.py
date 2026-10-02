from django.conf import settings
from django.db import models
class Equipment(models.Model):
    club=models.ForeignKey("core.Club",on_delete=models.CASCADE,related_name="equipment")
    branch=models.ForeignKey("core.Branch",on_delete=models.SET_NULL,null=True,blank=True)
    name=models.CharField("نام تجهیز",max_length=140)
    asset_code=models.CharField("کد اموال",max_length=60)
    location=models.CharField("محل استقرار",max_length=140,blank=True)
    status=models.CharField("وضعیت",max_length=16,choices=[("active","فعال"),("service","نیازمند سرویس"),("repair","خراب"),("retired","خارج از سرویس")],default="active")
    purchased_on=models.DateField("تاریخ خرید",null=True,blank=True)
    notes=models.TextField("یادداشت",blank=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["club","asset_code"],name="uniq_equipment_code_club")]
    def __str__(self): return f"{self.name} ({self.asset_code})"
class Maintenance(models.Model):
    equipment=models.ForeignKey(Equipment,on_delete=models.CASCADE,related_name="maintenance")
    club=models.ForeignKey("core.Club",on_delete=models.CASCADE)
    title=models.CharField("شرح سرویس/خرابی",max_length=180)
    reported_on=models.DateField("تاریخ ثبت",auto_now_add=True)
    due_on=models.DateField("موعد",null=True,blank=True)
    completed_on=models.DateField("تاریخ اتمام",null=True,blank=True)
    cost=models.PositiveBigIntegerField("هزینه (ریال)",default=0)
    notes=models.TextField("یادداشت",blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    class Meta: ordering=["-reported_on"]
