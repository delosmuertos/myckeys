# Importations nécessaires, ainsi que d'autres classes
import socket
from tools.cle_publique import echanger_cles_publiques
from tools.tcp_serveur import get_groupes, get_logs

# Variables globales
TCP_PORT = 50001
logs = get_logs()
groupes = get_groupes()

# Fonction s'occupant d'envoyer un message
def envoyer_message(ip, msg):
    if not echanger_cles_publiques(ip):
        logs.append(f"[ERREUR] Envoi de message annulé, clé publique non échangée avec {ip}")
        return
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, TCP_PORT))
            s.send(msg.encode())
            logs.append(f"[INFO] Message envoyé à {ip} : {msg}")
    except Exception as e:
        logs.append(f"[ERREUR] Échec de l'envoi du message à {ip} : {e}")

# Fonction s'occupant d'envoyer un message en multicast, réutilise la logique d'envoi de message solo
def envoyer_message_multicast(ips, msg):
    for ip in ips:
        print(f"[INFO] Envoi au pair {ip} ...")
        envoyer_message(ip, msg)

# Fonction permettant d'envoyer un message à un groupe existant
def envoyer_message_dans_groupe(nom, msg):
    if nom not in groupes:
        logs.append(f"[ERREUR] Le groupe '{nom}' n'existe pas.")
        return
    membres = groupes[nom]["membres"]
    logs.append(f"[DEBUG] Envoi d’un message dans le groupe '{nom}'")
    logs.append(f"[DEBUG] Membres du groupe '{nom}' : {membres}")

    logs.append(f"[DEBUG] Envoi d’un message dans groupe '{nom}' aux membres : {membres}")
    for ip in membres:
        if ip == get_local_ip():
            logs.append(f"[DEBUG] Ignoré : moi-même ({ip})")
            continue  # Ne pas s'envoyer à soi-même
        logs.append(f"[DEBUG] Tentative d'envoi à {ip} pour le groupe '{nom}'")
        envoyer_message(ip, f"GROUPMSG:{nom}:{msg}")
    groupes[nom]["messages"].append(("Moi", msg))
    logs.append(f"[DEBUG] Message ajouté localement dans groupe '{nom}'")
    logs.append(f"[INFO] Message envoyé au groupe '{nom}' : {msg}")