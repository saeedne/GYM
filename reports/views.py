import csv
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from members.models import Member
from membership.models import MembershipContract, Payment
from attendance.models import AttendanceRecord
from finance.models import FinanceEntry
from store.models import StoreSale
from trainers.models import ClassBooking
from crm.models import Lead

def _data(club, start, end):
    payments=Payment.objects.filter(club=club,status="paid",paid_on__range=(start,end))
    entries=FinanceEntry.objects.filter(club=club,occurred_on__range=(start,end))
    attend=AttendanceRecord.objects.filter(club=club,check_in__date__range=(start,end))
    return {"payments":payments,"entries":entries,"attendance":attend,"new_members":Member.objects.filter(club=club,created_at__date__range=(start,end)).count(),"active_members":Member.objects.filter(club=club,status="active").count(),"contracts":MembershipContract.objects.filter(club=club,status="active",end_date__gte=start,end_date__lte=end).count(),"leads":Lead.objects.filter(club=club,created_at__date__range=(start,end)).count(),"converted":Lead.objects.filter(club=club,stage="won",updated_at__date__range=(start,end)).count(),"sales":StoreSale.objects.filter(club=club,sold_at__date__range=(start,end)).count(),"class_bookings":ClassBooking.objects.filter(club=club,booked_at__date__range=(start,end)).count(),"income":entries.filter(entry_type="income").aggregate(v=Sum("amount"))["v"] or 0,"expenses":entries.filter(entry_type="expense").aggregate(v=Sum("amount"))["v"] or 0,"visits":attend.count(),"daily":attend.values("check_in__date").annotate(total=Count("id")).order_by("check_in__date")}

@login_required
def dashboard(request):
    club=request.active_club
    if not club: return render(request,"reports/dashboard.html",{"no_club":True})
    end=timezone.localdate(); start=end-timedelta(days=29)
    data=_data(club,start,end)
    data.update({"start":start,"end":end,"net":data["income"]-data["expenses"]})
    return render(request,"reports/dashboard.html",data)

@login_required
def export_csv(request):
    club=request.active_club
    if not club: return HttpResponse("No active club",status=400)
    response=HttpResponse(content_type="text/csv; charset=utf-8"); response.write("\ufeff")
    response["Content-Disposition"]='attachment; filename="gym-report.csv"'
    writer=csv.writer(response); writer.writerow(["date","entry_type","category","amount_irr","description"])
    def safe(value):
        value=str(value or "")
        return "'"+value if value.startswith(("=","+","-","@","\t","\r")) else value
    for row in FinanceEntry.objects.filter(club=club).select_related("category").order_by("-occurred_on")[:10000]: writer.writerow([row.occurred_on,row.entry_type,safe(row.category.name if row.category else ""),row.amount,safe(row.description)])
    return response
