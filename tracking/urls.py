from django.urls import path
from . import views

urlpatterns = [
    path('comptes/', views.liste_comptes, name='comptes_list'),
    path('comptes/ajouter/', views.ajouter_compte, name='compte_add'),
    path('compte/<int:compte_id>/', views.detail_compte, name='compte_detail'),
    path('lives/', views.liste_lives, name='lives_list'),
]
