from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404,redirect,render
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_POST
from .models import Equipment,Maintenance

class EquipmentForm(forms.ModelForm):
    class Meta: model=Equipment; fields=["branch","name","asset_code","location","status","purchased_on","notes"]
    def __init__(self,*args,club=None,**kwargs):
        super().__init__(*args,**kwargs)
        if club and "branch" in self.fields: self.fields["branch"].queryset=club.branches.filter(is_active=True)
class MaintenanceForm(forms.ModelForm):
    class Meta: model=Maintenance; fields=["title","due_on","cost","notes"]
@login_required
def list_equipment(request): return render(request,"equipment/list.html",{"items":Equipment.objects.filter(club=request.active_club).prefetch_related("maintenance")})
@login_required
def create_equipment(request):
    form=EquipmentForm(request.POST or None,club=request.active_club)
    if form.is_valid(): item=form.save(commit=False); item.club=request.active_club; item.save(); return redirect("equipment:list")
    return render(request,"equipment/form.html",{"form":form,"title":"ثبت تجهیز"})

@login_required
def edit_equipment(request, pk):
    item=get_object_or_404(Equipment,pk=pk,club=request.active_club)
    form=EquipmentForm(request.POST or None,instance=item,club=request.active_club)
    if request.method == "POST" and form.is_valid():
        form.save(); return redirect("equipment:list")
    return render(request,"equipment/form.html",{"form":form,"title":f"ویرایش تجهیز: {item.name}"})


@login_required
@require_POST
def equipment_delete(request, pk):
    item=get_object_or_404(Equipment,pk=pk,club=request.active_club)
    if item.maintenance.exists():
        messages.error(request,"این تجهیز سابقه سرویس دارد و برای حفظ تاریخچه حذف نمی‌شود.")
    else:
        name=item.name
        item.delete()
        messages.success(request,f"تجهیز «{name}» حذف شد.")
    return redirect("equipment:list")
@login_required
def add_maintenance(request,pk):
    item=get_object_or_404(Equipment,pk=pk,club=request.active_club); form=MaintenanceForm(request.POST or None)
    if form.is_valid(): log=form.save(commit=False); log.equipment=item; log.club=item.club; log.created_by=request.user; log.save(); return redirect("equipment:list")
    return render(request,"equipment/form.html",{"form":form,"title":f"ثبت سرویس: {item.name}"})
