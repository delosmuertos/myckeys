import socket
import threading

TCP_PORT = 50001
BUFFER_SIZE = 1024

class PeerCommunicator:
    def __init__(self, get_local_ip_func, key_exchange_func, log_func=None):
        self.get_local_ip = get_local_ip_func
        self.key_exchange = key_exchange_func
        self.log = log_func if log_func else lambda msg: None
        self.public_keys = {}
        self.groupes = {}
        self.messages = []
        self.stop_event = threading.Event()
        
        # Callbacks pour les messages reçus
        self.on_message_received = None
        self.on_group_message_received = None

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(BUFFER_SIZE).decode()
            if data.startswith("PUBKEY:"):
                peer_ip = addr[0]
                key = data.split(":", 1)[1]
                self.public_keys[peer_ip] = key
                self.log(f"[INFO] Clé publique reçue de {peer_ip}")
                
                # Répondre automatiquement avec notre clé publique
                try:
                    # Récupérer notre clé publique via la fonction d'échange
                    if hasattr(self.key_exchange, '__self__'):
                        # Si key_exchange est une méthode liée, récupérer la clé publique
                        message_manager = self.key_exchange.__self__
                        if hasattr(message_manager, 'ma_cle_publique'):
                            ma_cle = message_manager.ma_cle_publique
                            if ma_cle:
                                response = f"PUBKEY:{ma_cle}"
                                conn.send(response.encode())
                                self.log(f"[INFO] Clé publique renvoyée à {peer_ip}")
                            else:
                                self.log(f"[ERREUR] Clé publique locale non disponible pour {peer_ip}")
                        else:
                            self.log(f"[ERREUR] Impossible de récupérer la clé publique locale")
                    else:
                        self.log(f"[ERREUR] Fonction d'échange de clés non disponible")
                except Exception as e:
                    self.log(f"[ERREUR] Échec de la réponse de clé publique à {peer_ip}: {e}")
                    
            elif data.startswith("GROUPMSG:"):
                try:
                    _, nom, msg = data.split(":", 2)
                    if nom not in self.groupes:
                        self.groupes[nom] = {"membres": [addr[0]], "messages": []}
                    self.groupes[nom]["messages"].append((addr[0], msg))
                    self.log(f"[INFO] Message de {addr[0]} reçu dans le groupe '{nom}' : {msg}")
                    
                    # Appeler le callback pour les messages de groupe
                    if self.on_group_message_received:
                        self.on_group_message_received(nom, addr[0], msg)
                        
                except Exception as e:
                    self.log(f"[ERREUR] Mauvais format de message GROUPMSG : {e}")
                return
            elif data.startswith("JOINGROUP:"):
                try:
                    _, nom, ips_str = data.split(":", 2)
                    membres = ips_str.split(",")
                    if nom not in self.groupes:
                        self.groupes[nom] = {"membres": [], "messages": []}
                    anciens_membres = set(self.groupes[nom]["membres"])
                    nouveaux_membres = set(membres)
                    self.groupes[nom]["membres"] = list(anciens_membres.union(nouveaux_membres))
                    my_ip = self.get_local_ip()
                    for ip in membres:
                        if ip != my_ip:
                            self.key_exchange(ip)
                except Exception as e:
                    self.log(f"[ERREUR] Mauvais format de message JOINGROUP : {e}")
                return
            else:
                # Message direct reçu (peut être chiffré ou non)
                self.messages.append((addr[0], data))
                self.log(f"[INFO] Message reçu de {addr[0]} : {data}")
                
                # Appeler le callback pour les messages directs
                if self.on_message_received:
                    self.on_message_received(addr[0], data)
        except Exception as e:
            self.log(f"[ERREUR] Connexion entrante mal formée : {e}")
        finally:
            conn.close()

    def start_tcp_server(self):
        def server_loop():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', TCP_PORT))
                s.listen()
                while not self.stop_event.is_set():
                    try:
                        s.settimeout(1.0)
                        conn, addr = s.accept()
                        threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
                    except socket.timeout:
                        continue
        threading.Thread(target=server_loop, daemon=True).start()

    def envoyer_message(self, ip, msg):
        if not self.key_exchange(ip):
            self.log(f"[ERREUR] Envoi de message annulé, clé publique non échangée avec {ip}")
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, TCP_PORT))
                s.send(msg.encode())
                self.log(f"[INFO] Message envoyé à {ip} : {msg}")
        except Exception as e:
            self.log(f"[ERREUR] Échec de l'envoi du message à {ip} : {e}")

    def envoyer_message_multicast(self, ips, msg):
        for ip in ips:
            self.envoyer_message(ip, msg)

    def creer_groupe(self, nom, membres):
        if nom in self.groupes:
            self.log(f"[AVERTISSEMENT] Un groupe nommé '{nom}' existe déjà.")
            return
        my_ip = self.get_local_ip()
        if my_ip not in membres:
            membres.append(my_ip)
        self.groupes[nom] = {"membres": membres, "messages": []}
        for ip in membres:
            if ip == my_ip:
                continue
            if not self.key_exchange(ip):
                self.log(f"[ERREUR] Clé publique manquante pour {ip}, groupe incomplet.")
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, TCP_PORT))
                    group_info = f"JOINGROUP:{nom}:{','.join(membres)}"
                    s.send(group_info.encode())
                    self.log(f"[INFO] Notification de groupe '{nom}' envoyée à {ip}")
            except Exception as e:
                self.log(f"[ERREUR] Impossible de notifier {ip} pour le groupe '{nom}' : {e}")

    def envoyer_message_dans_groupe(self, nom, msg):
        if nom not in self.groupes:
            self.log(f"[ERREUR] Le groupe '{nom}' n'existe pas.")
            return
        membres = self.groupes[nom]["membres"]
        for ip in membres:
            if ip == self.get_local_ip():
                continue
            self.envoyer_message(ip, f"GROUPMSG:{nom}:{msg}")
        self.groupes[nom]["messages"].append(("Moi", msg))
        self.log(f"[INFO] Message envoyé au groupe '{nom}' : {msg}")

    def start(self):
        """Démarre le serveur TCP"""
        self.start_tcp_server()

    def stop(self):
        self.stop_event.set() 