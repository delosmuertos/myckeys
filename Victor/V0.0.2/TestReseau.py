import socket
import psutil
import threading
import time

UDP_PORT = 37020
TCP_PORT = 12345
BROADCAST_INTERVAL = 3
BUFFER_SIZE = 1024
known_peers = set()
received_messages = []
logs = []

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
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msg = f"{LOCAL_IP}:{TCP_PORT}".encode()

    while True:
        udp_sock.sendto(msg, ('<broadcast>', UDP_PORT))
        logs.append(f"[BROADCAST] Annonce envoyée depuis {LOCAL_IP}:{TCP_PORT}")
        time.sleep(BROADCAST_INTERVAL)


def udp_listener():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('', UDP_PORT))
    while True:
        data, addr = udp_sock.recvfrom(1024)
        try:
            peer_ip_port = data.decode()
            ip, port = peer_ip_port.split(':')
            if ip == LOCAL_IP:
                continue
            peer = (ip, int(port))
            if peer not in known_peers:
                known_peers.add(peer)
                logs.append(f"[DISCOVERY] Nouveau pair détecté : {peer}")
        except:
            logs.append("[ERREUR] Message UDP mal formé.")


def tcp_server():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind((LOCAL_IP, TCP_PORT))
    tcp_sock.listen()
    logs.append(f"[TCP] En écoute sur {LOCAL_IP}:{TCP_PORT}")
    while True:
        conn, addr = tcp_sock.accept()
        logs.append(f"[TCP] Connexion de {addr}")
        threading.Thread(target=handle_connection, args=(conn, addr)).start()


def handle_connection(conn, addr):
    with conn:
        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                msg = data.decode()
                logs.append(f"[REÇU] de {addr} : {msg}")
                received_messages.append((addr, msg))
            except:
                logs.append(f"[ERREUR] Connexion interrompue avec {addr}")
                break


def menu():
    while True:
        print("\n========= MENU =========")
        print("1 - Afficher les pairs connus")
        print("2 - Envoyer un message à un pair")
        print("3 - Voir les messages reçus")
        print("4 - Voir les logs système")
        print("q - Quitter")
        choix = input("Choix > ").strip()

        if choix == "1":
            print("\n--- Pairs connus ---")
            for i, peer in enumerate(known_peers):
                print(f"{i}: {peer}")
        elif choix == "2":
            if not known_peers:
                print("Aucun pair disponible.")
                continue
            print("\nChoisir un pair :")
            for i, peer in enumerate(known_peers):
                print(f"{i}: {peer}")
            try:
                idx = int(input("Numéro du pair > "))
                peer = list(known_peers)[idx]
                msg = input("Message > ")
                with socket.create_connection(peer, timeout=5) as sock:
                    sock.sendall(msg.encode())
                    logs.append(f"[ENVOYÉ] à {peer} : {msg}")
            except Exception as e:
                print(f"Erreur : {e}")
        elif choix == "3":
            print("\n--- Messages reçus ---")
            for addr, msg in received_messages:
                print(f"De {addr} > {msg}")
        elif choix == "4":
            print("\n--- Logs ---")
            for log in logs[-20:]:
                print(log)
        elif choix == "q":
            print("Au revoir.")
            break
        else:
            print("Choix invalide.")


if __name__ == "__main__":
    threading.Thread(target=udp_broadcast, daemon=True).start()
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=tcp_server, daemon=True).start()

    print("[SYSTEME] Peer lancé. Interface en cours...")
    menu()
