from datetime import datetime, timedelta
import json
import os
from app.crypto_manager import CryptoManager
from typing import Optional, Dict, List

class KeyManager:
    def __init__(self, storage_path: str = 'storage'):
        self.storage_path = storage_path
        self.revoked_certs_file = os.path.join(storage_path, 'revoked_certs.json')
        self.security_log_file = os.path.join(storage_path, 'security.log.enc')
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
        os.makedirs(self.storage_path, exist_ok=True)
        with open(self.revoked_certs_file, 'w') as f:
            json.dump(self.revoked_certs, f)

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

    def rotate_keys(self, common_name: str) -> bool:
        """Effectue une rotation des clés"""
        try:
            # Sauvegarde de l'ancien certificat dans la liste des révoqués
            old_cert = CryptoManager.load_certificate()
            self.revoked_certs.append({
                'serial': str(old_cert.serial_number),
                'revocation_date': datetime.utcnow().isoformat(),
                'reason': 'key_rotation'
            })
            self._save_revoked_certs()

            # Génération de nouvelles clés
            CryptoManager.generate_key_and_cert(common_name)
            
            self.log_security_event("Rotation des clés effectuée avec succès")
            return True
        except Exception as e:
            self.log_security_event(f"Erreur lors de la rotation des clés: {str(e)}")
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

    def log_security_event(self, event: str) -> None:
        """Enregistre un événement de sécurité dans le fichier de log chiffré"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event': event
            }
            
            # Lecture des logs existants
            existing_logs = []
            if os.path.exists(self.security_log_file):
                try:
                    with open(self.security_log_file, 'rb') as f:
                        encrypted_data = f.read()
                        decrypted_data = CryptoManager.decrypt_with_private_key(encrypted_data)
                        existing_logs = json.loads(decrypted_data.decode())
                except:
                    pass  # Fichier vide ou corrompu

            # Ajout du nouveau log
            existing_logs.append(log_entry)
            
            # Chiffrement et sauvegarde
            logs_json = json.dumps(existing_logs).encode()
            cert = CryptoManager.load_certificate()
            encrypted_logs = CryptoManager.encrypt_with_cert(
                cert.public_bytes(encoding=serialization.Encoding.PEM),
                logs_json
            )
            
            os.makedirs(self.storage_path, exist_ok=True)
            with open(self.security_log_file, 'wb') as f:
                f.write(encrypted_logs)
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du log de sécurité: {str(e)}")

    def get_security_logs(self) -> List[Dict]:
        """Récupère les logs de sécurité déchiffrés"""
        try:
            if not os.path.exists(self.security_log_file):
                return []
                
            with open(self.security_log_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = CryptoManager.decrypt_with_private_key(encrypted_data)
                return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Erreur lors de la lecture des logs de sécurité: {str(e)}")
            return [] 