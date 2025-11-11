from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tracking.models import CompteTiktok

@login_required
def home_page(request):
    comptes = CompteTiktok.objects.filter(user=request.user)
    return render(request, "core/home.html", {'comptes': comptes})
