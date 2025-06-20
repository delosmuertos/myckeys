import socket
import threading
import json

TCP_PORT = 50001
BUFFER_SIZE = 1024

class PeerCommunicator:
    def __init__(self, get_local_ip_func, key_exchange_func, on_key_received_func, log_func=None):
        self.get_local_ip = get_local_ip_func
        self.key_exchange = key_exchange_func
        self.on_key_received = on_key_received_func
        self.log = log_func if log_func else lambda msg: None
        self.public_keys = {}
        self.groupes = {}
        self.messages = []
        self.stop_event = threading.Event()
        
        # Callbacks pour les messages reçus
        self.on_message_received = None
        self.on_group_message_received = None
        self.local_public_key = None
        self.server_socket = None
        self.is_running = False

    def set_local_public_key(self, key: str):
        """Définit la clé publique locale à utiliser pour les réponses."""
        self.local_public_key = key

    def handle_client(self, conn, addr):
        self.log(f"[DEBUG] PEER_COMMUNICATOR: Connexion reçue de {addr[0]}")
        try:
            data = conn.recv(BUFFER_SIZE).decode()
            self.log(f"[DEBUG] PEER_COMMUNICATOR: Données reçues de {addr[0]}: {data[:100]}...")
            if data.startswith("PUBKEY:"):
                peer_ip = addr[0]
                key_pem = data.split(":", 1)[1]
                self.log(f"[INFO] Demande d'échange de clé reçue de {peer_ip}")

                # Mettre à jour la clé de l'expéditeur
                if self.on_key_received:
                    self.on_key_received(peer_ip, key_pem)

                # Envoyer notre propre clé en réponse
                if self.local_public_key:
                    response = f"PUBKEY:{self.local_public_key}"
                    conn.sendall(response.encode())
                    self.log(f"[INFO] Clé publique locale envoyée à {peer_ip}")
                else:
                    self.log("[ERREUR] Clé publique locale non disponible pour répondre.")
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
                # Si le message n'est pas une commande système, on suppose que c'est un message direct chiffré.
                # On le transmet au NetworkManager qui le passera au MessageManager pour déchiffrement.
                self.log(f"[DEBUG] PEER_COMMUNICATOR: Message direct reçu de {addr[0]}. Transmission pour déchiffrement.")
                if self.on_message_received:
                    self.on_message_received(addr[0], data)
        except Exception as e:
            self.log(f"[ERREUR] Erreur lors du traitement de la connexion de {addr}: {e}")
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

    def start(self) -> None:
        """Démarre le serveur TCP dans un thread séparé."""
        self.is_running = True
        self.start_tcp_server()

    def stop(self):
        self.stop_event.set() 