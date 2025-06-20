from datetime import datetime, timedelta
import json
import os
from app.crypto_manager import CryptoManager
from typing import Optional, Dict, List

STORAGE_DIR = os.path.join(os.path.dirname(__file__), '..', 'storage')
PUBLIC_KEYS_FILE = os.path.join(STORAGE_DIR, 'public_keys.json')
SECURITY_LOG_FILE = os.path.join(STORAGE_DIR, 'security_log.enc')

class KeyManager:
    def __init__(self, log_func=None):
        self._log = log_func if log_func else lambda msg, _: None
        os.makedirs(STORAGE_DIR, exist_ok=True)
        self.public_keys = self._load_public_keys()
        self.revoked_certs_file = os.path.join(STORAGE_DIR, 'revoked_certs.json')
        self.security_log_file = SECURITY_LOG_FILE
        self.key_rotation_interval = timedelta(days=30)  # Rotation des clés tous les 30 jours
        self._load_revoked_certs()

    def _load_revoked_certs(self) -> None:
        """Charge la liste des certificats révoqués"""
        if os.path.exists(self.revoked_certs_file):
            with open(self.revoked_certs_file, 'r') as f:
                self.revoked_certs = json.load(f)
        else:
            self.revoked_certs = []

    def _save_revoked_certs(self) -> None:
        """Sauvegarde la liste des certificats révoqués"""
        os.makedirs(STORAGE_DIR, exist_ok=True)
        with open(self.revoked_certs_file, 'w') as f:
            json.dump(self.revoked_certs, f)

    def _load_public_keys(self) -> Dict:
        if os.path.exists(PUBLIC_KEYS_FILE):
            try:
                with open(PUBLIC_KEYS_FILE, 'r') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                self._log(f"Erreur de chargement de public_keys.json: {e}", "KEY_MANAGER")
                return {}
        return {}

    def _save_public_keys(self):
        try:
            with open(PUBLIC_KEYS_FILE, 'w') as f:
                json.dump(self.public_keys, f, indent=4)
        except IOError as e:
            self._log(f"Erreur de sauvegarde de public_keys.json: {e}", "KEY_MANAGER")

    def add_public_key(self, ip: str, key_pem: str):
        self._log(f"Ajout de la clé publique pour {ip}", "KEY_MANAGER")
        self.public_keys[ip] = key_pem
        self._save_public_keys()

    def get_public_key(self, ip: str) -> Optional[str]:
        return self.public_keys.get(ip)

    def check_key_rotation(self) -> bool:
        """Vérifie si une rotation des clés est nécessaire"""
        try:
            cert_info = CryptoManager.get_certificate_info()
            creation_date = cert_info['not_before']
            if datetime.utcnow() - creation_date > self.key_rotation_interval:
                self.log_security_event("Rotation des clés nécessaire")
                return True
            return False
        except Exception as e:
            self.log_security_event(f"Erreur lors de la vérification de rotation des clés: {str(e)}")
            return False

    def rotate_keys(self, username: str) -> bool:
        """
        Génère une nouvelle paire de clés et un nouveau certificat pour l'utilisateur.
        L'ancienne clé privée est écrasée en toute sécurité.
        """
        try:
            self._log(f"Rotation des clés demandée pour {username}", "KEY_MANAGER")
            CryptoManager.generate_key_and_cert(username)
            self._log(f"Nouvelle paire de clés générée pour {username}", "KEY_MANAGER")
            
            # Recharger la clé publique pour le broadcast
            cert = CryptoManager.load_certificate(username)
            if cert:
                public_key_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
                # Cette information devra peut-être remonter au NetworkManager pour être diffusée
                self._log("La nouvelle clé publique doit être rediffusée.", "KEY_MANAGER")
            
            return True
        except Exception as e:
            self._log(f"Erreur lors de la rotation des clés : {e}", "KEY_MANAGER")
            return False

    def revoke_certificate(self, serial_number: str, reason: str) -> bool:
        """Révoque un certificat"""
        try:
            self.revoked_certs.append({
                'serial': serial_number,
                'revocation_date': datetime.utcnow().isoformat(),
                'reason': reason
            })
            self._save_revoked_certs()
            self.log_security_event(f"Certificat {serial_number} révoqué pour raison: {reason}")
            return True
        except Exception as e:
            self.log_security_event(f"Erreur lors de la révocation du certificat: {str(e)}")
            return False

    def is_certificate_revoked(self, serial_number: str) -> bool:
        """Vérifie si un certificat est révoqué"""
        return any(cert['serial'] == str(serial_number) for cert in self.revoked_certs)

    def log_security_event(self, event_message: str, username: str):
        """
        Chiffre et enregistre un événement de sécurité.
        """
        try:
            # Pour chiffrer, il faudrait une clé. Utiliser la clé publique de l'utilisateur
            # pour qu'il puisse déchiffrer avec sa clé privée est une option.
            cert = CryptoManager.load_certificate(username)
            if not cert:
                self._log("Impossible de logger l'événement, certificat non trouvé.", "KEY_MANAGER")
                return

            encrypted_event = CryptoManager.encrypt_with_cert(
                cert.public_bytes(serialization.Encoding.PEM),
                f"{datetime.now().isoformat()} - {event_message}".encode()
            )
            
            with open(SECURITY_LOG_FILE, 'ab') as f:
                f.write(encrypted_event + b'\\n')
        except Exception as e:
            self._log(f"Erreur lors du logging de l'événement de sécurité: {e}", "KEY_MANAGER")

    def get_security_logs(self, username: str) -> List[str]:
        """
        Lit et déchiffre les logs de sécurité.
        Chaque ligne est supposée être chiffrée séparément.
        """
        if not os.path.exists(SECURITY_LOG_FILE):
            return ["Le fichier de log de sécurité n'existe pas."]
        
        decrypted_logs = []
        try:
            with open(SECURITY_LOG_FILE, 'rb') as f:
                for line in f:
                    # Le log est binaire, on doit le déchiffrer
                    try:
                        decrypted_line = CryptoManager.decrypt_with_private_key(username, line.strip())
                        decrypted_logs.append(decrypted_line.decode())
                    except Exception as e:
                        # Si on ne peut pas déchiffrer une ligne, on le note
                        decrypted_logs.append(f"[Ligne non déchiffrable - {e}]")
            return decrypted_logs
        except Exception as e:
            return [f"Erreur lors de la lecture du fichier de log: {e}"] 