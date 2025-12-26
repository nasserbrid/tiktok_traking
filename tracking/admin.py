from django.contrib import admin
from .models import CompteTiktok, Live, Transcription, AnalyseDiscours, AlerteModeration


@admin.register(CompteTiktok)
class CompteTiktokAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'url', 'nb_followers', 'date_creation', 'en_live')
    list_filter = ('date_creation', 'user')
    search_fields = ('username', 'user__username')
    readonly_fields = ('date_creation',)


@admin.register(Live)
class LiveAdmin(admin.ModelAdmin):
    list_display = ('titre', 'compte', 'date_debut', 'date_fin', 'statut', 'nb_spectateurs')
    list_filter = ('statut', 'date_debut')
    search_fields = ('titre', 'compte__username')
    readonly_fields = ('date_debut',)


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ('live', 'segment_number', 'timestamp', 'text_preview')
    list_filter = ('live__compte__username', 'timestamp')
    search_fields = ('text',)
    readonly_fields = ('timestamp',)

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Aperçu'


@admin.register(AnalyseDiscours)
class AnalyseDiscoursAdmin(admin.ModelAdmin):
    list_display = ('transcription', 'categorie', 'viralite', 'discours_haineux', 'risque_score', 'niveau_risque', 'date_analyse')
    list_filter = ('categorie', 'viralite', 'discours_haineux', 'date_analyse')
    search_fields = ('justification', 'cible')
    readonly_fields = ('date_analyse',)


@admin.register(AlerteModeration)
class AlerteModerationAdmin(admin.ModelAdmin):
    list_display = ('id', 'analyse_info', 'statut', 'admin_notifie', 'date_creation', 'traite_par')
    list_filter = ('statut', 'date_creation')
    search_fields = ('analyse__transcription__live__compte__username',)
    readonly_fields = ('date_creation',)

    def analyse_info(self, obj):
        return f"Risque: {obj.analyse.risque_score} - {obj.analyse.transcription.live.compte.username}"
    analyse_info.short_description = 'Analyse'
