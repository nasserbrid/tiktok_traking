# ✅ Intégration IA - Résumé des modifications

## Ce qui a été fait

### 1. Modules IA intégrés ✅
```
tracking/ai/
├── __init__.py
├── transcript/
│   ├── __init__.py
│   └── transcriber.py (TikTokLiveTranscriber)
└── analyse/
    ├── __init__.py
    ├── analyzer.py
    ├── llm_client.py
    ├── utils.py
    └── template.yml
```

### 2. Nouveaux modèles Django ✅
- **Transcription** : Segments audio transcrits
- **AnalyseDiscours** : Résultats d'analyse IA
- **AlerteModeration** : Alertes pour admins

### 3. Service de transcription créé ✅
- [tracking/services/transcription_service.py](tracking/services/transcription_service.py)
- Gère le cycle de vie complet (start/stop)
- Callbacks pour transcription et analyse
- Création automatique d'alertes

### 4. Live Manager mis à jour ✅
- [tracking/managers/live_manager.py](tracking/managers/live_manager.py)
- Démarre automatiquement la transcription quand live détecté
- Arrête la transcription quand live terminé

### 5. Configuration Django ✅
- **settings.py** : Variables IA ajoutées
- **admin.py** : Interface admin pour tous les modèles
- **requirements.txt** : Dépendances IA ajoutées

---

## Prochaines étapes

### 1. Créer les migrations 🔄
```bash
python manage.py makemigrations tracking
python manage.py migrate
```

### 2. Configurer les variables d'environnement 📝
Ajouter dans votre [.env](.env) :
```env
# IA Configuration
API_KEY_GROQ=gsk_votre_cle_api_ici
WHISPER_MODEL=small
WHISPER_LANGUAGE=fr
RISK_THRESHOLD=0.7
```

### 3. Installer les dépendances IA 📦
```bash
pip install -r requirements.txt
```

**Note** : L'installation de Whisper et PyTorch peut prendre 10-15 minutes.

### 4. Installer FFmpeg ⚙️
**Windows** :
- Télécharger : https://ffmpeg.org/download.html
- Extraire et ajouter au PATH

**Linux/macOS** :
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

### 5. Obtenir une clé API Groq 🔑
1. Aller sur https://console.groq.com
2. Créer un compte
3. Générer une API key
4. Copier la clé dans `.env`

---

## Test de l'intégration

### Test 1 : Vérifier l'import
```python
python manage.py shell

from tracking.ai.analyse.analyzer import analyze_text

result = analyze_text("Bonjour, ceci est un test")
print(result)
# Devrait afficher un dict avec categorie, viralite, etc.
```

### Test 2 : Vérifier les modèles
```python
python manage.py shell

from tracking.models import Transcription, AnalyseDiscours, AlerteModeration
print("✅ Modèles importés avec succès")
```

### Test 3 : Accéder à l'admin
```bash
python manage.py runserver
```
Aller sur http://localhost:8000/admin et vérifier que les nouveaux modèles apparaissent.

---

## Structure de la solution IA

### Flux complet

```
Live détecté
    ↓
TikTokLiveTranscriber démarre
    ↓
Capture audio (15s par segment)
    ↓
Transcription (Whisper)
    ↓
Sauvegarde Transcription en BDD
    ↓
Analyse texte (Groq LLM)
    ↓
Sauvegarde AnalyseDiscours en BDD
    ↓
Si risque_score >= 0.7 → Création AlerteModeration
    ↓
Notification WebSocket aux admins
```

### Composants

1. **TikTokLiveTranscriber** (Whisper)
   - Modèles disponibles : tiny, base, small, medium, large
   - Capture segments de 15 secondes
   - Transcription en français (configurable)

2. **analyze_text()** (Groq LLM - LLaMA 3.3 70B)
   - Détection discours haineux
   - Classification (neutre, polémique, viral, haineux)
   - Score de viralité (faible, moyenne, forte)
   - Score de risque (0.0 - 1.0)

3. **TranscriptionService**
   - Gestion du cycle de vie
   - Callbacks automatiques
   - Création d'alertes

---

## Paramètres configurables

### Dans settings.py

```python
WHISPER_MODEL = 'small'  # Options: tiny, base, small, medium, large
WHISPER_LANGUAGE = 'fr'
RISK_THRESHOLD = 0.7  # Seuil d'alerte (0.0 à 1.0)
```

### Performance des modèles Whisper

| Modèle | Taille | RAM CPU | Temps/15s | Qualité |
|--------|--------|---------|-----------|---------|
| tiny   | 39 MB  | ~1 GB   | ~10s      | Basique |
| base   | 74 MB  | ~1 GB   | ~15s      | Correcte|
| small  | 244 MB | ~2 GB   | ~20s      | Bonne   |
| medium | 769 MB | ~5 GB   | ~40s      | Très bonne|
| large  | 1550 MB| ~10 GB  | ~60s      | Excellente|

**Recommandation** : `small` pour un bon équilibre qualité/performance.

---

## Fichiers modifiés

### ✅ Nouveaux fichiers
- `tracking/ai/` (tout le dossier)
- `tracking/services/transcription_service.py`
- `docs/` (documentation complète)

### ✅ Fichiers modifiés
- `tracking/models.py` (3 nouveaux modèles)
- `tracking/managers/live_manager.py` (intégration transcription)
- `tracking/admin.py` (admin pour nouveaux modèles)
- `core/settings.py` (config IA + logging)
- `requirements.txt` (dépendances IA)
- `.gitignore` (mis à jour)

---

## Déploiement sur Render

### Variables d'environnement à ajouter
Dans le dashboard Render, ajouter :
```
GROQ_API_KEY=gsk_...
WHISPER_MODEL=small
WHISPER_LANGUAGE=fr
RISK_THRESHOLD=0.7
```

### Build Command
```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

**Important** : FFmpeg doit être installé sur le serveur Render. Pour cela :
1. Créer un fichier `render.yaml` avec installation FFmpeg
2. Ou utiliser un buildpack FFmpeg

---

## Limitations actuelles

1. **Pas d'interface de modération** (vues et templates à créer)
2. **Transcription nécessite un live actif** (ne peut pas tester sans vrai live)
3. **FFmpeg requis** (installation système nécessaire)
4. **Quotas Groq API** (gratuit mais limité)

---

## Documentation complète

Voir le dossier [docs/](docs/) pour la documentation exhaustive :
- [01_PRESENTATION_PROJET.md](docs/01_PRESENTATION_PROJET.md)
- [02_ARCHITECTURE_TECHNIQUE.md](docs/02_ARCHITECTURE_TECHNIQUE.md)
- [03_GUIDE_INTEGRATION_IA.md](docs/03_GUIDE_INTEGRATION_IA.md)

---

**Date d'intégration** : 2025-12-26
**Statut** : ✅ Code intégré - En attente de tests et déploiement
**Développeur** : Claude (Assistant IA)
