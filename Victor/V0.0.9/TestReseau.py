'''
Changelog :

Inclusion d'un mode envoi groupé (multicast)
''' 

import socket
import threading
import time
import os

BROADCAST_PORT = 50000
TCP_PORT = 50001
BROADCAST_INTERVAL = 5
BUFFER_SIZE = 1024

known_peers = set()
logs = []
messages = []
public_keys = {}
cles_envoyees = set()
ma_cle_publique = ""

stop_event = threading.Event()

def charger_cle_publique():
    global ma_cle_publique
    chemin = "/home/victor/Bureau/GES/Année 2/Projet Messagerie Chiffrée/Code/test_cle_publique.pem"
    if os.path.exists(chemin):
        with open(chemin, 'r') as f:
            ma_cle_publique = f.read().strip()
            logs.append("[INFO] Clé publique chargée depuis le fichier.")
    else:
        logs.append("[AVERTISSEMENT] Fichier de clé publique introuvable.")

def broadcast_presence():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while not stop_event.is_set():
            message = "DISCOVER_PEER"
            s.sendto(message.encode(), ('<broadcast>', BROADCAST_PORT))
            time.sleep(BROADCAST_INTERVAL)

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

def handle_client(conn, addr):
    try:
        data = conn.recv(BUFFER_SIZE).decode()
        if data.startswith("PUBKEY:"):
            peer_ip = addr[0]
            key = data.split(":", 1)[1]
            public_keys[peer_ip] = key
            logs.append(f"[INFO] Clé publique reçue de {peer_ip}")
            # Répondre automatiquement avec notre propre clé publique
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

def echanger_cles_publiques(ip):
    if not ma_cle_publique:
        logs.append("[ERREUR] Clé publique locale non chargée.")
        return
    if ip in cles_envoyees:
        return
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, TCP_PORT))
            s.send(f"PUBKEY:{ma_cle_publique}".encode())
            logs.append(f"[INFO] Clé publique envoyée à {ip}")
            cles_envoyees.add(ip)
            # Réception de la clé publique du pair (si réponse immédiate)
            try:
                s.settimeout(2.0)
                data = s.recv(BUFFER_SIZE).decode()
                if data.startswith("PUBKEY:"):
                    key = data.split(":", 1)[1]
                    public_keys[ip] = key
                    logs.append(f"[INFO] Clé publique reçue de {ip}")
            except socket.timeout:
                logs.append(f"[INFO] Aucun retour de clé publique de {ip} (timeout)")
    except Exception as e:
        logs.append(f"[ERREUR] Échec de l'échange de clé avec {ip} : {e}")

def envoyer_message(ip, msg):
    echanger_cles_publiques(ip)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, TCP_PORT))
            s.send(msg.encode())
            logs.append(f"[INFO] Message envoyé à {ip} : {msg}")
    except Exception as e:
        logs.append(f"[ERREUR] Échec de l'envoi du message à {ip} : {e}")

def envoyer_message_groupe(ips, msg):
    for ip in ips:
        print(f"[INFO] Envoi au pair {ip} ...")
        envoyer_message(ip, msg)

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

if __name__ == "__main__":
    charger_cle_publique()
    threading.Thread(target=broadcast_presence, daemon=True).start()
    threading.Thread(target=listen_for_peers, daemon=True).start()
    threading.Thread(target=start_tcp_server, daemon=True).start()
    menu()
