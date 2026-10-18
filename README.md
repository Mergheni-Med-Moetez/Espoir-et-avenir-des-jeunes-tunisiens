# 🇹🇳 Tunisian Hope & Future — Espoir et Avenir des Jeunes Tunisiens

Bienvenue dans le dépôt officiel du projet **Tunisian Hope & Future for Children and Youth** (Projet d'Examen Django — SESAME University 2025–2026).

Plateforme d'intervention et d'accompagnement social pour la jeunesse tunisienne, axée sur la détection précoce des risques scolaires (décrochage/absentéisme) et médicaux (adhérence aux soins).

---

## 📁 Structure du Projet

```text
.
├── co files/                  # Sujet officiel de l'examen et grille d'évaluation
│   ├── evaluation_grid_django_exam_2025_2026_Chaouki_Bayoudhi.pdf
│   └── exam_Project_python_web_programming_Djnago_Chaouki_Bayoudhi_2026.pdf
├── data-gen.py                # Script autonome de génération du jeu de données synthétique
├── students_data.csv          # Données synthétiques générées (50+ profils étudiants)
├── pdf rapport/               # Exemples de rapports d'intervention IA générés en PDF
│   ├── ai_report_CASE-2026-00400.pdf
│   └── ai_report_CASE-2026-00402.pdf
└── tunisian_hope/             # Application Web Django principale
    ├── apps/                  # Applications Django modulaires (core, education, health, dashboard)
    ├── config/                # Configuration Django (settings, URLs, GraphQL schema)
    ├── docs/                  # Documentation complémentaire du projet
    ├── static/                # Fichiers statiques (CSS, JS, images)
    ├── templates/             # Templates HTML (Bootstrap 5)
    ├── db.sqlite3             # Base de données SQLite préconfigurée avec données de démo
    ├── manage.py              # Point d'entrée de gestion Django
    ├── pytest.ini             # Configuration des tests Pytest
    ├── requirements.txt       # Dépendances Python du projet
    └── README.md              # Documentation détaillée de l'application Django
```

---

## 🚀 Guide Rapide de Démarrage

### 1. Cloner le Projet
```bash
git clone https://github.com/Mergheni-Med-Moetez/Espoir-et-avenir-des-jeunes-tunisiens.git
cd Espoir-et-avenir-des-jeunes-tunisiens/tunisian_hope
```

### 2. Installer les Dépendances
```bash
pip install -r requirements.txt
```

### 3. Exécuter les Migrations (si nécessaire)
*(Le fichier `db.sqlite3` pré-rempli est déjà inclus, cette étape est facultative pour tester directement)*
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Comptes de Démonstration (RBAC)
Le projet intègre des comptes préconfigurés avec le mot de passe `demo1234` :
* **Field Operator** : `operator`
* **Supervisor** : `supervisor`
* **System Admin** : `admin_user`

Pour réinitialiser les groupes et utilisateurs :
```bash
python manage.py seed_groups --with-users
```

### 5. Lancer le Serveur Django
```bash
python manage.py runserver
```
Accédez à l'application sur : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 6. Lancer les Tests Automatisés
```bash
pytest
```
*Exécute la suite de tests (66 tests réussis), incluant les tests unitaires, d'intégration, de sécurité et d'injection de panne (Failure Injection).*

---

## 🌟 Fonctionnalités Clés

1. **Architecture "Fat Models, Thin Views"** : Logique métier et validation encapsulées dans les modèles.
2. **Machine à États Stricte (Workflow des Cas)** :
   `INTAKE` ➔ `ASSESSMENT` ➔ `ACTIVE_INTERVENTION` ➔ `FOLLOW_UP` ➔ `CLOSED` avec traçabilité complète dans `AuditLog`.
3. **2 Scénarios Métiers Validés** :
   - **Éducation** : Détection automatique de l'absentéisme et du risque de décrochage.
   - **Santé** : Suivi de l'adhérence aux soins et détection des rendez-vous manqués.
4. **API GraphQL (Strawberry)** : Endpoint `/graphql/` avec GraphiQL interactif et contrôle d'accès par décorateur.
5. **Agent IA Local & Export PDF** : Support LLM local (Ollama/llama3) avec fallback simulé et génération de rapports PDF via ReportLab.
6. **Fiabilité & Failure Injection** : Résilience face aux pannes testée via transactions atomiques (`transaction.atomic`).

---

## 👤 Auteur

* **Mohamed Moetez Mergheni** — SESAME University
