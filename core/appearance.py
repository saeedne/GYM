from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def appearance_settings(request):
    return render(request, "settings/appearance.html")
