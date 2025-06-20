# Plan Technique - Application de Messagerie Sécurisée

## 1. Vue d'ensemble du projet

### Objectif
Application de messagerie instantanée P2P avec chiffrement de bout en bout, fonctionnant sur réseau local sans serveur central.

### Technologies utilisées
- **Interface** : PyQt5 (GUI moderne)
- **Réseau** : UDP pour la découverte, TCP pour les messages
- **Sécurité** : RSA-2048 (échange de clés) + AES-256 (chiffrement des messages)
- **Découverte** : Zeroconf/mDNS pour la détection automatique des pairs
- **Base de données** : SQLite pour les utilisateurs

## 2. Architecture générale

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Interface     │    │   Gestion       │    │   Sécurité      │
│   Utilisateur   │◄──►│   Réseau        │◄──►│   & Chiffrement │
│   (PyQt5)       │    │   (TCP/UDP)     │    │   (RSA/AES)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Persistance   │    │   Découverte    │    │   Logs          │
│   (JSON/SQLite) │    │   (Zeroconf)    │    │   (Chiffrés)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 3. Structure des dossiers

```
Mykeys/
├── main.py                 # Point d'entrée principal
├── app/                    # Logique métier principale
│   ├── network_manager.py  # Orchestrateur réseau
│   ├── crypto_manager.py   # Gestion du chiffrement
│   ├── UserManager.py      # Gestion des utilisateurs
│   └── models/User.py      # Modèle utilisateur
├── network/                # Communication réseau
│   ├── communication.py    # Communication TCP entre pairs
│   ├── discoveryend.py     # Découverte réseau (Zeroconf)
│   ├── message_manager.py  # Gestion des messages
│   ├── group_manager.py    # Gestion des groupes
│   └── disconnect.py       # Gestion de la déconnexion
├── security/               # Sécurité
│   └── key_manager.py      # Gestion des clés et certificats
├── resources/              # Interface utilisateur
│   ├── views/
│   │   ├── auth_window.py  # Fenêtre d'authentification
│   │   ├── dashboard.py    # Interface principale
│   │   └── settings_window.py # Paramètres
│   └── img/                # Icônes et images
├── database/               # Base de données
│   ├── db.py              # Configuration SQLite
│   └── models.py          # Modèles de données
├── storage/                # Données persistantes
│   ├── app.db             # Base SQLite
│   ├── messages.json      # Messages sauvegardés
│   ├── groups.json        # Groupes sauvegardés
│   └── public_keys.json   # Clés publiques des pairs
└── utils/                  # Utilitaires
    └── logger.py          # Système de logging
```

## 4. Composants principaux

### 4.1 Point d'entrée (`main.py`)
- Initialise la base de données
- Lance l'interface d'authentification
- Point de départ de l'application

### 4.2 Gestionnaire de réseau (`app/network_manager.py`)
**Rôle** : Orchestrateur central qui coordonne tous les modules réseau

**Responsabilités** :
- Initialisation des modules (découverte, communication, messages, groupes)
- Gestion des callbacks entre modules
- Émission de signaux vers l'interface utilisateur
- Gestion des événements réseau (nouveau pair, message reçu, etc.)

**Signaux émis** :
- `peer_discovered(ip, nom)` : Nouveau pair détecté
- `peer_lost(ip)` : Pair perdu
- `message_received(sender_ip, message)` : Message reçu
- `group_message_received(group_name, sender_ip, message)` : Message de groupe

### 4.3 Interface utilisateur (`resources/views/`)

#### Dashboard (`dashboard.py`)
**Rôle** : Interface principale de messagerie

**Composants** :
- **Colonne gauche** : Liste des périphériques découverts
- **Colonne centrale** : Liste des contacts/conversations
- **Colonne droite** : Zone de chat active
- **Barre d'outils** : Boutons d'action (nouvelle conversation, paramètres, etc.)

**Flux de conversation** :
1. Clic sur un périphérique (gauche) → Ajout à la liste de contacts (centre)
2. Clic sur un contact (centre) → Sélection pour conversation
3. Clic sur "Nv conversation" → Ouverture du chat

### 4.4 Communication réseau (`network/`)

#### Découverte (`discoveryend.py`)
**Rôle** : Détection automatique des pairs sur le réseau local

**Mécanisme** :
- Utilise Zeroconf/mDNS pour annoncer et découvrir les services
- Service type : `_securemsg._tcp.local.`
- Port UDP : 50000 pour les broadcasts
- Timeout : 30 secondes pour considérer un pair comme déconnecté

#### Communication (`communication.py`)
**Rôle** : Communication TCP directe entre pairs

**Fonctionnalités** :
- Serveur TCP sur le port 50001
- Gestion des connexions entrantes
- Traitement des messages chiffrés
- Échange de clés publiques

#### Messages (`message_manager.py`)
**Rôle** : Gestion du chiffrement/déchiffrement des messages

**Sécurité** :
- Chiffrement hybride : AES-256 pour le message + RSA-2048 pour la clé AES
- Chaque message utilise une clé AES unique
- Persistance des messages dans `storage/messages.json`

### 4.5 Sécurité (`security/` et `app/crypto_manager.py`)

#### Gestionnaire de chiffrement (`crypto_manager.py`)
**Rôle** : Opérations cryptographiques

**Fonctionnalités** :
- Génération de paires de clés RSA-2048
- Chiffrement/déchiffrement AES-256
- Création de certificats X.509
- Rotation automatique des clés

#### Gestionnaire de clés (`key_manager.py`)
**Rôle** : Gestion du cycle de vie des clés

**Fonctionnalités** :
- Stockage sécurisé des clés publiques
- Révocation de certificats
- Validation des clés
- Persistance dans `storage/public_keys.json`

## 5. Flux de données principaux

### 5.1 Découverte d'un nouveau pair
```
1. Zeroconf détecte un nouveau service
2. NetworkDiscovery → on_peer_discovered(ip, nom)
3. NetworkManager → peer_discovered.emit(ip, nom)
4. Dashboard → _on_peer_discovered(ip, nom)
5. Interface mise à jour avec le nouveau pair
```

### 5.2 Envoi d'un message
```
1. Utilisateur saisit un message dans l'interface
2. Dashboard → NetworkManager.send_message(recipient_ip, message)
3. MessageManager → chiffrement AES + chiffrement clé AES avec RSA
4. Communication → envoi TCP du message chiffré
5. Pair distant → déchiffrement et affichage
```

### 5.3 Réception d'un message
```
1. Communication → réception TCP du message chiffré
2. MessageManager → déchiffrement RSA puis AES
3. NetworkManager → message_received.emit(sender_ip, plaintext)
4. Dashboard → _on_message_received(sender_ip, plaintext)
5. Interface mise à jour avec le nouveau message
```

## 6. Points d'entrée pour les développeurs

### 6.1 Pour comprendre l'interface
**Fichiers à lire** :
1. `resources/views/dashboard.py` - Interface principale
2. `resources/views/auth_window.py` - Authentification
3. `main.py` - Point de départ

### 6.2 Pour comprendre la communication réseau
**Fichiers à lire** :
1. `app/network_manager.py` - Orchestrateur
2. `network/discoveryend.py` - Découverte des pairs
3. `network/communication.py` - Communication TCP
4. `network/message_manager.py` - Gestion des messages

### 6.3 Pour comprendre la sécurité
**Fichiers à lire** :
1. `app/crypto_manager.py` - Opérations cryptographiques
2. `security/key_manager.py` - Gestion des clés
3. `network/message_manager.py` - Chiffrement des messages

### 6.4 Pour ajouter une nouvelle fonctionnalité
**Processus recommandé** :
1. Identifier le module concerné dans la structure
2. Ajouter la logique métier dans le module approprié
3. Si nécessaire, ajouter un signal dans `NetworkManager`
4. Connecter le signal à l'interface dans `Dashboard`
5. Tester la fonctionnalité

## 7. Configuration et déploiement

### 7.1 Dépendances
```bash
pip install -r requirements.txt
```

### 7.2 Variables d'environnement importantes
- Ports par défaut : UDP 50000, TCP 50001
- Timeout de découverte : 30 secondes
- Taille des clés RSA : 2048 bits
- Algorithme de chiffrement : AES-256

### 7.3 Fichiers de configuration
- `storage/` : Données persistantes
- `config/database.py` : Configuration base de données
- `requirements.txt` : Dépendances Python

## 8. Bonnes pratiques de développement

### 8.1 Gestion des erreurs
- Utiliser des blocs `try/except` appropriés
- Logger les erreurs avec `utils/logger.py`
- Afficher des messages d'erreur utilisateur-friendly

### 8.2 Threading
- Les opérations réseau sont dans des threads séparés
- Utiliser `QTimer.singleShot` pour mettre à jour l'interface depuis les threads
- Éviter les accès concurrents aux ressources partagées

### 8.3 Sécurité
- Ne jamais stocker de clés privées en clair
- Valider toutes les entrées utilisateur
- Utiliser des timeouts appropriés pour les opérations réseau

## 9. Débogage et maintenance

### 9.1 Logs
- Logs chiffrés dans `app.log.enc`
- Logs de débogage dans la console
- Utiliser `utils/logger.py` pour la cohérence

### 9.2 Problèmes courants
- **Messages non reçus** : Vérifier les pare-feu Windows
- **Pairs non détectés** : Vérifier la configuration réseau
- **Erreurs de déchiffrement** : Supprimer `storage/public_keys.json`

### 9.3 Tests
- `test_network.py` : Tests de communication réseau
- Tests manuels recommandés pour les nouvelles fonctionnalités

---

**Note** : Ce plan est un document vivant qui doit être mis à jour lors de l'ajout de nouvelles fonctionnalités ou de modifications importantes de l'architecture. 