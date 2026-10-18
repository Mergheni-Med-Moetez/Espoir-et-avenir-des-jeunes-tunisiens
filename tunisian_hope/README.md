# Tunisian Hope & Future — Documentation du Projet

Bienvenue dans la documentation officielle du projet **Tunisian Hope & Future**. Ce document offre une vue d'ensemble complète de l'architecture, des fonctionnalités et des instructions d'installation pour cette plateforme à impact social.

---

## 📖 Sommaire

1. [Présentation du Projet](#1-présentation-du-projet)
2. [Choix Architecturaux et Technologies](#2-choix-architecturaux-et-technologies)
3. [Gestion des Rôles (RBAC)](#3-gestion-des-rôles-rbac)
4. [Scénarios Métiers (Éducation & Santé)](#4-scénarios-métiers-éducation--santé)
5. [Machine à États (Workflow des Cas)](#5-machine-à-états-workflow-des-cas)
6. [Intégration Avancée : API GraphQL](#6-intégration-avancée--api-graphql)
7. [Intégration Avancée : Agent IA & Export PDF](#7-intégration-avancée--agent-ia--export-pdf)
8. [Fiabilité et Tests (Failure Injection)](#8-fiabilité-et-tests-failure-injection)
9. [Guide d'Installation et d'Exécution](#9-guide-dinstallation-et-dexécution)

---

## 1. Présentation du Projet

**Tunisian Hope & Future** est une plateforme de gestion de cas orientée vers l'impact social en Tunisie. Elle met en œuvre une architecture **"Fat Models, Thin Views"** et une machine à états stricte pour gérer les cas d'assistance dans 2 scénarios métiers :
1. **Éducation** : Détection de l'absentéisme et du décrochage scolaire.
2. **Santé** : Suivi des soins, de l'adhérence médicale et des rendez-vous manqués.

Le but principal est de fournir un tableau de bord en temps réel pour détecter les comportements à risque et déclencher des interventions adaptées à travers un système hiérarchique de rôles et une assistance IA (Agent-based support).

---

## 2. Choix Architecturaux et Technologies

Pour répondre aux exigences de scalabilité, de maintenabilité et de sécurité (niveau de l'examen final), nous avons opté pour la pile technologique suivante :

*   **Backend Framework** : Django 5.2.14 (Python 3.11+)
    *   *Justification* : L'ORM robuste de Django et son système d'authentification garantissent un développement sécurisé.
*   **Base de Données** : PostgreSQL / SQLite
    *   *Justification* : Base de données relationnelle pour gérer l'intégrité de la Machine à États et la concurrence.
*   **API / Intégration** : Strawberry GraphQL
    *   *Justification* : Résout le problème du "Over-fetching" des APIs REST traditionnelles grâce à des requêtes fortement typées (Python 3.11 dataclasses).
*   **Agent IA Local** : Ollama (llama3) + LangChain
    *   *Justification* : Protection totale de la confidentialité des données (Privacy by Design). Les données des étudiants ne quittent jamais le serveur local.
*   **Frontend / UI** : Bootstrap 5 (CDN) + Django Templates
    *   *Justification* : Approche "Server-Side Rendering" classique (Architecture Monolithique) pour une interface réactive et légère sans la complexité d'un framework JS.
*   **Export de données** : ReportLab (Génération PDF)
*   **Tests** : Pytest + Django-Pytest

---

## 3. Gestion des Rôles (RBAC)

Le système implémente un contrôle d'accès basé sur les rôles (Role-Based Access Control) avec une ségrégation stricte des permissions :

| Rôle | Description |
|------|-------------|
| **Field Operator** | Utilisateur sur le terrain. Crée les cas (`INTAKE`) et renseigne les données initiales. Ne voit que ses propres cas. |
| **Supervisor** | Validation finale, visualisation des tableaux de bord agrégés et gestion des alertes IA. Valide le passage à `CLOSED`. |
| **System Admin** | Configuration système, accès à l'interface d'administration Django et aux journaux d'audit (`AuditLog`). |

---

## 4. Scénarios Métiers (Éducation & Santé)

Le projet valide officiellement **2 Scénarios** avec leurs moteurs de règles respectifs :

**Scénario 1 : Éducation (Early Warning)**
*   **Indicateurs** : Taux de présence (`attendance_rate` < 85%), tendance des notes, rapports de comportement.
*   **Action** : Si le score de risque global dépasse le seuil, le statut de l'étudiant passe automatiquement de `INTAKE` à `ASSESSMENT` et génère une Alerte.

**Scénario 2 : Suivi de Santé (Health Follow-up)**
*   **Indicateurs** : Taux d'adhérence aux traitements (`adherence_rate`), nombre de rendez-vous manqués (`missed_appointments`).
*   **Action** : Détecte les abandons de soins chroniques ou mentaux et génère automatiquement des Alertes de Santé prioritaires pour le Superviseur.

---

## 5. Machine à États (Workflow des Cas)

Chaque entité gérée par la plateforme est liée à un `Case` (Cas). Ce cas traverse un cycle de vie strict (State Machine) garanti par le code et testé via injection d'erreurs :

```text
[INTAKE] ---> [ASSESSMENT] ---> [ACTIVE_INTERVENTION] ---> [FOLLOW_UP] ---> [CLOSED]
```

**Règles de sécurité :**
*   Il est interdit de sauter des étapes (ex: Intake vers Closed est bloqué).
*   Chaque changement d'état est immuable et génère une entrée non modifiable dans la table `AuditLog` (Traçabilité complète).

---

## 6. Intégration Avancée : API GraphQL

L'API GraphQL permet aux systèmes externes (ou à un futur frontend découplé) de requêter précisément les données :
*   **Endpoint** : `/graphql/` (Interface GraphiQL interactive disponible)
*   **Sécurité** : Intègre un décorateur personnalisé de permissions. Seuls les Superviseurs et Admins peuvent exécuter les requêtes de KPI comme `educationDashboard`.

---

## 7. Intégration Avancée : Agent IA & Export PDF

Pour satisfaire le parcours **Advanced AI/LLM** (Track F), la plateforme intègre un **Assistant IA à la Demande** :
1.  **Tableau de bord des Alertes :** Les Superviseurs reçoivent les alertes générées par le moteur de règles.
2.  **Prompt Engineering Dynamique :** En un clic, l'agent extrait les données du cas (Éducation ou Santé) et génère un rapport d'intervention personnalisé.
3.  **Fallback Mécanisme :** Si l'IA locale (Ollama) est hors ligne, le système génère un "Rapport Simulé" pour garantir la continuité des démonstrations.
4.  **Export PDF :** Une fois le rapport généré, il est exportable instantanément en fichier PDF formaté professionnellement.

---

## 8. Fiabilité et Tests (Failure Injection)

La fiabilité est prouvée par une suite de 66 tests automatisés. Nous avons mis en place une méthode de **Failure Injection** (`test_failure_injection.py`) requise par l'examen :

Nous simulons intentionnellement un crash de la base de données au milieu d'une mise à jour de statut. Grâce à l'utilisation de `transaction.atomic`, le système effectue un **rollback sécurisé** et évite toute corruption de données.

---

## 9. Guide d'Installation et d'Exécution

Voici les commandes pour exécuter et tester le projet localement :

**1. Prérequis :**
Assurez-vous d'avoir Python 3.11+ et installez les dépendances :
```bash
pip install -r requirements.txt
```

**2. Effectuer les Migrations :**
```bash
python manage.py makemigrations
python manage.py migrate
```

**3. Générer les Rôles et Utilisateurs par Défaut :**
```bash
python manage.py seed_groups --with-users
```
*(Ceci crée les utilisateurs: `operator`, `supervisor`, `admin_user` avec le mot de passe: `demo1234`)*

**4. Générer les Données Synthétiques et Déclencher les Alertes :**
```bash
python manage.py generate_synthetic_data --flush --count 50
```
*(Cette commande crée 50 étudiants, génère leurs dossiers de santé, exécute le moteur de risque, et crée les Alertes pour l'IA)*

**5. Lancer le Serveur Web :**
```bash
python manage.py runserver
```

**6. Lancer la Suite de Tests Complète :**
Dans un terminal séparé, exécutez pytest :
```bash
pytest
```
*(Affiche 66 tests réussis, incluant les tests de sécurité et de failure injection)*
