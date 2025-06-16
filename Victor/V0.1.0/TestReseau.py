'''
Changelog :

Correction de l'échange de clé :
- Vérification robuste si échange a déjà eu lieu
- Echange de clé symétique groupe ou solo --> Blocage tant que la clé n'a pas été reçue
- 
''' 

# Importations nécessaire au bon fonctionnement du prog
import socket
import threading
import time
import os

# Variables globales servant pour le réseau, les ports, ...
BROADCAST_PORT = 50000
TCP_PORT = 50001
BROADCAST_INTERVAL = 5
BUFFER_SIZE = 1024

# Initialisation des tableaux et ensembles
known_peers = set()
logs = []
messages = []
public_keys = {}
ma_cle_publique = ""

stop_event = threading.Event()

# Fonction s'occupoant de charger la clé publique à partir d'un chemin donné, vérification de présence de la clé intégrée
def charger_cle_publique():
    global ma_cle_publique
    chemin = "../test_cle_publique.pem"
    if os.path.exists(chemin):
        with open(chemin, 'r') as f:
            ma_cle_publique = f.read().strip()
            logs.append("[INFO] Clé publique chargée depuis le fichier.")
    else:
        logs.append("[AVERTISSEMENT] Fichier de clé publique introuvable.")

# Fonction permettant de se promouvoir au niveau du réseau, afin que nous puissions être détecté par les autres instances du prog
def broadcast_presence():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while not stop_event.is_set():
            message = "DISCOVER_PEER"
            s.sendto(message.encode(), ('<broadcast>', BROADCAST_PORT))
            time.sleep(BROADCAST_INTERVAL)

# Fonction permettant de découvrir les pairs sur le réseau
def listen_for_peers():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', BROADCAST_PORT))
        while not stop_event.is_set():
            try:
                data, addr = s.recvfrom(BUFFER_SIZE)
                if data.decode() == "DISCOVER_PEER":
                    if addr[0] != socket.gethostbyname(socket.gethostname()):
                        known_peers.add(addr[0])
                        logs.append(f"[INFO] Nouveau pair découvert : {addr[0]}")
            except Exception as e:
                logs.append(f"[ERREUR] Message UDP mal formé : {e}")

# Soccupe de tout ce qui est récepption de message venant du réseau, clés et messages
def handle_client(conn, addr):
    try:
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

# Logique derrière l'échange de clé publiques lors du premier envoi de message entre deux nouveaux pairs
def echanger_cles_publiques(ip):
    if ip in public_keys:
        return True
    if not ma_cle_publique:
        logs.append("[ERREUR] Clé publique locale non chargée.")
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, TCP_PORT))
            s.send(f"PUBKEY:{ma_cle_publique}".encode())
            logs.append(f"[INFO] Clé publique envoyée à {ip}")
            data = s.recv(BUFFER_SIZE).decode()
            if data.startswith("PUBKEY:"):
                key = data.split(":", 1)[1]
                public_keys[ip] = key
                logs.append(f"[INFO] Clé publique reçue de {ip}")
                return True
            else:
                logs.append(f"[ERREUR] Réponse inattendue lors de l'échange de clé avec {ip}")
                return False
    except Exception as e:
        logs.append(f"[ERREUR] Échec de l'échange de clé avec {ip} : {e}")
        return False

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
def envoyer_message_groupe(ips, msg):
    for ip in ips:
        print(f"[INFO] Envoi au pair {ip} ...")
        envoyer_message(ip, msg)

# Menu permettant de choisir quoi faire
def menu():
    try:
        while True:
            print("\nMenu:")
            print("1. Afficher les pairs connus")
            print("2. Afficher les messages")
            print("3. Afficher les logs")
            print("4. Envoyer un message")
            print("5. Envoyer un message à un groupe")
            print("6. Afficher les clés publiques reçues")
            print("7. Quitter")
            choix = input("> ")

            if choix == '1':
                for peer in known_peers:
                    print(f"- {peer}")
            elif choix == '2':
                for sender, msg in messages:
                    print(f"De {sender} : {msg}")
            elif choix == '3':
                for log in logs:
                    print(log)
            elif choix == '4':
                peer_list = list(known_peers)
                for i, peer in enumerate(peer_list):
                    print(f"{i}. {peer}")
                idx = int(input("Choisissez un pair : "))
                if idx < 0 or idx >= len(peer_list):
                    print("Index invalide.")
                    continue
                msg = input("Message à envoyer : ")
                envoyer_message(peer_list[idx], msg)
            elif choix == '5':
                peer_list = list(known_peers)
                if not peer_list:
                    print("Aucun pair disponible.")
                    continue
                print("Paires disponibles :")
                for i, peer in enumerate(peer_list):
                    print(f"{i}. {peer}")
                selection = input("Entrez les indices séparés par des virgules ou 'tous' : ")
                if selection.lower() == 'tous':
                    destinataires = peer_list
                else:
                    try:
                        indices = [int(i.strip()) for i in selection.split(',')]
                        destinataires = [peer_list[i] for i in indices if 0 <= i < len(peer_list)]
                    except Exception:
                        print("Entrée invalide.")
                        continue
                msg = input("Message à envoyer au groupe : ")
                envoyer_message_groupe(destinataires, msg)
            elif choix == '6':
                if public_keys:
                    for ip, key in public_keys.items():
                        print(f"{ip} : {key}")
                else:
                    print("Aucune clé publique reçue.")
            elif choix == '7':
                stop_event.set()
                break
            else:
                print("Choix invalide.")
    except KeyboardInterrupt:
        stop_event.set()

# Gestion de threads
if __name__ == "__main__":
    charger_cle_publique()
    threading.Thread(target=broadcast_presence, daemon=True).start()
    threading.Thread(target=listen_for_peers, daemon=True).start()
    threading.Thread(target=start_tcp_server, daemon=True).start()
    menu()
