import socket
import threading
import time
from typing import Dict, List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from cryptography.hazmat.primitives import serialization

# Import des modules créés
from network.discoveryend import NetworkDiscovery
from network.communication import PeerCommunicator
from network.group_manager import GroupManager
from network.message_manager import MessageManager
from security.key_manager import KeyManager
from utils.logger import Logger, LogLevel
from app.crypto_manager import CryptoManager

class NetworkManager(QObject):
    """
    Module d'intégration qui coordonne tous les modules réseau.
    Gère la découverte, la communication, les groupes et les messages.
    """
    
    # Signaux PyQt pour l'interface utilisateur
    peer_discovered = pyqtSignal(str, str)  # ip, nom
    peer_lost = pyqtSignal(str)  # ip
    message_received = pyqtSignal(str, str)  # sender_ip, message
    group_message_received = pyqtSignal(str, str, str)  # group_name, sender_ip, message
    connection_status_changed = pyqtSignal(bool)  # connected
    log_message = pyqtSignal(str)  # log message
    
    def __init__(self, username: str = "User"):
        super().__init__()
        self.username = username
        self.logger = Logger()
        self.logger.add_callback(self._on_log_message)
        
        # Initialisation des modules
        self._init_modules()
        self._setup_connections()
        
        # État du réseau
        self.is_running = False
        self.known_peers = {}  # ip -> {nom, ip, status}
        
    def _init_modules(self):
        """Initialise tous les modules réseau"""
        try:
            # Logger
            self.logger.info("Initialisation des modules réseau", "NETWORK_MANAGER")
            
            # Découverte réseau
            self.discovery = NetworkDiscovery(
                username=self.username,
                on_peer_discovered=self._on_peer_discovered
            )
            
            # Gestionnaire de clés
            self.key_manager = KeyManager()
            
            # Gestionnaire de messages
            self.message_manager = MessageManager(
                get_local_ip_func=self._get_local_ip,
                log_func=self.logger.info
            )
            
            # Gestionnaire de groupes
            self.group_manager = GroupManager(
                get_local_ip_func=self._get_local_ip,
                key_exchange_func=self.message_manager.echanger_cles_publiques,
                log_func=self.logger.info
            )
            
            # Communicateur peer
            self.communicator = PeerCommunicator(
                get_local_ip_func=self._get_local_ip,
                key_exchange_func=self.message_manager.echanger_cles_publiques,
                log_func=self.logger.info
            )
            
            # Initialisation de la cryptographie
            self._init_crypto()
            
            self.logger.info("Tous les modules réseau initialisés", "NETWORK_MANAGER")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation des modules: {e}", "NETWORK_MANAGER")
            raise
    
    def _init_crypto(self):
        """Initialise la cryptographie"""
        try:
            # Vérifier si les clés existent, sinon les générer
            if not CryptoManager.load_certificate():
                self.logger.info("Génération des clés cryptographiques", "NETWORK_MANAGER")
                CryptoManager.generate_key_and_cert(self.username)
            
            # Charger la clé publique pour le message manager
            cert = CryptoManager.load_certificate()
            public_key_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
            self.message_manager.set_ma_cle_publique(public_key_pem.decode())
            
            self.logger.info("Cryptographie initialisée", "NETWORK_MANAGER")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation de la cryptographie: {e}", "NETWORK_MANAGER")
            raise
    
    def _setup_connections(self):
        """Configure les connexions entre modules"""
        # Connecter les signaux du communicateur
        self.communicator.on_message_received = self._on_message_received
        self.communicator.on_group_message_received = self._on_group_message_received
    
    def _get_local_ip(self) -> str:
        """Récupère l'IP locale"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def _on_log_message(self, log_entry: str):
        """Callback pour les messages de log"""
        self.log_message.emit(log_entry)
    
    def _on_peer_discovered(self, ip: str, nom: str):
        """Callback quand un pair est découvert"""
        print(f"[DEBUG] NetworkManager: Pair découvert - {nom} ({ip})")
        self.known_peers[ip] = {
            'nom': nom,
            'ip': ip,
            'status': 'online'
        }
        print(f"[DEBUG] NetworkManager: known_peers après ajout: {self.known_peers}")
        self.peer_discovered.emit(ip, nom)
        self.logger.info(f"Pair découvert: {nom} ({ip})", "NETWORK_MANAGER")
    
    def _on_message_received(self, sender_ip: str, message: str):
        """Callback quand un message direct est reçu"""
        print(f"[DEBUG] NetworkManager - Message reçu de {sender_ip}: {message}")
        
        # Vérifier que le message est bien traité par le MessageManager
        if hasattr(self.message_manager, 'traiter_message_recu'):
            success = self.message_manager.traiter_message_recu(message, sender_ip)
            print(f"[DEBUG] NetworkManager - Traitement du message par MessageManager: {'succès' if success else 'échec'}")
        else:
            print("[ERROR] NetworkManager - MessageManager n'a pas la méthode traiter_message_recu")
            
        # Émettre le signal pour l'interface
        self.message_received.emit(sender_ip, message)
        self.logger.info(f"Message reçu de {sender_ip}: {message}", "NETWORK_MANAGER")
    
    def _on_group_message_received(self, group_name: str, sender_ip: str, message: str):
        """Callback quand un message de groupe est reçu"""
        self.group_message_received.emit(group_name, sender_ip, message)
        self.logger.info(f"Message de groupe '{group_name}' de {sender_ip}: {message}", "NETWORK_MANAGER")
    
    def start(self) -> bool:
        """Démarre tous les services réseau"""
        try:
            self.logger.info("Démarrage des services réseau", "NETWORK_MANAGER")
            print("[DEBUG] Démarrage des services réseau...")
            
            # Démarrer la découverte
            print("[DEBUG] Démarrage de la découverte réseau...")
            self.discovery.start()
            
            # Démarrer le communicateur
            print("[DEBUG] Démarrage du communicateur...")
            self.communicator.start()
            
            # Démarrer le thread de nettoyage
            self._start_cleanup_thread()
            
            self.is_running = True
            self.connection_status_changed.emit(True)
            self.logger.info("Services réseau démarrés", "NETWORK_MANAGER")
            print("[DEBUG] Services réseau démarrés avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage des services: {e}", "NETWORK_MANAGER")
            print(f"[DEBUG] Erreur lors du démarrage: {e}")
            return False
    
    def _start_cleanup_thread(self):
        """Démarre le thread de nettoyage des pairs inactifs"""
        def cleanup_loop():
            while self.is_running:
                try:
                    time.sleep(10)  # Nettoyer toutes les 10 secondes
                    if hasattr(self.discovery, 'cleanup_inactive_peers'):
                        self.discovery.cleanup_inactive_peers()
                except Exception as e:
                    print(f"[DEBUG] Erreur nettoyage: {e}")
        
        threading.Thread(target=cleanup_loop, daemon=True).start()
    
    def stop(self):
        """Arrête tous les services réseau"""
        try:
            self.logger.info("Arrêt des services réseau", "NETWORK_MANAGER")
            
            # Arrêter la découverte
            self.discovery.stop()
            
            # Arrêter le communicateur
            self.communicator.stop()
            
            self.is_running = False
            self.connection_status_changed.emit(False)
            self.logger.info("Services réseau arrêtés", "NETWORK_MANAGER")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt des services: {e}", "NETWORK_MANAGER")
    
    # === MÉTHODES POUR L'INTERFACE UTILISATEUR ===
    
    def get_known_peers(self) -> Dict:
        """Retourne la liste des pairs connus"""
        return self.known_peers.copy()
    
    def send_message(self, target_ip: str, message: str) -> bool:
        """Envoie un message direct"""
        return self.message_manager.envoyer_message(target_ip, message)
    
    def send_group_message(self, group_name: str, message: str) -> bool:
        """Envoie un message de groupe"""
        return self.group_manager.envoyer_message_dans_groupe(group_name, message)
    
    def create_group(self, group_name: str, member_ips: List[str]) -> bool:
        """Crée un nouveau groupe"""
        return self.group_manager.creer_groupe(group_name, member_ips)
    
    def get_groups(self) -> Dict:
        """Retourne tous les groupes"""
        return self.group_manager.get_groupes()
    
    def get_messages(self) -> List:
        """Retourne tous les messages directs"""
        return self.message_manager.get_messages()
    
    def get_group_messages(self, group_name: str) -> List:
        """Retourne les messages d'un groupe"""
        return self.group_manager.get_messages_groupe(group_name)
    
    def get_public_keys(self) -> Dict:
        """Retourne toutes les clés publiques"""
        return self.message_manager.get_public_keys()
    
    def clear_messages(self):
        """Efface tous les messages"""
        self.message_manager.clear_messages()
        self.logger.info("Tous les messages ont été effacés", "NETWORK_MANAGER")
    
    def get_logs(self, level: Optional[LogLevel] = None, limit: Optional[int] = None) -> List:
        """Retourne les logs"""
        return self.logger.get_logs(level=level, limit=limit)
    
    def rotate_keys(self) -> bool:
        """Effectue une rotation des clés"""
        success = self.key_manager.rotate_keys(self.username)
        if success:
            # Recharger la nouvelle clé publique
            cert = CryptoManager.load_certificate()
            public_key_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
            self.message_manager.set_ma_cle_publique(public_key_pem.decode())
        return success
    
    def get_security_logs(self) -> List:
        """Retourne les logs de sécurité"""
        return self.key_manager.get_security_logs() 