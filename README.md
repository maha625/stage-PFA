# 🎓 Projet de Fin d'Année (PFA) — Intégration et Développement Odoo ERP

Ce dépôt contient le **code source**, les **modules personnalisés** ainsi que la **documentation technique** relatifs à mon **Projet de Fin d'Année (PFA)**, réalisé dans le cadre de mon cycle d'ingénieur en **Informatique et Systèmes Intelligents à l'ENSAM Meknès**.

Le projet consiste à mettre en œuvre une solution **ERP basée sur Odoo Community**, enrichie par des modules spécifiques et connectée à différents services externes, notamment des **plateformes de réservation** et des **API touristiques**.

---

## 🛠️ Technologies et stack technique

| Catégorie | Technologies |
|---|---|
| **ERP** | Odoo Community |
| **Conteneurisation** | Docker, Docker Compose |
| **Langages** | Python, XML, SQL |
| **Gestion de versions** | Git, GitHub |
| **Convention Git** | Conventional Commits |
| **Documentation** | LaTeX |

---

## 📂 Structure du dépôt

```text
stage-PFA/
│
├── docker-compose.yml
│
├── custom_addons/
│   ├── CONNECTIVITÉ_GDS_AÉRIEN/
│   ├── allotements_aeriens/
│   ├── api_gds/
│   ├── hotel_channel_manager/
│   └── travel_webhook/
│
└── documentation_du_grile_fonctionnelle/
    ├── Sources
    └── PDF
```

### 📌 Description des principaux dossiers

- **`custom_addons/`** : contient les modules Odoo développés spécifiquement dans le cadre du projet.
- **`CONNECTIVITÉ_GDS_AÉRIEN/`** : module dédié à la connectivité avec les systèmes de réservation aérienne.
- **`allotements_aeriens/`** : module dédié à la gestion des allotements aériens.
- **`api_gds/`** : module de configuration et de gestion des paramètres des services GDS.
- **`hotel_channel_manager/`** : module destiné à la gestion de la connectivité avec les plateformes hôtelières.
- **`travel_webhook/`** : module permettant la gestion des webhooks liés aux services externes.
- **`documentation_du_grile_fonctionnelle/`** : contient la documentation technique ainsi que les rapports et sources LaTeX.

---

# 🚀 Guide d'installation et de déploiement

## 1. Prérequis

Avant de commencer l'installation, assurez-vous que les outils suivants sont installés sur votre machine :

- **Git**
- **Docker Desktop** avec Docker Compose

### Vérification

Vous pouvez vérifier l'installation avec les commandes suivantes :

```bash
git --version
docker --version
docker compose version
```

---

## 2. Installation de Docker

### 🐧 Ubuntu / Debian

Mettre à jour la liste des paquets :

```bash
sudo apt-get update
```

Installer les dépendances nécessaires :

```bash
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release
```

Ajouter la clé GPG officielle de Docker :

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
| sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

Configurer le dépôt stable :

```bash
echo "deb [arch=$(dpkg --print-architecture) \
signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
https://download.docker.com/linux/ubuntu \
$(lsb_release -cs) stable" \
| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Installer Docker Engine et Docker Compose :

```bash
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

Ajouter l'utilisateur courant au groupe `docker` :

```bash
sudo usermod -aG docker $USER
```

> **Remarque :** une reconnexion à la session peut être nécessaire pour que la modification du groupe soit prise en compte.

---

### 🪟 Windows / 🍎 macOS

Téléchargez et installez **Docker Desktop**.

Après l'installation :

1. Lancez Docker Desktop.
2. Attendez que Docker soit complètement démarré.
3. Vérifiez que l'état indique que Docker est en cours d'exécution (**Running**).

---

# 3. Clonage du projet

Clonez le dépôt GitHub :

```bash
git clone https://github.com/maha625/stage-PFA.git
```

Accédez ensuite au répertoire du projet :

```bash
cd stage-PFA
```

---

# 4. Lancement des services avec Docker Compose

Le projet utilise **Docker Compose** pour démarrer les différents services nécessaires au fonctionnement de l'application.

Lancez les conteneurs en arrière-plan :

```bash
docker compose up -d
```

> **Ancienne version de Docker Compose :**
>
> Si votre environnement utilise encore l'ancienne syntaxe, vous pouvez utiliser :
>
> ```bash
> docker-compose up -d
> ```

### Vérification des conteneurs

Pour vérifier que les services sont correctement démarrés :

```bash
docker ps
```

Les conteneurs **Odoo** et **PostgreSQL** doivent apparaître dans la liste.

### Accès à Odoo

Une fois les conteneurs démarrés, ouvrez votre navigateur et accédez à :

```text
http://localhost:8069
```

---

# 5. Configuration des modules personnalisés

Les modules spécifiques développés dans le cadre du PFA sont regroupés dans le dossier :

```text
custom_addons/
```

Afin qu'Odoo puisse détecter ces modules, le dossier doit être monté dans le conteneur Odoo.

## Vérification du fichier `docker-compose.yml`

Assurez-vous que le fichier `docker-compose.yml` contient un volume similaire à :

```yaml
services:
  web:
    volumes:
      - ./custom_addons:/mnt/extra-addons
```

Cette configuration permet de rendre les modules présents dans `custom_addons/` accessibles depuis Odoo.

---

# 6. Activation du mode développeur

Après avoir démarré Odoo :

1. Connectez-vous à votre base de données Odoo.
2. Accédez au menu **Paramètres** (*Settings*).
3. Activez le **mode développeur** (*Developer Mode*).

Le mode développeur permet notamment d'accéder aux fonctionnalités nécessaires à la gestion et à l'installation des modules personnalisés.

---

# 7. Mise à jour de la liste des applications

Une fois le mode développeur activé :

1. Accédez au menu **Applications** (*Apps*).
2. Ouvrez le menu permettant de gérer les applications.
3. Cliquez sur **Mettre à jour la liste des applications** (*Update Apps List*).
4. Confirmez la mise à jour.

Odoo pourra alors détecter les modules présents dans le dossier `custom_addons`.

---

# 8. Installation des modules du PFA

Pour installer les modules développés :

1. Accédez au menu **Applications**.
2. Retirez le filtre **Applications** de la barre de recherche afin d'afficher également les modules techniques.
3. Recherchez le module souhaité.
4. Sélectionnez le module.
5. Cliquez sur **Installer** (*Install*).

Parmi les modules développés dans le cadre du projet :

- `CONNECTIVITÉ_GDS_AÉRIEN`
- `allotements_aeriens`
- `api_gds`
- `hotel_channel_manager`
- `travel_webhook`

---

# 🔧 Configuration générale

Après l'installation des modules, certains paramètres peuvent nécessiter une configuration dans Odoo, notamment :

- les paramètres de connexion aux API externes ;
- les identifiants des services GDS ;
- les clés d'API touristiques ;
- les paramètres liés aux plateformes de réservation ;
- les paramètres des différents modules personnalisés.

Ces paramètres sont généralement accessibles depuis les menus de configuration correspondants dans Odoo.

---

# 📚 Documentation

La documentation fonctionnelle et technique du projet est disponible dans :

```text
documentation_du_grile_fonctionnelle/
```

Ce dossier contient notamment :

- les sources **LaTeX** ;
- les documents techniques ;
- les rapports ;
- les documents PDF associés au projet.

---

# 🔄 Gestion des versions

Le projet utilise **Git** et **GitHub** pour assurer le suivi des versions du code source.

Les commits suivent la convention **Conventional Commits**, permettant de structurer et d'identifier clairement les différentes modifications apportées au projet.

Exemples :

```text
feat: ajout de la recherche de vols via le GDS
fix: correction du calcul des tarifs passagers
docs: mise à jour de la documentation
refactor: amélioration du module de connectivité
```

---

# 👩‍💻 Projet réalisé dans le cadre du PFA

**Projet de Fin d'Année (PFA)**  
**Cycle Ingénieur — Informatique et Systèmes Intelligents**  
**ENSAM Meknès**

**Thématique :** Intégration et développement d'une solution ERP Odoo pour les activités liées au voyage, à l'aérien et à l'hôtellerie.