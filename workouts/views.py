from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from core.models import AuditLog
from .forms import AssessmentForm, AssignmentForm, ExerciseForm, PlanExerciseForm, PlanForm
from .models import BodyAssessment, Exercise, WorkoutAssignment, WorkoutPlan


@login_required
def plans(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = PlanForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="WorkoutPlan", object_id=str(item.pk), description=f"برنامه {item.name} ثبت شد.")
        messages.success(request, "برنامه تمرینی ایجاد شد.")
        return redirect("workouts:plan_detail", pk=item.pk)
    return render(request, "workouts/plans.html", {"club": club, "form": form, "items": WorkoutPlan.objects.filter(club=club).prefetch_related("items")})

@login_required
def plan_edit(request, pk):
    club=request.active_club
    item=get_object_or_404(WorkoutPlan, club=club, pk=pk)
    form=PlanForm(request.POST or None, instance=item, club=club)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "برنامه تمرینی به‌روزرسانی شد.")
        return redirect("workouts:plan_detail", pk=item.pk)
    return render(request, "workouts/plan_edit.html", {"form":form, "item":item})


@login_required
@require_POST
def workout_plan_delete(request, pk):
    item = get_object_or_404(WorkoutPlan, club=request.active_club, pk=pk)
    name = item.name
    try:
        item.delete()
    except ProtectedError:
        messages.error(request, "این برنامه به اعضا اختصاص داده شده است و حذف نمی‌شود.")
    else:
        messages.success(request, f"برنامه «{name}» حذف شد.")
    return redirect("workouts:plans")


@login_required
def plan_detail(request, pk):
    club = request.active_club
    plan = get_object_or_404(WorkoutPlan.objects.prefetch_related("items__exercise"), club=club, pk=pk)
    form = PlanExerciseForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.plan = plan
        item.save()
        messages.success(request, "حرکت به برنامه افزوده شد.")
        return redirect("workouts:plan_detail", pk=plan.pk)
    return render(request, "workouts/plan_detail.html", {"club": club, "plan": plan, "form": form})


@login_required
def exercise_library(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = ExerciseForm(request.POST or None, club=club)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "حرکت ثبت شد.")
        return redirect("workouts:exercises")
    return render(request, "workouts/exercises.html", {"club": club, "form": form, "items": Exercise.objects.filter(club=club)})

@login_required
def exercise_edit(request, pk):
    club=request.active_club
    item=get_object_or_404(Exercise, club=club, pk=pk)
    form=ExerciseForm(request.POST or None, instance=item, club=club)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "حرکت به‌روزرسانی شد.")
        return redirect("workouts:exercises")
    return render(request, "workouts/exercise_edit.html", {"form":form, "item":item})


@login_required
@require_POST
def exercise_delete(request, pk):
    item = get_object_or_404(Exercise, club=request.active_club, pk=pk)
    name = item.name
    try:
        item.delete()
    except ProtectedError:
        messages.error(request, "این حرکت در برنامه‌های تمرینی استفاده شده و حذف نمی‌شود؛ آن را غیرفعال کنید.")
    else:
        messages.success(request, f"حرکت «{name}» حذف شد.")
    return redirect("workouts:exercises")


@login_required
def assignments(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = AssignmentForm(request.POST or None, club=club, user=request.user)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="WorkoutAssignment", object_id=str(item.pk), description=f"برنامه {item.plan.name} به {item.member.full_name} اختصاص داده شد.")
        messages.success(request, "برنامه به عضو اختصاص یافت.")
        return redirect("workouts:assignments")
    items = WorkoutAssignment.objects.filter(club=club).select_related("member", "plan")
    return render(request, "workouts/assignments.html", {"club": club, "form": form, "items": items})


@login_required
def assessments(request):
    club = request.active_club
    if not club: return redirect("dashboard")
    form = AssessmentForm(request.POST or None, club=club, user=request.user)
    if request.method == "POST" and form.is_valid():
        item = form.save()
        AuditLog.objects.create(club=club, user=request.user, action="create", model_name="BodyAssessment", object_id=str(item.pk), description=f"ارزیابی بدنی {item.member.full_name} ثبت شد.")
        messages.success(request, "ارزیابی ثبت شد.")
        return redirect("workouts:assessments")
    items = BodyAssessment.objects.filter(club=club).select_related("member", "branch")[:100]
    return render(request, "workouts/assessments.html", {"club": club, "form": form, "items": items})
