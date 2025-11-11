from django.db import models
from authentication.models import User

class CompteTiktok(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comptes_tiktok")
    username = models.CharField(max_length=255)
    url = models.URLField()
    date_creation = models.DateTimeField(auto_now_add=True)
    nb_followers = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'username')

    def __str__(self):
        return self.username
    
    @property
    def statut(self):
        if self.lives.filter(statut='en_cours').exists():
            return 'En ligne'
        elif self.lives.exists():
            return 'Actif'
        else:
            return 'Hors ligne'


class Live(models.Model):
    compte = models.ForeignKey(CompteTiktok, on_delete=models.CASCADE, related_name="lives")
    titre = models.CharField(max_length=255)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    nb_spectateurs = models.PositiveIntegerField(default=0)
    statut = models.CharField(
        max_length=50,
        choices=[
            ('en_cours', 'En cours'),
            ('termine', 'Terminé'),
        ],
        default='en_cours'
    )

    def __str__(self):
        return f"{self.titre} ({self.compte.username})"

