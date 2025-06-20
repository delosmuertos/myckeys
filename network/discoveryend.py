import socket
import threading
import time
import json

BROADCAST_PORT = 50000
BROADCAST_INTERVAL = 5  # Envoyer un broadcast toutes les 5 secondes
BUFFER_SIZE = 1024

class NetworkDiscovery:
    def __init__(self, username="User", on_peer_discovered=None, on_peer_lost=None):
        self.username = username
        self.known_peers = {}  # ip -> {nom, ip, status, last_seen}
        self.stop_event = threading.Event()
        self.on_peer_discovered = on_peer_discovered  # callback(ip, nom)
        self.on_peer_lost = on_peer_lost  # callback(ip)
        self.peer_timeout = 30  # Secondes d'inactivité avant de considérer un pair comme perdu

    def get_local_ip(self):
        """Tente de récupérer l'IP locale pour éviter de se découvrir soi-même."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Se connecte à une IP externe (sans envoyer de données) pour obtenir l'IP de l'interface sortante
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"  # Fallback

    def broadcast_presence(self):
        """Envoie périodiquement un message de présence sur le réseau."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = {
                "type": "DISCOVER_PEER",
                "username": self.username
            }
            encoded_message = json.dumps(message).encode()
            
            while not self.stop_event.is_set():
                try:
                    s.sendto(encoded_message, ('<broadcast>', BROADCAST_PORT))
                except Exception as e:
                    print(f"[ERREUR][DISCOVERY] Erreur lors du broadcast: {e}")
                time.sleep(BROADCAST_INTERVAL)

    def listen_for_peers(self):
        """Écoute les messages de présence des autres pairs."""
        local_ip = self.get_local_ip()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', BROADCAST_PORT))
            
            while not self.stop_event.is_set():
                try:
                    data, addr = s.recvfrom(BUFFER_SIZE)
                    peer_ip = addr[0]

                    # Ignorer les messages venant de soi-même
                    if peer_ip == local_ip:
                        continue

                    message = json.loads(data.decode())
                    if message.get("type") == "DISCOVER_PEER":
                        peer_name = message.get("username", "Inconnu")
                        current_time = time.time()
                        
                        if peer_ip not in self.known_peers:
                            # Nouveau pair découvert
                            self.known_peers[peer_ip] = {'nom': peer_name, 'last_seen': current_time}
                            if self.on_peer_discovered:
                                self.on_peer_discovered(peer_ip, peer_name)
                        else:
                            # Pair déjà connu, mettre à jour son timestamp
                            self.known_peers[peer_ip]['last_seen'] = current_time

                except Exception as e:
                    print(f"[ERREUR][DISCOVERY] Erreur lors de l'écoute: {e}")

    def cleanup_inactive_peers(self):
        """Vérifie et supprime les pairs inactifs."""
        current_time = time.time()
        inactive_peers = [ip for ip, data in self.known_peers.items() if current_time - data['last_seen'] > self.peer_timeout]
        
        for ip in inactive_peers:
            del self.known_peers[ip]
            if self.on_peer_lost:
                self.on_peer_lost(ip)

    def start(self):
        """Démarre les threads de broadcast et d'écoute."""
        threading.Thread(target=self.broadcast_presence, daemon=True).start()
        threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def stop(self):
        """Arrête les threads."""
        self.stop_event.set()

    def get_known_peers(self):
        """Retourne une copie des pairs connus."""
        return self.known_peers.copy() 