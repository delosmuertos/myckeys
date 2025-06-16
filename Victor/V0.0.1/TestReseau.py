import socket
import threading
import time

UDP_PORT = 37020
TCP_PORT = 12345  # Port d'écoute pour la messagerie
BROADCAST_INTERVAL = 3  # secondes
BUFFER_SIZE = 1024
known_peers = set()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connexion factice pour récupérer l'IP locale
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

LOCAL_IP = get_local_ip()

def udp_broadcast():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msg = f"{LOCAL_IP}:{TCP_PORT}".encode()

    while True:
        udp_sock.sendto(msg, ('<broadcast>', UDP_PORT))
        time.sleep(BROADCAST_INTERVAL)

def udp_listener():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('', UDP_PORT))
    while True:
        data, addr = udp_sock.recvfrom(1024)
        peer_ip_port = data.decode()
        ip, port = peer_ip_port.split(':')
        if ip == LOCAL_IP:
            continue  # ne pas se connecter à soi-même
        peer = (ip, int(port))
        if peer not in known_peers:
            known_peers.add(peer)
            print(f"[DISCOVERY] Nouveau pair détecté : {peer}")
            threading.Thread(target=tcp_client, args=(peer,)).start()

def tcp_server():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind((LOCAL_IP, TCP_PORT))
    tcp_sock.listen()
    print(f"[TCP] En écoute sur {LOCAL_IP}:{TCP_PORT}")
    while True:
        conn, addr = tcp_sock.accept()
        print(f"[TCP] Connexion de {addr}")
        threading.Thread(target=handle_connection, args=(conn, addr)).start()

def handle_connection(conn, addr):
    with conn:
        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                print(f"[REÇU de {addr}] {data.decode()}")
            except:
                break

def tcp_client(peer):
    ip, port = peer
    try:
        with socket.create_connection((ip, port), timeout=5) as sock:
            print(f"[TCP] Connecté à {peer}")
            while True:
                msg = input(f"[à {peer}] > ")
                sock.sendall(msg.encode())
    except Exception as e:
        print(f"[ERREUR TCP client] {e}")

if __name__ == "__main__":
    threading.Thread(target=udp_broadcast, daemon=True).start()
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=tcp_server, daemon=True).start()

    print("[SYSTEME] Peer lancé. En attente de connexions...\n")
    while True:
        time.sleep(1)  # Garde le main thread en vie
