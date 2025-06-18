# Importations nécessaires
import socket
import threading
from tools.etat import logs, messages, groupes, public_keys, stop_event, BUFFER_SIZE, TCP_PORT
from tools.utils import get_local_ip

def set_ma_cle_publique(valeur):
    global ma_cle_publique
    ma_cle_publique = valeur

# Soccupe de tout ce qui est récepption de message venant du réseau, clés et messages
def handle_client(conn, addr):
    try:
        # S'occupe de la réception et de l'interprétation de la clé publique
        data = conn.recv(BUFFER_SIZE).decode()
        if data.startswith("PUBKEY:"):
            peer_ip = addr[0]
            key = data.split(":", 1)[1]
            public_keys[peer_ip] = key
            logs.append(f"[INFO] Clé publique reçue de {peer_ip}")
            if ma_cle_publique:
                try:
                    conn.send(f"PUBKEY:{ma_cle_publique}".encode())
                    logs.append(f"[INFO] Clé publique renvoyée à {peer_ip}")
                except Exception as e:
                    logs.append(f"[ERREUR] Échec de la réponse de clé publique à {peer_ip} : {e}")
        # S'occupe de l'interprétation de la réception d'un message avec le préambule GROUPMSG
        elif data.startswith("GROUPMSG:"):
            try:
                _, nom, msg = data.split(":", 2)
                if nom not in groupes:
                    logs.append(f"[DEBUG] Groupe inconnu '{nom}' — création automatique")

                    if nom not in groupes:
                        groupes[nom] = {
                            "membres": [addr[0]],  # on initialise au moins avec l'expéditeur
                            "messages": []
                        }
                        logs.append(f"[INFO] Message de groupe reçu pour groupe inconnu '{nom}', groupe créé avec {addr[0]}")
                    else:
                        if addr[0] not in groupes[nom]["membres"]:
                            groupes[nom]["membres"].append(addr[0])
                            logs.append(f"[DEBUG] Ajout du nouvel expéditeur {addr[0]} au groupe existant '{nom}'")
                logs.append(f"[DEBUG] Message de groupe reçu de {addr[0]} pour '{nom}' : {msg}")
                groupes[nom]["messages"].append((addr[0], msg))
                logs.append(f"[INFO] Message de {addr[0]} reçu dans le groupe '{nom}' : {msg}")
            except Exception as e:
                logs.append(f"[ERREUR] Mauvais format de message GROUPMSG : {e}")
            return
        # S'occupe de la réception des messages avec le préambule JOINGROUP, receuillir toutes les informations du groupe
        elif data.startswith("JOINGROUP:"):
            try:
                _, nom, ips_str = data.split(":", 2)
                membres = ips_str.split(",")
                logs.append(f"[DEBUG] JOINGROUP reçu pour groupe '{nom}' avec membres : {membres}")

                if nom not in groupes:
                    groupes[nom] = {
                        "membres": [],
                        "messages": []
                    }
                    logs.append(f"[INFO] Nouveau groupe '{nom}' ajouté localement.")

                # Fusionner les membres
                anciens_membres = set(groupes[nom]["membres"])
                nouveaux_membres = set(membres)
                groupes[nom]["membres"] = list(anciens_membres.union(nouveaux_membres))
                logs.append(f"[INFO] Groupe '{nom}' mis à jour avec membres : {groupes[nom]['membres']}")

                # Échange de clés publiques avec les autres membres
                my_ip = get_local_ip()
                for ip in membres:
                    if ip != my_ip:
                        logs.append(f"[DEBUG] Tentative d'échange de clé avec {ip} à la réception du groupe")
                        echanger_cles_publiques(ip)

            except Exception as e:
                logs.append(f"[ERREUR] Mauvais format de message JOINGROUP : {e}")
            return
        else:
            messages.append((addr[0], data))
            logs.append(f"[INFO] Message reçu de {addr[0]} : {data}")
    except Exception as e:
        logs.append(f"[ERREUR] Connexion entrante mal formée : {e}")
    finally:
        conn.close()

# Lance le démon serveur TCP
def start_tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', TCP_PORT))
        s.listen()
        while not stop_event.is_set():
            try:
                s.settimeout(1.0)
                conn, addr = s.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue

def get_messages():
    return messages

def get_logs():
    return logs

def get_public_keys():
    return public_keys

def get_groupes():
    return groupes

def get_stop_event():
    return stop_event
    