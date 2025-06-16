import socket
import psutil
import threading
import time

UDP_PORT = 37020            # Port utilisé pour les messages de broadcast (Pas besoin de handshake)
TCP_PORT = 12345            # Port d'écoute pour les messages
BROADCAST_INTERVAL = 3      # Combien de temps entre les broadcasts
BUFFER_SIZE = 1024          # Taille max des messages lus
known_peers = set()         # Ensemble, pour stocker les pairs déjà découverts, n'est pas un tableau !
received_messages = []      # Un tableau pour stocker les messages
logs = []                   # Un tableau pour stocker les logs
public_keys = {}            # Un dictionnaire pour stocker les clés publiques reçues

# Utiisation d'une sorte de leurre pour savoir quelle interface le système va utiliser, le code va donc enregistrer l'IP
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

LOCAL_IP = get_local_ip()
logs.append(f"[INIT] Adresse IP locale : {LOCAL_IP}")


def udp_broadcast():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Demande de création de socket UDP
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # Configuration de la socket pour envoyer en mode broadcast
    msg = f"{LOCAL_IP}:{TCP_PORT}".encode() # On envoie en broadcast l'IP local de mon PC (du pair) ainsi que son port par lequel on va communiquer

    while True:  # Envoi en boucle sur le réseau
        udp_sock.sendto(msg, ('<broadcast>', UDP_PORT)) # Envoi du message avec Adresse et Port, via l'IP de broadcast ainsi que le port qu'on a choisi au début
        logs.append(f"[BROADCAST] Annonce envoyée depuis {LOCAL_IP}:{TCP_PORT}") # Mise en logs
        time.sleep(BROADCAST_INTERVAL) # Un temps d'attente pour éviter de bombarder le réseau de requêtes


def udp_listener():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Demande de création de socket UDP
    udp_sock.bind(('', UDP_PORT)) # On réserve la socket demandé à un port de notre choix, mais on écoute sur toutes les interfaces
    while True: # Tant que la condition est vraie
        data, addr = udp_sock.recvfrom(1024) # Stockage de la data et des informations de l'envoyeur
        try:
            peer_ip_port = data.decode() # Décodage de la data reçue
            ip, port = peer_ip_port.split(':') # On sépare l'IP et le port dans des variables
            if ip == LOCAL_IP: # Vérifie que ce qu'on a reçu n'est pas nous même
                continue
            peer = (ip, int(port))
            if peer not in known_peers: # Vérification si le pair distant est nouveau, comparaison avec l'ensemble
                known_peers.add(peer) # Ajout du pair dans l'ensemble
                logs.append(f"[DISCOVERY] Nouveau pair détecté : {peer}") # Affichage dans le terminal du nouveau pair
        except:
            logs.append("[ERREUR] Message UDP mal formé.")


def tcp_server():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Demande de cr"ation d'une socket en TCP (SOCK_STREAM)
    tcp_sock.bind((LOCAL_IP, TCP_PORT)) # Attribution d'une adresse d'écoute et d'un port
    tcp_sock.listen() # Mise en écoute
    logs.append(f"[TCP] En écoute sur {LOCAL_IP}:{TCP_PORT}")
    while True: # Tant que c'est vrai
        conn, addr = tcp_sock.accept() # Accepte les connexions des pair grâce à l'IP de celui-ci
        logs.append(f"[TCP] Connexion de {addr}")
        threading.Thread(target=handle_connection, args=(conn, addr)).start()  # Lancement dans un thread

# Fonction appelée pour prendre en charge la connexion avec un pair, l'envoi de message et l'échange de clés
def handle_connection(conn, addr):
    with conn: # Objet utilisé pour communiquer avec le pair
        try:
            first_data = conn.recv(BUFFER_SIZE) # On met les données reçues dans first_data
            if first_data.startswith(b"[KEY]"): # Si les données commencent par [KEY] alors
                key = first_data.decode()[5:]
                public_keys[addr] = key
                logs.append(f"[CLÉ PUBLIQUE] Reçue de {addr} : {key}")
            else:
                msg = first_data.decode() # Si ce n'est pas une clé, alors on l'interprête comme un message
                received_messages.append((addr, msg)) # On enregistre ça dans received_messages
                logs.append(f"[REÇU] de {addr} : {msg}") # Logs

            while True: # Tant que c'est vrai
                data = conn.recv(BUFFER_SIZE) # Enregistrement des données reçues dans datz
                if not data: # Un failsafe
                    break
                msg = data.decode() # On enregistre la donnée dans message
                received_messages.append((addr, msg)) # On ajoute aux messages reçus
                logs.append(f"[REÇU] de {addr} : {msg}") # Logs
        except:
            logs.append(f"[ERREUR] Connexion interrompue avec {addr}")


def menu():
    while True: # Affichage du menu tant qu'on quite pas
        print("\n========= MENU =========")
        print("1 - Afficher les pairs connus")
        print("2 - Envoyer un message à un pair")
        print("3 - Voir les messages reçus")
        print("4 - Voir les logs système")
        print("5 - Voir les clés publiques des pairs")
        print("q - Quitter")
        choix = input("Choix > ").strip()

        if choix == "1":
            print("\n--- Pairs connus ---")
            for i, peer in enumerate(known_peers):
                print(f"{i}: {peer}") # Enumaration des éléments dans known_peers
        elif choix == "2":
            if not known_peers:
                print("Aucun pair disponible.") # Failsafe si jamais il n'y a pas de pairs trouvés
                continue
            print("\nChoisir un pair :")
            for i, peer in enumerate(known_peers):
                print(f"{i}: {peer}") # Enumération des pairs trouvés précédemment
            try:
                idx = int(input("Numéro du pair > ")) # On entre un numéro de pair celon la liste
                peer = list(known_peers)[idx] # On compare
                msg = input("Message > ") # On entre un message
                with socket.create_connection(peer, timeout=5) as sock:
                    fake_key = "FAKE_PUBLIC_KEY_123" # Création d'une fake clé publique pour le test 
                    sock.sendall(f"[KEY]{fake_key}".encode()) # Envoi aux pairs
                    time.sleep(0.1) # Un sleep
                    sock.sendall(msg.encode())
                    logs.append(f"[ENVOYÉ] à {peer} : {msg}")
            except Exception as e:
                print(f"Erreur : {e}")
        elif choix == "3":
            print("\n--- Messages reçus ---")
            for addr, msg in received_messages:
                print(f"De {addr} > {msg}") # Affichage des messages reçus
        elif choix == "4":
            print("\n--- Logs ---")
            for log in logs[-20:]:
                print(log) # Affichage des logs
        elif choix == "5":
            print("\n--- Clés publiques connues ---")
            for peer, key in public_keys.items():
                print(f"{peer} > {key}") # Affichages de clés publiques en fonction des pairs
        elif choix == "q":
            print("Au revoir.")
            break
        else:
            print("Choix invalide.")

# Système mettant en threads les différentes fonctions du programme 
if __name__ == "__main__":
    threading.Thread(target=udp_broadcast, daemon=True).start()
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=tcp_server, daemon=True).start()

    print("[SYSTEME] Peer lancé. Interface en cours...")
    menu()
