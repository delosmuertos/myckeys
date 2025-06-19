# Importations nécessaire
import socket
import threading
import time
from tools.etat import known_peers, logs, stop_event, BROADCAST_PORT, BROADCAST_INTERVAL, BUFFER_SIZE
from tools.utils import get_local_ip

# Fonction permettant de se promouvoir au niveau du réseau, afin que nous puissions être détecté par les autres instances du prog
def broadcast_presence():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Boucle qui continue de tourner pour découvrir les pairs sur le réseau
        while not stop_event.is_set():
            message = "DISCOVER_PEER"
            s.sendto(message.encode(), ('<broadcast>', BROADCAST_PORT))
            time.sleep(BROADCAST_INTERVAL)

# Fonction permettant de découvrir les pairs sur le réseau
def listen_for_peers():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', BROADCAST_PORT))
        while not stop_event.is_set():
            # A la recherche de data sur le réseau avec en préambule DISCOVER_PEER
            try:
                data, addr = s.recvfrom(BUFFER_SIZE)
                if data.decode() == "DISCOVER_PEER":
                    if addr[0] != get_local_ip():
                        known_peers.add(addr[0])
                        logs.append(f"[INFO] Nouveau pair découvert : {addr[0]}")
            except Exception as e:
                logs.append(f"[ERREUR] Message UDP mal formé : {e}")