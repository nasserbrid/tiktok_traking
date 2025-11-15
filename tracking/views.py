from django.shortcuts import render, redirect, get_object_or_404 
from .models import CompteTiktok, Live
from .forms import CompteTiktokForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def liste_comptes(request):
    """
    Dashboard : affiche les comptes TikTok suivis par l'utilisateur.
    - Suppression des doublons par username.
    - Ajoute un attribut 'en_live' pour savoir si le compte a un live en cours.
    - Calcule le statut dynamique basé sur les lives détectés.
    """
    comptes = CompteTiktok.objects.filter(user=request.user)
    
    comptes_uniques = []
    usernames_vus = set()
    for compte in comptes:
        if compte.username not in usernames_vus:
            # Vérifie si le compte a un live en cours
            compte.en_live = compte.lives.filter(statut='en_cours').exists()
            
            # Calcule le statut dynamique
            if compte.en_live:
                compte.statut_dynamique = 'En ligne'
            elif compte.lives.exists():
                compte.statut_dynamique = 'Hors ligne'
            else:
                compte.statut_dynamique = 'Jamais en live'
            
            comptes_uniques.append(compte)
            usernames_vus.add(compte.username)

    return render(request, 'core/home.html', {'comptes': comptes_uniques})


@login_required
def detail_compte(request, compte_id):
    compte = get_object_or_404(CompteTiktok, id=compte_id, user=request.user)
    lives = compte.lives.all().order_by('-date_debut')  # Les plus récents d'abord
    return render(request, 'tracking/compte_detail.html', {'compte': compte, 'lives': lives})


@login_required
def liste_lives(request):
    lives = Live.objects.filter(compte__user=request.user).order_by('-date_debut')
    return render(request, 'tracking/lives_list.html', {'lives': lives})


@login_required
def ajouter_compte(request):
    if request.method == 'POST':
        form = CompteTiktokForm(request.POST, user=request.user)
        if form.is_valid():
            compte = form.save(commit=False)
            compte.user = request.user
            compte.url = f"https://www.tiktok.com/@{compte.username}"
            compte.save()
            messages.success(request, f"✅ Compte @{compte.username} ajouté avec succès !")
            return redirect('home')
    else:
        form = CompteTiktokForm(user=request.user)

    return render(request, 'tracking/compte_add.html', {'form': form})


@login_required
def supprimer_compte(request, compte_id):
    """
    Supprime un compte TikTok après confirmation.
    """
    compte = get_object_or_404(CompteTiktok, id=compte_id, user=request.user)
    
    if request.method == 'POST':
        username = compte.username
        compte.delete()
        messages.success(request, f"🗑️ Compte @{username} supprimé avec succès !")
        return redirect('home')
    
    return render(request, 'tracking/compte_delete.html', {'compte': compte})
# from django.shortcuts import render, redirect, get_object_or_404 
# from .models import CompteTiktok, Live
# from .forms import CompteTiktokForm
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages

# @login_required
# def liste_comptes(request):
#     """
#     Dashboard : affiche les comptes TikTok suivis par l'utilisateur.
#     - Suppression des doublons par username.
#     - Ajoute un attribut 'en_live' pour savoir si le compte a un live en cours.
#     """
#     comptes = CompteTiktok.objects.filter(user=request.user)
    
#     comptes_uniques = []
#     usernames_vus = set()
#     for compte in comptes:
#         if compte.username not in usernames_vus:
#             compte.en_live = compte.lives.filter(statut='en_cours').exists()
#             comptes_uniques.append(compte)
#             usernames_vus.add(compte.username)

#     return render(request, 'core/home.html', {'comptes': comptes_uniques})


# @login_required
# def detail_compte(request, compte_id):
#     compte = get_object_or_404(CompteTiktok, id=compte_id, user=request.user)
#     lives = compte.lives.all()
#     return render(request, 'tracking/compte_detail.html', {'compte': compte, 'lives': lives})

# @login_required
# def liste_lives(request):
#     lives = Live.objects.filter(compte__user=request.user)
#     return render(request, 'tracking/lives_list.html', {'lives': lives})

# @login_required
# def ajouter_compte(request):
#     if request.method == 'POST':
#         form = CompteTiktokForm(request.POST, user=request.user)  # ✅ ajout du paramètre user
#         if form.is_valid():
#             compte = form.save(commit=False)
#             compte.user = request.user
#             compte.url = f"https://www.tiktok.com/@{compte.username}"  # (optionnel) auto-générer l’URL
#             compte.save()
#             return redirect('home')
#     else:
#         form = CompteTiktokForm(user=request.user)  # ✅ idem ici

#     return render(request, 'tracking/compte_add.html', {'form': form})

# @login_required
# def supprimer_compte(request, compte_id):
#     """
#     Supprime un compte TikTok après confirmation.
#     """
#     compte = get_object_or_404(CompteTiktok, id=compte_id, user=request.user)
    
#     if request.method == 'POST':
#         username = compte.username
#         compte.delete()
#         messages.success(request, f"🗑️ Compte @{username} supprimé avec succès !")
#         return redirect('home')
    
#     return render(request, 'tracking/compte_delete.html', {'compte': compte})