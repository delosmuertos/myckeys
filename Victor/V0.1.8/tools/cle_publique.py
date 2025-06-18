# Importation de toutes les libraries nécessaires
import socket
import threading
import os

# Variables globales et initialisations
BUFFER_SIZE = 1024
ma_cle_publique = ""
public_keys = {}
logs = []

# Fonction s'occupant de charger la clé publique
def charger_cle_publique(chemin="../../test_cle_publique.pem"):
    global ma_cle_publique
    # Vérification du chemin et lecture
    if os.path.exists(chemin):
        with open(chemin, 'r') as f:
            ma_cle_publique = f.read().strip()
            logs.append("[INFO] Clé publique chargée depuis le fichier.")
    else:
        logs.append("[AVERTISSEMENT] Fichier de clé publique introuvable.")

# Fonction s'occupant de l'échange des clés publiques entre pairs
def echanger_cles_publiques(ip):
    logs.append(f"[DEBUG] Démarrage de l’échange de clé avec {ip}")
    # Vérification de la présence de l'IP dans les clés déjà ajoutées
    if ip in public_keys:
        return True
    # Vérification qu'il ne s'agisse pas de ma propre clé
    if not ma_cle_publique:
        logs.append("[ERREUR] Clé publique locale non chargée.")
        return False
    # Transaction des clés publiques, perso et destinataire
    try:
        # Partie envoi
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, TCP_PORT))
            s.send(f"PUBKEY:{ma_cle_publique}".encode())
            logs.append(f"[INFO] Clé publique envoyée à {ip}")
            data = s.recv(BUFFER_SIZE).decode()
            # Partie réception
            if data.startswith("PUBKEY:"):
                key = data.split(":", 1)[1]
                public_keys[ip] = key
                logs.append(f"[DEBUG] Échange de clé réussi avec {ip}")
                logs.append(f"[INFO] Clé publique reçue de {ip}")
                return True
            else:
                logs.append(f"[ERREUR] Réponse inattendue lors de l'échange de clé avec {ip}")
                return False
    except Exception as e:
        logs.append(f"[ERREUR] Échec de l'échange de clé avec {ip} : {e}")
        return False

def get_public_keys():
    return public_keys

def get_cle_publique():
    return ma_cle_publique

def get_logs():
    return logs