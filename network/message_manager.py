import socket
import json
import os
from typing import Dict, List, Tuple, Optional, Callable
from app.crypto_manager import CryptoManager

class MessageManager:
    def __init__(self, get_local_ip_func, log_func=None):
        self.get_local_ip = get_local_ip_func
        self.log = log_func if log_func else lambda msg: None
        self.public_keys = {}
        self.ma_cle_publique = ""
        self.messages = []
        self.TCP_PORT = 50001
        self.BUFFER_SIZE = 1024
        
        # Fichiers de persistance
        self.storage_dir = os.path.join(os.path.dirname(__file__), '..', 'storage')
        self.messages_file = os.path.join(self.storage_dir, 'messages.json')
        self.keys_file = os.path.join(self.storage_dir, 'public_keys.json')
        
        # Charger les données sauvegardées
        self._load_messages()
        self._load_public_keys()

    def set_ma_cle_publique(self, cle_publique: str) -> None:
        """Définit la clé publique locale"""
        self.ma_cle_publique = cle_publique
        self.log("[INFO] Clé publique locale définie")

    def echanger_cles_publiques(self, ip: str) -> bool:
        """Échange les clés publiques avec un pair"""
        self.log(f"[DEBUG] Démarrage de l'échange de clé avec {ip}")
        
        # Vérifications si on a déjà cet IP
        if ip in self.public_keys:
            return True
            
        # vérification que ce ne soit pas ma clé publique
        if not self.ma_cle_publique:
            self.log("[ERREUR] Clé publique locale non chargée.")
            return False
            
        # Echange
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)  # Timeout de 5 secondes
                s.connect((ip, self.TCP_PORT))
                s.send(f"PUBKEY:{self.ma_cle_publique}".encode())
                self.log(f"[INFO] Clé publique envoyée à {ip}")
                data = s.recv(self.BUFFER_SIZE).decode()
                if data.startswith("PUBKEY:"):
                    key = data.split(":", 1)[1]
                    self.public_keys[ip] = key
                    self.log(f"[DEBUG] Échange de clé réussi avec {ip}")
                    self.log(f"[INFO] Clé publique reçue de {ip}")
                    # Sauvegarder les clés publiques
                    self._save_public_keys()
                    return True
                else:
                    self.log(f"[ERREUR] Réponse inattendue lors de l'échange de clé avec {ip}: {data}")
                    return False
        except socket.timeout:
            self.log(f"[ERREUR] Timeout lors de l'échange de clé avec {ip}")
            return False
        except Exception as e:
            self.log(f"[ERREUR] Échec de l'échange de clé avec {ip} : {e}")
            return False

    def envoyer_message(self, ip: str, msg: str) -> bool:
        """Envoie un message direct chiffré à un pair"""
        # Vérification si l'échange de clé à bien eu lieu
        if not self.echanger_cles_publiques(ip):
            self.log(f"[ERREUR] Envoi de message annulé, clé publique non échangée avec {ip}")
            return False
            
        try:
            # Récupérer la clé publique du destinataire
            if ip not in self.public_keys:
                self.log(f"[ERREUR] Clé publique manquante pour {ip}")
                return False
                
            recipient_public_key = self.public_keys[ip]
            
            # Chiffrer le message avec la clé publique du destinataire
            encrypted_data = CryptoManager.hybrid_encrypt(
                recipient_public_key.encode(), 
                msg.encode()
            )
            
            # Préparer le message chiffré pour l'envoi
            encrypted_message = {
                'type': 'ENCRYPTED_MESSAGE',
                'encrypted_key': encrypted_data['encrypted_key'].hex(),
                'iv': encrypted_data['iv'].hex(),
                'ciphertext': encrypted_data['ciphertext'].hex()
            }
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, self.TCP_PORT))
                s.send(json.dumps(encrypted_message).encode())
                self.log(f"[INFO] Message chiffré envoyé à {ip} : {msg}")
                
                # Stocker le message envoyé dans la liste locale (en clair pour l'affichage)
                local_ip = self.get_local_ip()
                self.messages.append((local_ip, msg))
                print(f"[DEBUG] MessageManager - Message envoyé stocké: ({local_ip}, {msg})")
                print(f"[DEBUG] MessageManager - État des messages après envoi: {self.messages}")
                # Sauvegarder les messages
                self._save_messages()
                
                return True
        except Exception as e:
            self.log(f"[ERREUR] Échec de l'envoi du message chiffré à {ip} : {e}")
            return False

    def envoyer_message_multicast(self, ips: List[str], msg: str) -> Dict[str, bool]:
        """Envoie un message à plusieurs pairs et retourne le statut de chaque envoi"""
        resultats = {}
        for ip in ips:
            self.log(f"[INFO] Envoi au pair {ip} ...")
            resultats[ip] = self.envoyer_message(ip, msg)
        return resultats

    def traiter_message_recu(self, data: str, addr: str) -> Optional[str]:
        """
        Traite un message direct reçu.
        Retourne le message en clair si le déchiffrement réussit, sinon None.
        """
        try:
            if not data or not addr:
                return None
            
            try:
                message_data = json.loads(data)
                if message_data.get('type') == 'ENCRYPTED_MESSAGE':
                    encrypted_key = bytes.fromhex(message_data['encrypted_key'])
                    iv = bytes.fromhex(message_data['iv'])
                    ciphertext = bytes.fromhex(message_data['ciphertext'])
                    
                    decrypted_message = CryptoManager.hybrid_decrypt(encrypted_key, iv, ciphertext)
                    plaintext = decrypted_message.decode()
                    
                    self.log(f"[INFO] Message déchiffré reçu de {addr} : {plaintext}")
                    self.messages.append((addr, plaintext))
                    self._save_messages()
                    return plaintext
                else:
                    # Gérer d'autres types de messages JSON si nécessaire
                    self.log(f"[INFO] Message JSON non-chiffré reçu de {addr} : {data}")
                    self.messages.append((addr, data))
                    self._save_messages()
                    return data

            except json.JSONDecodeError:
                # Gérer les messages non-JSON (pour la compatibilité)
                self.log(f"[INFO] Message texte simple reçu de {addr} : {data}")
                self.messages.append((addr, data))
                self._save_messages()
                return data
                
        except Exception as e:
            self.log(f"[ERREUR] Erreur lors du traitement du message de {addr} : {e}")
            return None

    def traiter_echange_cles(self, data: str, addr: str) -> bool:
        """Traite un échange de clés publiques"""
        try:
            if data.startswith("PUBKEY:"):
                peer_ip = addr
                key = data.split(":", 1)[1]
                self.public_keys[peer_ip] = key
                self.log(f"[INFO] Clé publique reçue de {peer_ip}")
                
                # Envoi de notre clé publique en réponse
                if self.ma_cle_publique:
                    try:
                        # Note: Cette réponse devrait être envoyée via la connexion existante
                        # mais pour simplifier, on utilise une nouvelle connexion
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.connect((peer_ip, self.TCP_PORT))
                            s.send(f"PUBKEY:{self.ma_cle_publique}".encode())
                            self.log(f"[INFO] Clé publique renvoyée à {peer_ip}")
                    except Exception as e:
                        self.log(f"[ERREUR] Échec de la réponse de clé publique à {peer_ip} : {e}")
                return True
            return False
        except Exception as e:
            self.log(f"[ERREUR] Erreur lors du traitement de l'échange de clés avec {addr} : {e}")
            return False

    def get_messages(self) -> List[Tuple[str, str]]:
        """Retourne tous les messages reçus"""
        print(f"[DEBUG] MessageManager - get_messages appelé, messages disponibles: {self.messages}")
        return self.messages.copy()

    def get_messages_from(self, ip: str) -> List[Tuple[str, str]]:
        """Retourne les messages reçus d'une IP spécifique"""
        return [(sender, msg) for sender, msg in self.messages if sender == ip]

    def get_public_keys(self) -> Dict[str, str]:
        """Retourne toutes les clés publiques reçues"""
        return self.public_keys.copy()

    def get_public_key(self, ip: str) -> Optional[str]:
        """Retourne la clé publique d'une IP spécifique"""
        return self.public_keys.get(ip)

    def has_public_key(self, ip: str) -> bool:
        """Vérifie si on a la clé publique d'une IP"""
        return ip in self.public_keys

    def clear_messages(self) -> None:
        """Efface tous les messages"""
        self.messages.clear()
        self._save_messages()
        self.log("[INFO] Tous les messages ont été effacés")

    def clear_messages_from(self, ip: str) -> int:
        """Efface tous les messages d'une IP spécifique et retourne le nombre d'effacés"""
        initial_count = len(self.messages)
        self.messages = [(sender, msg) for sender, msg in self.messages if sender != ip]
        deleted_count = initial_count - len(self.messages)
        if deleted_count > 0:
            self.log(f"[INFO] {deleted_count} messages de {ip} ont été effacés")
        return deleted_count

    def get_message_count(self) -> int:
        """Retourne le nombre total de messages"""
        return len(self.messages)

    def get_message_count_from(self, ip: str) -> int:
        """Retourne le nombre de messages d'une IP spécifique"""
        return len([1 for sender, _ in self.messages if sender == ip])

    def get_recent_messages(self, count: int = 10) -> List[Tuple[str, str]]:
        """Retourne les messages les plus récents"""
        return self.messages[-count:] if self.messages else []

    def search_messages(self, keyword: str) -> List[Tuple[str, str]]:
        """Recherche des messages contenant un mot-clé"""
        return [(sender, msg) for sender, msg in self.messages if keyword.lower() in msg.lower()]

    def _load_messages(self) -> None:
        """Charge les messages depuis le fichier de persistance"""
        if os.path.exists(self.messages_file):
            with open(self.messages_file, 'r') as f:
                self.messages = json.load(f)
        else:
            self.messages = []

    def _load_public_keys(self) -> None:
        """Charge les clés publiques depuis le fichier de persistance"""
        if os.path.exists(self.keys_file):
            with open(self.keys_file, 'r') as f:
                self.public_keys = json.load(f)
        else:
            self.public_keys = {}

    def _save_messages(self) -> None:
        """Sauvegarde les messages dans le fichier de persistance"""
        os.makedirs(self.storage_dir, exist_ok=True)
        with open(self.messages_file, 'w') as f:
            json.dump(self.messages, f, indent=2)

    def _save_public_keys(self) -> None:
        """Sauvegarde les clés publiques dans le fichier de persistance"""
        os.makedirs(self.storage_dir, exist_ok=True)
        with open(self.keys_file, 'w') as f:
            json.dump(self.public_keys, f, indent=2) 