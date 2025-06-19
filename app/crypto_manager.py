from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.x509 import NameOID, CertificateBuilder, random_serial_number
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import os

CERTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'storage')
PRIVATE_KEY_FILE = os.path.join(CERTS_DIR, 'private_key.pem')
CERT_FILE = os.path.join(CERTS_DIR, 'certificate.pem')

class CryptoManager:
    @staticmethod
    def generate_key_and_cert(common_name: str = "User"):
        # Génère une clé privée RSA et un certificat autosigné
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name)
        ])
        cert = CertificateBuilder().subject_name(subject).issuer_name(issuer)
        cert = cert.public_key(private_key.public_key())
        cert = cert.serial_number(random_serial_number())
        cert = cert.not_valid_before(datetime.utcnow())
        cert = cert.not_valid_after(datetime.utcnow() + timedelta(days=365))
        cert = cert.sign(private_key, hashes.SHA256(), default_backend())
        # Sauvegarde
        os.makedirs(CERTS_DIR, exist_ok=True)
        with open(PRIVATE_KEY_FILE, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(CERT_FILE, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        return private_key, cert

    @staticmethod
    def load_private_key():
        with open(PRIVATE_KEY_FILE, 'rb') as f:
            return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

    @staticmethod
    def load_certificate():
        with open(CERT_FILE, 'rb') as f:
            return x509.load_pem_x509_certificate(f.read(), default_backend())

    @staticmethod
    def get_certificate_info():
        cert = CryptoManager.load_certificate()
        return {
            'subject': cert.subject.rfc4514_string(),
            'issuer': cert.issuer.rfc4514_string(),
            'serial': cert.serial_number,
            'not_before': cert.not_valid_before,
            'not_after': cert.not_valid_after
        }

    @staticmethod
    def encrypt_with_cert(cert_pem: bytes, data: bytes) -> bytes:
        cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        public_key = cert.public_key()
        return public_key.encrypt(
            data,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

    @staticmethod
    def decrypt_with_private_key(data: bytes) -> bytes:
        private_key = CryptoManager.load_private_key()
        return private_key.decrypt(
            data,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

    @staticmethod
    def encrypt_aes(key: bytes, plaintext: bytes) -> tuple:
        from os import urandom
        iv = urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return iv, ciphertext

    @staticmethod
    def decrypt_aes(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    @staticmethod
    def hybrid_encrypt(cert_pem: bytes, plaintext: bytes) -> dict:
        """
        Chiffre le message en utilisant une clé AES aléatoire, puis chiffre la clé AES avec le certificat x509 (clé publique RSA).
        Retourne un dict contenant la clé AES chiffrée, l'IV et le message chiffré.
        """
        from os import urandom
        aes_key = urandom(32)  # AES-256
        iv, ciphertext = CryptoManager.encrypt_aes(aes_key, plaintext)
        encrypted_key = CryptoManager.encrypt_with_cert(cert_pem, aes_key)
        return {
            'encrypted_key': encrypted_key,
            'iv': iv,
            'ciphertext': ciphertext
        }

    @staticmethod
    def hybrid_decrypt(encrypted_key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
        """
        Déchiffre la clé AES avec la clé privée, puis déchiffre le message avec la clé AES.
        """
        aes_key = CryptoManager.decrypt_with_private_key(encrypted_key)
        return CryptoManager.decrypt_aes(aes_key, iv, ciphertext)
