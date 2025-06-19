import socket
import json
import os
from typing import Dict, List, Tuple, Optional

class GroupManager:
    def __init__(self, get_local_ip_func, key_exchange_func, log_func=None):
        self.get_local_ip = get_local_ip_func
        self.key_exchange = key_exchange_func
        self.log = log_func if log_func else lambda msg: None
        self.groupes = {}
        self.TCP_PORT = 50001
        
        # Fichier de persistance
        self.storage_dir = os.path.join(os.path.dirname(__file__), '..', 'storage')
        self.groups_file = os.path.join(self.storage_dir, 'groups.json')
        
        # Charger les groupes sauvegardés
        self._load_groups()

    def creer_groupe(self, nom: str, membres: List[str]) -> bool:
        """Crée un nouveau groupe avec les membres spécifiés"""
        if nom in self.groupes:
            self.log(f"[AVERTISSEMENT] Un groupe nommé '{nom}' existe déjà.")
            return False

        # Vérification s'il ne s'agit pas de mon IP
        my_ip = self.get_local_ip()
        if my_ip not in membres:
            membres.append(my_ip)
            self.log(f"[DEBUG] IP du créateur {my_ip} ajoutée à la liste des membres du groupe '{nom}'")

        self.log(f"[DEBUG] Création du groupe '{nom}' avec membres (incluant soi) : {membres}")

        self.groupes[nom] = {
            "membres": membres,
            "messages": []
        }
        self.log(f"[INFO] Groupe '{nom}' créé avec les membres : {membres}")
        
        # Sauvegarder les groupes
        self._save_groups()

        # Notification des autres membres
        for ip in membres:
            if ip == my_ip:
                self.log(f"[DEBUG] Je suis {ip}, je ne m'envoie pas JOINGROUP, Duh")
                continue

            self.log(f"[DEBUG] Tentative d'échange de clé avec {ip} lors de la création du groupe")
            if not self.key_exchange(ip):
                self.log(f"[ERREUR] Clé publique manquante pour {ip}, groupe incomplet.")
                continue

            try:
                self.log(f"[DEBUG] Envoi de JOINGROUP à {ip}")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, self.TCP_PORT))
                    group_info = f"JOINGROUP:{nom}:{','.join(membres)}"
                    s.send(group_info.encode())
                    self.log(f"[INFO] Notification de groupe '{nom}' envoyée à {ip}")
            except Exception as e:
                self.log(f"[ERREUR] Impossible de notifier {ip} pour le groupe '{nom}' : {e}")

        return True

    def envoyer_message_dans_groupe(self, nom: str, msg: str) -> bool:
        """Envoie un message à tous les membres d'un groupe"""
        if nom not in self.groupes:
            self.log(f"[ERREUR] Le groupe '{nom}' n'existe pas.")
            return False

        membres = self.groupes[nom]["membres"]
        self.log(f"[DEBUG] Envoi d'un message dans le groupe '{nom}'")
        self.log(f"[DEBUG] Membres du groupe '{nom}' : {membres}")

        self.log(f"[DEBUG] Envoi d'un message dans groupe '{nom}' aux membres : {membres}")
        for ip in membres:
            if ip == self.get_local_ip():
                self.log(f"[DEBUG] Ignoré : moi-même ({ip})")
                continue  # Ne pas s'envoyer à soi-même
            
            self.log(f"[DEBUG] Tentative d'envoi à {ip} pour le groupe '{nom}'")
            self._envoyer_message_groupe(ip, nom, msg)

        # Ajout du message localement
        self.groupes[nom]["messages"].append(("Moi", msg))
        self.log(f"[DEBUG] Message ajouté localement dans groupe '{nom}'")
        self.log(f"[INFO] Message envoyé au groupe '{nom}' : {msg}")
        
        # Sauvegarder les groupes
        self._save_groups()
        
        return True

    def _envoyer_message_groupe(self, ip: str, nom_groupe: str, msg: str) -> bool:
        """Envoie un message de groupe à une IP spécifique"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, self.TCP_PORT))
                group_msg = f"GROUPMSG:{nom_groupe}:{msg}"
                s.send(group_msg.encode())
                self.log(f"[INFO] Message de groupe envoyé à {ip}")
                return True
        except Exception as e:
            self.log(f"[ERREUR] Échec de l'envoi du message de groupe à {ip} : {e}")
            return False

    def traiter_message_groupe(self, data: str, addr: str) -> bool:
        """Traite un message de groupe reçu"""
        try:
            _, nom, msg = data.split(":", 2)
            if nom not in self.groupes:
                self.log(f"[DEBUG] Groupe inconnu '{nom}' — création automatique")

                if nom not in self.groupes:
                    self.groupes[nom] = {
                        "membres": [addr],  # on initialise au moins avec l'expéditeur
                        "messages": []
                    }
                    self.log(f"[INFO] Message de groupe reçu pour groupe inconnu '{nom}', groupe créé avec {addr}")
                else:
                    if addr not in self.groupes[nom]["membres"]:
                        self.groupes[nom]["membres"].append(addr)
                        self.log(f"[DEBUG] Ajout du nouvel expéditeur {addr} au groupe existant '{nom}'")

            self.log(f"[DEBUG] Message de groupe reçu de {addr} pour '{nom}' : {msg}")
            self.groupes[nom]["messages"].append((addr, msg))
            self.log(f"[INFO] Message de {addr} reçu dans le groupe '{nom}' : {msg}")
            
            # Sauvegarder les groupes
            self._save_groups()
            
            return True
        except Exception as e:
            self.log(f"[ERREUR] Mauvais format de message GROUPMSG : {e}")
            return False

    def traiter_join_groupe(self, data: str, addr: str) -> bool:
        """Traite une demande de rejoindre un groupe"""
        try:
            _, nom, ips_str = data.split(":", 2)
            membres = ips_str.split(",")
            self.log(f"[DEBUG] JOINGROUP reçu pour groupe '{nom}' avec membres : {membres}")

            if nom not in self.groupes:
                self.groupes[nom] = {
                    "membres": [],
                    "messages": []
                }
                self.log(f"[INFO] Nouveau groupe '{nom}' ajouté localement.")

            # Fusionner les membres
            anciens_membres = set(self.groupes[nom]["membres"])
            nouveaux_membres = set(membres)
            self.groupes[nom]["membres"] = list(anciens_membres.union(nouveaux_membres))
            self.log(f"[INFO] Groupe '{nom}' mis à jour avec membres : {self.groupes[nom]['membres']}")
            
            # Sauvegarder les groupes
            self._save_groups()

            # Échange de clés publiques avec les autres membres
            my_ip = self.get_local_ip()
            for ip in membres:
                if ip != my_ip:
                    self.log(f"[DEBUG] Tentative d'échange de clé avec {ip} à la réception du groupe")
                    self.key_exchange(ip)

            return True
        except Exception as e:
            self.log(f"[ERREUR] Mauvais format de message JOINGROUP : {e}")
            return False

    def get_groupes(self) -> Dict:
        """Retourne tous les groupes"""
        return self.groupes

    def get_groupe(self, nom: str) -> Optional[Dict]:
        """Retourne un groupe spécifique"""
        return self.groupes.get(nom)

    def get_messages_groupe(self, nom: str) -> List[Tuple[str, str]]:
        """Retourne les messages d'un groupe"""
        if nom in self.groupes:
            return self.groupes[nom]["messages"]
        return []

    def get_membres_groupe(self, nom: str) -> List[str]:
        """Retourne les membres d'un groupe"""
        if nom in self.groupes:
            return self.groupes[nom]["membres"]
        return []

    def supprimer_groupe(self, nom: str) -> bool:
        """Supprime un groupe"""
        if nom in self.groupes:
            del self.groupes[nom]
            self.log(f"[INFO] Groupe '{nom}' supprimé")
            return True
        return False

    def ajouter_membre_groupe(self, nom: str, ip: str) -> bool:
        """Ajoute un membre à un groupe existant"""
        if nom in self.groupes and ip not in self.groupes[nom]["membres"]:
            self.groupes[nom]["membres"].append(ip)
            self.log(f"[INFO] Membre {ip} ajouté au groupe '{nom}'")
            return True
        return False

    def retirer_membre_groupe(self, nom: str, ip: str) -> bool:
        """Retire un membre d'un groupe"""
        if nom in self.groupes and ip in self.groupes[nom]["membres"]:
            self.groupes[nom]["membres"].remove(ip)
            self.log(f"[INFO] Membre {ip} retiré du groupe '{nom}'")
            return True
        return False

    def clear_group_messages(self, nom: str) -> bool:
        """Efface tous les messages d'un groupe spécifique"""
        if nom in self.groupes:
            self.groupes[nom]["messages"].clear()
            self.log(f"[INFO] Tous les messages du groupe '{nom}' ont été effacés")
            # Sauvegarder les groupes
            self._save_groups()
            return True
        return False

    def clear_all_group_messages(self) -> bool:
        """Efface tous les messages de tous les groupes"""
        for nom in self.groupes:
            self.groupes[nom]["messages"].clear()
        self.log(f"[INFO] Tous les messages de tous les groupes ont été effacés")
        # Sauvegarder les groupes
        self._save_groups()
        return True

    def _load_groups(self):
        """Charge les groupes sauvegardés"""
        if os.path.exists(self.groups_file):
            with open(self.groups_file, 'r') as f:
                self.groupes = json.load(f)
        else:
            self.groupes = {}

    def _save_groups(self):
        """Sauvegarde les groupes"""
        os.makedirs(self.storage_dir, exist_ok=True)
        with open(self.groups_file, 'w') as f:
            json.dump(self.groupes, f, indent=2) 