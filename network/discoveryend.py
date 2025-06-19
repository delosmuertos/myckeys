import socket
import threading
import time
import json

BROADCAST_PORT = 50000
BROADCAST_INTERVAL = 5
BUFFER_SIZE = 1024

class NetworkDiscovery:
    def __init__(self, username="User", on_peer_discovered=None, on_peer_lost=None):
        self.username = username
        self.known_peers = {}  # ip -> {nom, ip, status, last_seen}
        self.stop_event = threading.Event()
        self.on_peer_discovered = on_peer_discovered  # callback(ip, nom)
        self.on_peer_lost = on_peer_lost  # callback(ip)
        self.peer_timeout = 30  # 30 secondes de timeout pour un pair

    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    def broadcast_presence(self):
        print(f"[DEBUG] Démarrage du broadcast pour {self.username}")
        local_ip = self.get_local_ip()
        print(f"[DEBUG] IP locale: {local_ip}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            while not self.stop_event.is_set():
                message = {
                    "type": "DISCOVER_PEER",
                    "username": self.username
                }
                try:
                    s.sendto(json.dumps(message).encode(), ('<broadcast>', BROADCAST_PORT))
                    print(f"[DEBUG] Broadcast envoyé: {message} depuis {local_ip}")
                except Exception as e:
                    print(f"[DEBUG] Erreur broadcast: {e}")
                time.sleep(BROADCAST_INTERVAL)

    def listen_for_peers(self):
        local_ip = self.get_local_ip()
        print(f"[DEBUG] Démarrage de l'écoute sur le port {BROADCAST_PORT}")
        print(f"[DEBUG] IP locale: {local_ip}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Lier à toutes les interfaces (plus simple et plus fiable)
            s.bind(('', BROADCAST_PORT))
            print(f"[DEBUG] Écoute liée à toutes les interfaces")
            
            while not self.stop_event.is_set():
                try:
                    data, addr = s.recvfrom(BUFFER_SIZE)
                    message = json.loads(data.decode())
                    print(f"[DEBUG] Message reçu de {addr}: {message}")
                    if message.get("type") == "DISCOVER_PEER":
                        peer_ip = addr[0]
                        print(f"[DEBUG] Vérification: peer_ip={peer_ip}, local_ip={local_ip}")
                        if peer_ip != local_ip:
                            peer_name = message.get("username", "Inconnu")
                            print(f"[DEBUG] Nouveau pair détecté: {peer_name} ({peer_ip})")
                            
                            # Mettre à jour ou ajouter le pair
                            current_time = time.time()
                            if peer_ip not in self.known_peers:
                                self.known_peers[peer_ip] = {
                                    'nom': peer_name,
                                    'ip': peer_ip,
                                    'status': 'online',
                                    'last_seen': current_time
                                }
                                print(f"[DEBUG] Nouveau pair ajouté: {peer_name} ({peer_ip})")
                                if self.on_peer_discovered:
                                    print(f"[DEBUG] Appel du callback on_peer_discovered")
                                    self.on_peer_discovered(peer_ip, peer_name)
                            else:
                                # Mettre à jour le timestamp
                                self.known_peers[peer_ip]['last_seen'] = current_time
                                print(f"[DEBUG] Pair mis à jour: {peer_ip}")
                        else:
                            print(f"[DEBUG] Message ignoré (provenance locale)")
                except Exception as e:
                    print(f"Erreur lors de la découverte: {e}")
                    pass

    def cleanup_inactive_peers(self):
        """Nettoie les pairs inactifs"""
        current_time = time.time()
        inactive_peers = []
        
        for ip, peer_info in self.known_peers.items():
            if current_time - peer_info.get('last_seen', 0) > self.peer_timeout:
                inactive_peers.append(ip)
        
        for ip in inactive_peers:
            print(f"[DEBUG] Suppression du pair inactif: {ip}")
            del self.known_peers[ip]
            if self.on_peer_lost:
                print(f"[DEBUG] Appel du callback on_peer_lost pour {ip}")
                self.on_peer_lost(ip)

    def start(self):
        """Démarre les threads de broadcast et d'écoute"""
        print(f"[DEBUG] Démarrage de NetworkDiscovery pour {self.username}")
        
        # Démarrer les threads
        threading.Thread(target=self.broadcast_presence, daemon=True).start()
        threading.Thread(target=self.listen_for_peers, daemon=True).start()
        
        # Envoyer un broadcast immédiat pour se faire connaître rapidement
        self._send_immediate_broadcast()

    def _send_immediate_broadcast(self):
        """Envoie un broadcast immédiat pour se faire connaître"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                message = {
                    "type": "DISCOVER_PEER",
                    "username": self.username
                }
                s.sendto(json.dumps(message).encode(), ('<broadcast>', BROADCAST_PORT))
                print(f"[DEBUG] Broadcast immédiat envoyé: {message}")
        except Exception as e:
            print(f"[DEBUG] Erreur broadcast immédiat: {e}")

    def stop(self):
        self.stop_event.set()

    def get_known_peers(self):
        return self.known_peers.copy() 