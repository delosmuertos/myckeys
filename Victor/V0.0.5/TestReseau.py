import socket
import threading
import time

BROADCAST_PORT = 50000
TCP_PORT = 50001
BROADCAST_INTERVAL = 5
BUFFER_SIZE = 1024

known_peers = set()
logs = []
messages = []
public_keys = {}

stop_event = threading.Event()

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

def menu():
    try:
        while True:
            print("\nMenu:")
            print("1. Afficher les pairs connus")
            print("2. Afficher les messages")
            print("3. Afficher les logs")
            print("4. Envoyer un message")
            print("5. Quitter")
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
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer_list[idx], TCP_PORT))
                    s.send(msg.encode())
            elif choix == '5':
                stop_event.set()
                break
            else:
                print("Choix invalide.")
    except KeyboardInterrupt:
        stop_event.set()

if __name__ == "__main__":
    threading.Thread(target=broadcast_presence, daemon=True).start()
    threading.Thread(target=listen_for_peers, daemon=True).start()
    threading.Thread(target=start_tcp_server, daemon=True).start()
    menu()
