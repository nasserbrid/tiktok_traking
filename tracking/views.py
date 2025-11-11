from django.shortcuts import render, redirect, get_object_or_404 
from .models import CompteTiktok, Live
from .forms import CompteTiktokForm
from django.contrib.auth.decorators import login_required

@login_required
def liste_comptes(request):
    """
    Dashboard : affiche les comptes TikTok suivis par l'utilisateur.
    - Suppression des doublons par username.
    - Ajoute un attribut 'en_live' pour savoir si le compte a un live en cours.
    """
    comptes = CompteTiktok.objects.filter(user=request.user)
    
    comptes_uniques = []
    usernames_vus = set()
    for compte in comptes:
        if compte.username not in usernames_vus:
            compte.en_live = compte.lives.filter(statut='en_cours').exists()
            comptes_uniques.append(compte)
            usernames_vus.add(compte.username)

    return render(request, 'core/home.html', {'comptes': comptes_uniques})


@login_required
def detail_compte(request, compte_id):
    compte = get_object_or_404(CompteTiktok, id=compte_id, user=request.user)
    lives = compte.lives.all()
    return render(request, 'tracking/compte_detail.html', {'compte': compte, 'lives': lives})

@login_required
def liste_lives(request):
    lives = Live.objects.filter(compte__user=request.user)
    return render(request, 'tracking/lives_list.html', {'lives': lives})

@login_required
def ajouter_compte(request):
    if request.method == 'POST':
        form = CompteTiktokForm(request.POST)
        if form.is_valid():
            compte = form.save(commit=False)
            compte.user = request.user
            compte.save()
            return redirect('home')  # Redirige vers le dashboard
    else:
        form = CompteTiktokForm()

    return render(request, 'tracking/compte_add.html', {'form': form})
