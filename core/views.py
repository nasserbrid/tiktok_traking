import asyncio
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tracking.managers.live_manager import update_live_status
from tracking.models import CompteTiktok
from tracking.services.tiktok_live_service import is_live

@login_required
def home_page(request):
    comptes = CompteTiktok.objects.filter(user=request.user)
    for compte in comptes:
        live_detected, room_id = asyncio.run(is_live(compte.username))
        update_live_status(compte, live_detected, room_id)

        compte.derniere_analyse = compte.get_derniere_analyse()

    return render(request, "core/home.html", {'comptes': comptes})
