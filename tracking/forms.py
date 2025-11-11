from django import forms
from .models import CompteTiktok

class CompteTiktokForm(forms.ModelForm):
    class Meta:
        model = CompteTiktok
        fields = ['username']  # On ne demande que le nom d'utilisateur

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@NomUtilisateur',  # Affiche @ devant
            }),
        }

        labels = {
            'username': 'Nom d’utilisateur',
        }

        help_texts = {
            'username': 'Entre le nom sans le @',
        }
