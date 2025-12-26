# TikTok Tracking - Documentation Complète

## Vue d'ensemble du projet

### Contexte et Objectif

**TikTok Tracking** est une application de surveillance et d'analyse des activités TikTok destinée à un usage gouvernemental. L'application permet de monitorer en temps réel des comptes TikTok spécifiques, détecter les lives actifs, transcrire automatiquement le contenu audio, analyser le discours pour identifier les propos haineux ou virulents, et envoyer des alertes automatiques aux administrateurs.

### Informations générales

- **Type d'application** : Application web Django avec WebSocket
- **Équipe** : 2 personnes
  - Vous : Conception et développement complet de l'application
  - Associé : Développement de la solution IA (transcription + analyse)
- **État actuel** : MVP déployé sur Render
- **URL de production** : https://tiktok-traking.onrender.com/
- **Phase** : Prêt pour présentation aux investisseurs
- **Prochaine étape** : Intégration de la solution IA

---

## Fonctionnalités principales

### 1. Gestion des comptes TikTok

- Ajout/suppression de comptes TikTok à surveiller
- Visualisation de la liste des comptes suivis
- Consultation de l'historique des lives par compte
- Contrainte : Un utilisateur ne peut pas suivre le même compte deux fois

### 2. Détection de lives en temps réel

- Surveillance automatique des comptes suivis
- Détection instantanée du démarrage d'un live
- Mise à jour du statut des comptes :
  - En ligne (live actif)
  - Actif (compte en ligne sans live)
  - Hors ligne

### 3. Système de notifications temps réel

- Notifications WebSocket pour alertes instantanées
- Broadcast à tous les utilisateurs connectés
- Historique des notifications consultable
- Interface non-intrusive

### 4. Statistiques et historique

- Historique complet des lives détectés
- Date de début et fin de chaque live
- Nombre de spectateurs
- Titre du live
- Durée des lives

### 5. Authentification sécurisée

- Système de connexion/inscription
- Gestion des rôles (Admin/Utilisateur)
- Réinitialisation de mot de passe
- Validation des mots de passe (minimum 8 caractères, au moins une lettre)

### 6. Solution IA (à intégrer)

#### Transcription automatique (Whisper)
- Capture audio des lives TikTok en temps réel
- Transcription automatique par segments de 15 secondes
- Support multilingue (français par défaut)
- Gestion des silences et erreurs
- Logs et métriques détaillées

#### Analyse de discours (LLM via Groq)
- Détection de discours haineux
- Classification du contenu :
  - Neutre
  - Polémique
  - Potentiellement viral
  - Discours haineux
- Évaluation du niveau de viralité (faible/moyenne/forte)
- Identification des cibles (ethnie, religion, groupe social, etc.)
- Score de risque calculé automatiquement

---

## Architecture technique

### Stack technologique

**Backend**
- Django 5.2.7 (Framework web Python)
- Django Channels 4.3.1 (WebSocket support)
- PostgreSQL (Base de données)
- Redis (Message broker pour WebSocket)
- Celery 5.4.0 (Tâches asynchrones - actuellement désactivé)
- Gunicorn 23.0.0 (Serveur WSGI)

**Frontend**
- Bootstrap 5 (Framework CSS)
- JavaScript vanilla (WebSocket client)
- Templates Django

**APIs et Librairies**
- TikTokLive 6.6.5 (Détection de lives)
- OpenAI Whisper (Transcription audio)
- Groq API avec LLaMA 3.3 70B (Analyse de texte)
- FFmpeg (Capture audio)

**Infrastructure**
- Hébergement : Render (PaaS)
- Base de données : PostgreSQL sur Render
- Cache/Message Broker : Redis
- Serveur de fichiers statiques : WhiteNoise

### Architecture applicative

L'application est structurée en 4 apps Django principales :

1. **authentication/** : Gestion des utilisateurs
2. **tracking/** : Surveillance des comptes TikTok
3. **notifications/** : Système de notifications WebSocket
4. **core/** : Configuration du projet

---

## Modèle de données

### Schéma de base de données

```
┌─────────────────────────┐
│   authentication_user   │
├─────────────────────────┤
│ id (PK)                 │
│ username (UNIQUE)       │
│ email                   │
│ password                │
│ first_name              │
│ last_name               │
│ role (ADMIN/USER)       │
│ date_joined             │
└─────────────────────────┘
           │ 1
           │
           │ N
┌─────────────────────────┐
│ tracking_comptetiktok   │
├─────────────────────────┤
│ id (PK)                 │
│ user_id (FK)            │
│ username                │
│ url                     │
│ date_creation           │
│ nb_followers            │
│ UNIQUE(user_id,username)│
└─────────────────────────┘
           │ 1
           │
           │ N
┌─────────────────────────┐
│   tracking_live         │
├─────────────────────────┤
│ id (PK)                 │
│ compte_id (FK)          │
│ titre                   │
│ date_debut              │
│ date_fin                │
│ nb_spectateurs          │
│ statut (en_cours/fini)  │
└─────────────────────────┘
           │ 1
           │
           │ N
┌─────────────────────────┐
│notifications_notification│
├─────────────────────────┤
│ id (PK)                 │
│ user_id (FK)            │
│ live_id (FK)            │
│ message                 │
│ is_read                 │
│ date_created            │
└─────────────────────────┘
```

---

## Flux utilisateur

### 1. Inscription et connexion

```
┌─────────┐
│  Signup │ → Validation → Enregistrement User → Redirection Login
└─────────┘

┌───────┐
│ Login │ → Authentification → Session → Dashboard
└───────┘
```

### 2. Ajout d'un compte TikTok

```
Dashboard → Ajouter un compte → Saisie @username
    ↓
Validation (compte non déjà suivi)
    ↓
Création CompteTiktok (URL auto-générée)
    ↓
Redirection Dashboard (compte visible)
```

### 3. Détection de live (flux actuel)

```
Chargement Dashboard
    ↓
Pour chaque compte :
    ↓
is_live(username) via TikTokLiveClient
    ↓
┌─ Live détecté → Création Live record (statut='en_cours')
│                     ↓
│                 Trigger notification
│                     ↓
│                 WebSocket broadcast
│
└─ Pas de live → Si Live actif existe → Marquer 'termine'
```

### 4. Flux de notification WebSocket

```
Détection Live
    ↓
update_live_status(compte, live_detected=True)
    ↓
channel_layer.group_send("lives", {...})
    ↓
LiveNotificationConsumer.live_notification(event)
    ↓
WebSocket send(JSON) → Client JavaScript
    ↓
Affichage notification utilisateur
```

---

## Architecture de la solution IA (à intégrer)

### Composants de la solution IA

La solution développée par votre associé est structurée en 2 modules principaux :

#### 1. Module `transcript/` - Transcription audio

**Fichier principal** : `transcript.py`

**Classe** : `TikTokLiveTranscriber`

**Fonctionnement** :
1. Récupère l'URL du flux audio via l'API TikTok WebCast
2. Capture des segments audio de 15 secondes avec FFmpeg
3. Transcription via OpenAI Whisper (modèle configurable : tiny/small/medium/large)
4. Gestion alternée de 2 fichiers (A/B) pour traitement parallèle
5. Callbacks pour chaque transcription

**Caractéristiques** :
- Asynchrone (threading Python)
- Gestion automatique des erreurs et timeouts
- Retry automatique en cas d'expiration d'URL
- Métriques détaillées (segments traités, taux de succès, durée)
- Logging complet dans `logs/`

#### 2. Module `analyse/` - Analyse de discours

**Fichier principal** : `analyzer.py`

**Fonction** : `analyze_text(text: str) -> dict`

**Fonctionnement** :
1. Chargement du prompt depuis `template.yml`
2. Injection du texte transcrit dans le prompt
3. Appel à l'API Groq (LLaMA 3.3 70B)
4. Parsing de la réponse JSON
5. Calcul du score de risque (0.0 à 1.0)

**Résultat retourné** :
```json
{
  "categorie": "Neutre | Polémique | Potentiellement viral | Discours haineux",
  "viralite": "faible | moyenne | forte",
  "discours_haineux": true/false,
  "cible": "ethnie | religion | individu | groupe social | autre",
  "justification": "Explication contextuelle",
  "risque_score": 0.0 - 1.0
}
```

**Algorithme de scoring** :
- Base : 0.2
- Viralité moyenne : +0.3
- Viralité forte : +0.5
- Discours haineux détecté : +0.4
- Score max plafonné à 1.0

### Flux complet avec IA

```
Live détecté sur TikTok
    ↓
Connexion au live (TikTokLiveClient)
    ↓
TikTokLiveTranscriber.start()
    ↓
┌─ Boucle toutes les 15s :
│     ↓
│   Capture audio (FFmpeg)
│     ↓
│   Transcription (Whisper)
│     ↓
│   Callback : my_callback(text, segment, unique_id)
│     ↓
│   analyze_text(text) via Groq LLM
│     ↓
│   Résultat analyse JSON
│     ↓
│   Si risque_score > seuil → ALERTE
│     ↓
└─ Retour à la capture

Si discours haineux détecté :
    ↓
Notification admin + Arrêt possible du live
```

---

## Points d'intégration nécessaires

### Changements requis dans l'application Django

1. **Nouveaux modèles** (dans `tracking/models.py`) :
   - `Transcription` : Stocker les segments transcrits
   - `AnalyseDiscours` : Résultats de l'analyse IA

2. **Nouveau service** (dans `tracking/services/`) :
   - `transcription_service.py` : Wrapper pour TikTokLiveTranscriber
   - Gestion du cycle de vie (start/stop)
   - Callbacks vers Django

3. **Mise à jour de `live_manager.py`** :
   - Démarrer transcription quand live détecté
   - Stopper transcription quand live terminé

4. **Nouvelles vues** :
   - Affichage des transcriptions par live
   - Visualisation des analyses de risque
   - Dashboard de modération

5. **Variables d'environnement** :
   - `GROQ_API_KEY` : Clé API Groq
   - `WHISPER_MODEL` : Modèle Whisper (tiny/small/medium/large)
   - `RISK_THRESHOLD` : Seuil d'alerte (0.0-1.0)

6. **Dépendances** (requirements.txt) :
   - openai-whisper==20250625
   - torch==2.9.1
   - ffmpeg-python==0.2.0
   - groq (API client)
   - pyyaml (pour template.yml)

---

## Limitations et améliorations futures

### Limitations actuelles

1. **Performance** :
   - Détection synchrone sur chargement de page (bloquant)
   - Celery désactivé (pas de détection périodique automatique)
   - 1 seul worker Gunicorn

2. **WebSocket** :
   - Broadcast global (pas de ciblage par utilisateur)
   - Pas de persistance de connexion

3. **Scalabilité** :
   - Architecture non optimisée pour grand volume
   - Pas de cache
   - Pas de CDN pour statiques

4. **IA** :
   - Solution IA non intégrée
   - Pas de stockage des transcriptions
   - Pas d'interface de modération

### Améliorations recommandées

#### Court terme (MVP amélioré)
- ✅ Intégrer la solution IA
- ✅ Activer Celery pour détection périodique
- ✅ Ajouter interface de modération
- ✅ Stocker les transcriptions et analyses
- ✅ Implémenter système d'alertes par seuil

#### Moyen terme
- Optimiser WebSocket (canal par utilisateur)
- Augmenter workers Gunicorn
- Ajouter cache Redis pour données fréquentes
- Implémenter pagination
- Ajouter exports CSV/PDF
- Dashboard analytique avancé

#### Long terme
- Migration vers architecture microservices
- Séparation transcription/analyse en service dédié
- API REST pour intégrations tierces
- ML custom pour détection (fine-tuning)
- Support multi-plateformes (YouTube, Instagram, etc.)
- Archivage automatique des lives

---

## Sécurité et conformité

### Mesures de sécurité implémentées

- Authentification requise pour toutes les pages
- Validation des mots de passe (complexité)
- Protection CSRF (Django middleware)
- Sessions sécurisées
- Variables sensibles en environnement
- HTTPS forcé en production

### Considérations légales

- **RGPD** : Traitement de données personnelles (comptes publics TikTok)
- **Droits d'auteur** : Enregistrement de contenus TikTok
- **Usage gouvernemental** : Cadre légal requis
- **Modération** : Responsabilité de l'action (arrêt de live)

**Recommandation** : Consultation juridique avant déploiement officiel

---

## Déploiement

### Configuration actuelle (Render)

**Procfile** :
```
web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers=1 --threads=2
```

**Variables d'environnement requises** :
- `SECRET_KEY`
- `DEBUG` (False en production)
- `ALLOWED_HOSTS`
- `DATABASE_URL` (PostgreSQL)
- `REDIS_URL`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DOMAIN`

**Services nécessaires** :
- Web service (Gunicorn)
- PostgreSQL database
- Redis instance

### Configuration post-intégration IA

**Nouvelles variables** :
- `GROQ_API_KEY`
- `WHISPER_MODEL` (default: small)
- `RISK_THRESHOLD` (default: 0.7)

**Dépendances système** :
- FFmpeg installé sur serveur
- CUDA (optionnel, pour Whisper GPU)

**Procfile étendu** :
```
web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers=2 --threads=4 --timeout=120
worker: celery -A core worker -l info
beat: celery -A core beat -l info
```

---

## Ressources utiles

### Documentation technique
- Django : https://docs.djangoproject.com/
- Django Channels : https://channels.readthedocs.io/
- TikTokLive : https://github.com/isaackogan/TikTokLive
- Whisper : https://github.com/openai/whisper
- Groq : https://console.groq.com/docs

### Repositories
- Application principale : (votre repository)
- Solution IA : https://github.com/ohamjoseph/transcript_ttt

### Contact
- Développeur principal : Vous
- Développeur IA : Votre associé (ohamjoseph)

---

**Document généré le** : 2025-12-26
**Version** : 1.0
**Statut** : MVP déployé - Intégration IA en attente
