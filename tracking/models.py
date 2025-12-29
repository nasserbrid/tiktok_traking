from django.db import models
from django.conf import settings
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
    def en_live(self):
        return self.lives.filter(statut='en_cours').exists()

    @property
    def statut_dynamique(self):
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
    
    
    def save(self, *args, **kwargs):
        is_new_live = self.pk is None
        previous_statut = None
        if not is_new_live:
            previous = Live.objects.get(pk=self.pk)
            previous_statut = previous.statut

        super().save(*args, **kwargs)

        if self.statut == 'en_cours' and (is_new_live or previous_statut != 'en_cours'):
            from notifications.utils import envoyer_notification_live
            envoyer_notification_live(self)


class Transcription(models.Model):
    """Segment de transcription d'un live"""
    live = models.ForeignKey(
        Live,
        on_delete=models.CASCADE,
        related_name='transcriptions'
    )
    segment_number = models.PositiveIntegerField(
        help_text="Numéro du segment (ordre chronologique)"
    )
    text = models.TextField(
        help_text="Texte transcrit du segment audio"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Horodatage de la transcription"
    )

    class Meta:
        ordering = ['segment_number']
        unique_together = ('live', 'segment_number', 'timestamp')

    def __str__(self):
        return f"Segment {self.segment_number} - Live {self.live.id}"


class AnalyseDiscours(models.Model):
    """Analyse de discours d'une transcription"""

    CATEGORIE_CHOICES = [
        ('neutre', 'Neutre'),
        ('polemique', 'Polémique'),
        ('viral', 'Potentiellement viral'),
        ('haineux', 'Discours haineux'),
    ]

    VIRALITE_CHOICES = [
        ('faible', 'Faible'),
        ('moyenne', 'Moyenne'),
        ('forte', 'Forte'),
    ]

    transcription = models.OneToOneField(
        Transcription,
        on_delete=models.CASCADE,
        related_name='analyse'
    )
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES
    )
    viralite = models.CharField(
        max_length=10,
        choices=VIRALITE_CHOICES
    )
    discours_haineux = models.BooleanField(
        default=False,
        help_text="Indique si un discours haineux a été détecté"
    )
    cible = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cible du discours haineux (si détecté)"
    )
    justification = models.TextField(
        help_text="Explication de l'analyse"
    )
    risque_score = models.FloatField(
        help_text="Score de risque (0.0 à 1.0)"
    )
    date_analyse = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Analyse de discours"
        verbose_name_plural = "Analyses de discours"
        ordering = ['-risque_score', '-date_analyse']

    def __str__(self):
        return f"Analyse {self.transcription} - Score: {self.risque_score}"

    @property
    def niveau_risque(self):
        """Retourne le niveau de risque textuel"""
        if self.risque_score >= 0.7:
            return "Élevé"
        elif self.risque_score >= 0.4:
            return "Moyen"
        else:
            return "Faible"


class AlerteModeration(models.Model):
    """Alerte générée pour modération"""

    STATUT_CHOICES = [
        ('pending', 'En attente'),
        ('reviewed', 'Examinée'),
        ('action_taken', 'Action effectuée'),
        ('dismissed', 'Ignorée'),
    ]

    analyse = models.ForeignKey(
        AnalyseDiscours,
        on_delete=models.CASCADE,
        related_name='alertes'
    )
    admin_notifie = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='alertes_recues'
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='pending'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    action_effectuee = models.TextField(
        blank=True,
        help_text="Description de l'action prise"
    )
    traite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_traitees'
    )

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Alerte de modération"
        verbose_name_plural = "Alertes de modération"

    def __str__(self):
        return f"Alerte {self.id} - {self.statut} - Risque: {self.analyse.risque_score}"

