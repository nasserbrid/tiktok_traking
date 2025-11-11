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

    # 🔹 Ajout de la vérification personnalisée
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # On récupère l'utilisateur connecté
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if self.user and CompteTiktok.objects.filter(user=self.user, username=username).exists():
            raise forms.ValidationError("Ce compte TikTok est déjà dans votre liste.")
        return username


# from django import forms
# from .models import CompteTiktok

# class CompteTiktokForm(forms.ModelForm):
#     class Meta:
#         model = CompteTiktok
#         fields = ['username']  # On ne demande que le nom d'utilisateur

#         widgets = {
#             'username': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': '@NomUtilisateur',  # Affiche @ devant
#             }),
#         }

#         labels = {
#             'username': 'Nom d’utilisateur',
#         }

#         help_texts = {
#             'username': 'Entre le nom sans le @',
#         }
