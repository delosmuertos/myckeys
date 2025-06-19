import socket
from typing import Dict, List, Tuple, Optional, Callable

class MessageManager:
    def __init__(self, get_local_ip_func, log_func=None):
        self.get_local_ip = get_local_ip_func
        self.log = log_func if log_func else lambda msg: None
        self.messages = []
        self.public_keys = {}
        self.ma_cle_publique = ""
        self.TCP_PORT = 50001
        self.BUFFER_SIZE = 1024

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
        """Envoie un message direct à un pair"""
        # Vérification si l'échange de clé à bien eu lieu
        if not self.echanger_cles_publiques(ip):
            self.log(f"[ERREUR] Envoi de message annulé, clé publique non échangée avec {ip}")
            return False
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, self.TCP_PORT))
                s.send(msg.encode())
                self.log(f"[INFO] Message envoyé à {ip} : {msg}")
                return True
        except Exception as e:
            self.log(f"[ERREUR] Échec de l'envoi du message à {ip} : {e}")
            return False

    def envoyer_message_multicast(self, ips: List[str], msg: str) -> Dict[str, bool]:
        """Envoie un message à plusieurs pairs et retourne le statut de chaque envoi"""
        resultats = {}
        for ip in ips:
            self.log(f"[INFO] Envoi au pair {ip} ...")
            resultats[ip] = self.envoyer_message(ip, msg)
        return resultats

    def traiter_message_recu(self, data: str, addr: str) -> bool:
        """Traite un message direct reçu"""
        try:
            self.messages.append((addr, data))
            self.log(f"[INFO] Message reçu de {addr} : {data}")
            return True
        except Exception as e:
            self.log(f"[ERREUR] Erreur lors du traitement du message de {addr} : {e}")
            return False

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