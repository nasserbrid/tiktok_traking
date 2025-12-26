# Documentation TikTok Tracking

## Vue d'ensemble

Cette documentation technique complète décrit l'application **TikTok Tracking**, une solution de surveillance et d'analyse des activités TikTok destinée à un usage gouvernemental.

---

## Structure de la documentation

### 📋 [01 - Présentation du Projet](01_PRESENTATION_PROJET.md)

**Description complète du projet** incluant :
- Contexte et objectifs
- Fonctionnalités principales
- Stack technologique
- Modèle de données
- Flux utilisateur
- Architecture de la solution IA
- Limitations et améliorations futures
- Sécurité et conformité
- Configuration de déploiement

**À lire en premier** pour comprendre le projet dans son ensemble.

---

### 🏗️ [02 - Architecture Technique](02_ARCHITECTURE_TECHNIQUE.md)

**Documentation technique détaillée** couvrant :
- Structure complète du projet
- Description des apps Django (core, authentication, tracking, notifications)
- Modèles de données détaillés
- Services et managers
- WebSocket et temps réel
- Système de détection de lives
- Architecture IA (transcription et analyse)
- Configuration système
- Performance et optimisation

**Pour les développeurs** qui veulent comprendre l'architecture en profondeur.

---

### 🔧 [03 - Guide d'Intégration IA](03_GUIDE_INTEGRATION_IA.md)

**Guide pas à pas** pour intégrer la solution IA :
- Prérequis (FFmpeg, Python, Groq API)
- Installation des dépendances
- Intégration étape par étape (10+ étapes)
- Configuration complète
- Création des modèles Django
- Services de transcription
- Vues de modération
- Templates d'interface
- Tests et validation
- Déploiement en production
- Troubleshooting

**Pour l'intégration** de la solution IA dans l'application existante.

---

## Démarrage rapide

### Pour comprendre le projet

1. Lire [01_PRESENTATION_PROJET.md](01_PRESENTATION_PROJET.md)
2. Consulter la section "Flux utilisateur"
3. Examiner le schéma de base de données

### Pour développer

1. Lire [02_ARCHITECTURE_TECHNIQUE.md](02_ARCHITECTURE_TECHNIQUE.md)
2. Explorer la section "Apps Django"
3. Consulter les services et managers

### Pour intégrer l'IA

1. Suivre [03_GUIDE_INTEGRATION_IA.md](03_GUIDE_INTEGRATION_IA.md)
2. Compléter la checklist étape par étape
3. Tester avec les exemples fournis

---

## État actuel du projet

### ✅ Fonctionnalités implémentées

- Authentification utilisateurs (inscription, connexion, réinitialisation mot de passe)
- Gestion des comptes TikTok (ajout, suppression, consultation)
- Détection de lives en temps réel (via TikTokLive API)
- Système de notifications WebSocket
- Historique des lives détectés
- Interface utilisateur responsive (Bootstrap 5)
- Déploiement sur Render (PostgreSQL + Redis)

### 🚧 À intégrer

- **Solution IA de transcription** (OpenAI Whisper)
- **Analyse de discours** (Groq LLM - LLaMA 3.3 70B)
- **Interface de modération** pour administrateurs
- **Système d'alertes** basé sur score de risque
- **Stockage des transcriptions** et analyses en base de données

### 🎯 Prochaines étapes

1. **Intégrer la solution IA** (voir guide d'intégration)
2. **Activer Celery** pour détection périodique en background
3. **Créer l'interface de modération** complète
4. **Optimiser les performances** (GPU pour Whisper, cache Redis)
5. **Tester en conditions réelles** avec des lives TikTok
6. **Déployer la version complète** pour présentation investisseurs

---

## Technologies utilisées

### Backend
- **Django 5.2.7** - Framework web Python
- **Django Channels 4.3.1** - Support WebSocket
- **Celery 5.4.0** - Tâches asynchrones
- **PostgreSQL** - Base de données
- **Redis** - Cache et message broker

### IA
- **OpenAI Whisper** - Transcription audio (speech-to-text)
- **Groq API (LLaMA 3.3 70B)** - Analyse de discours
- **FFmpeg** - Capture audio des lives
- **PyTorch** - Framework ML pour Whisper

### APIs
- **TikTokLive 6.6.5** - Détection de lives TikTok
- **TikTok WebCast API** - Accès aux flux audio

### Infrastructure
- **Render** - Hébergement (PaaS)
- **Gunicorn** - Serveur WSGI
- **WhiteNoise** - Serveur de fichiers statiques

---

## Structure des fichiers de documentation

```
docs/
├── README.md                      # Ce fichier (index)
├── 01_PRESENTATION_PROJET.md      # Vue d'ensemble du projet
├── 02_ARCHITECTURE_TECHNIQUE.md   # Architecture détaillée
└── 03_GUIDE_INTEGRATION_IA.md     # Guide d'intégration IA
```

---

## Ressources externes

### Documentation officielle
- Django : https://docs.djangoproject.com/
- Django Channels : https://channels.readthedocs.io/
- Celery : https://docs.celeryproject.org/

### Librairies utilisées
- TikTokLive : https://github.com/isaackogan/TikTokLive
- OpenAI Whisper : https://github.com/openai/whisper
- Groq : https://console.groq.com/docs

### Repositories
- Application principale : `tiktok_traking/` (votre repository local)
- Solution IA : https://github.com/ohamjoseph/transcript_ttt

---

## Conventions de code

### Python
- Style : PEP 8
- Docstrings : Google style
- Type hints recommandés

### Django
- Apps : snake_case (ex: `tracking`, `notifications`)
- Modèles : PascalCase (ex: `CompteTiktok`, `Live`)
- Vues : snake_case avec suffixe descriptif (ex: `liste_comptes`, `ajouter_compte`)

### Templates
- Nommage : snake_case (ex: `liste_comptes.html`)
- Organisation : par app (`templates/tracking/`, `templates/authentication/`)

### JavaScript
- Variables : camelCase
- Fonctions : camelCase
- Constantes : UPPER_SNAKE_CASE

---

## Glossaire

| Terme | Définition |
|-------|------------|
| **Live** | Session de diffusion en direct sur TikTok |
| **Room ID** | Identifiant unique d'une room de live TikTok |
| **Transcription** | Segment de texte transcrit depuis l'audio d'un live |
| **Analyse de discours** | Résultat de l'analyse IA d'une transcription |
| **Score de risque** | Valeur de 0.0 à 1.0 indiquant le niveau de risque d'un contenu |
| **Alerte de modération** | Notification envoyée aux admins pour contenu à risque élevé |
| **WebSocket** | Protocole de communication bidirectionnelle en temps réel |
| **Channel Layer** | Système de messaging Django Channels (via Redis) |
| **Celery** | Framework de tâches asynchrones Python |
| **Whisper** | Modèle de transcription audio open-source d'OpenAI |
| **Groq** | Plateforme d'inférence LLM ultra-rapide |

---

## Contact et support

### Équipe
- **Développeur principal** : Vous (conception et développement complet)
- **Développeur IA** : Votre associé (ohamjoseph - solution transcription/analyse)

### Pour toute question
- Consulter d'abord cette documentation
- Vérifier les logs applicatifs (`logs/`)
- Consulter les issues GitHub de la solution IA

---

## Licence et usage

**Usage gouvernemental** - Application destinée à un usage officiel dans le cadre de la modération de contenus TikTok.

**Considérations légales** :
- Respect du RGPD pour le traitement des données
- Cadre légal requis pour l'enregistrement et l'analyse de contenus
- Responsabilité juridique pour les actions de modération

⚠️ **Recommandation** : Consultation juridique avant déploiement officiel en production.

---

## Changelog

### Version 1.0 (2025-12-26)
- ✅ Documentation initiale créée
- ✅ Architecture existante documentée
- ✅ Guide d'intégration IA rédigé
- ✅ MVP déployé sur Render
- 🚧 Intégration IA en attente

---

**Documentation générée le** : 2025-12-26
**Version** : 1.0
**Statut** : MVP déployé - Intégration IA documentée et prête
