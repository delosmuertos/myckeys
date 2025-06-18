# Importations et importations d'autres classes
import socket
from tools.cle_publique import echanger_cles_publiques
from tools.tcp_serveur import get_groupes, get_logs
from tools.etat import groupes, logs

# Initialisations et variables globales
TCP_PORT = 50001
logs = get_logs()
groupes = get_groupes()

# Fonction s'occupant de créer un groupe
def creer_groupe(nom, membres):
    if nom in groupes:
        logs.append(f"[AVERTISSEMENT] Un groupe nommé '{nom}' existe déjà.")
        return

    my_ip = get_local_ip()
    if my_ip not in membres:
        membres.append(my_ip)
        logs.append(f"[DEBUG] IP du créateur {my_ip} ajoutée à la liste des membres du groupe '{nom}'")

    logs.append(f"[DEBUG] Création du groupe '{nom}' avec membres (incluant soi) : {membres}")

    groupes[nom] = {
        "membres": membres,
        "messages": []
    }
    logs.append(f"[INFO] Groupe '{nom}' créé avec les membres : {membres}")

    for ip in membres:
        if ip == my_ip:
            logs.append(f"[DEBUG] Je suis {ip}, je ne m’envoie pas JOINGROUP")
            continue

        logs.append(f"[DEBUG] Tentative d’échange de clé avec {ip} lors de la création du groupe")
        if not echanger_cles_publiques(ip):
            logs.append(f"[ERREUR] Clé publique manquante pour {ip}, groupe incomplet.")
            continue

        try:
            logs.append(f"[DEBUG] Envoi de JOINGROUP à {ip}")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, TCP_PORT))
                group_info = f"JOINGROUP:{nom}:{','.join(membres)}"
                s.send(group_info.encode())
                logs.append(f"[INFO] Notification de groupe '{nom}' envoyée à {ip}")
        except Exception as e:
            logs.append(f"[ERREUR] Impossible de notifier {ip} pour le groupe '{nom}' : {e}")