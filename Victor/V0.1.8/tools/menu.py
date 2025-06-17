# Importations des autres classes
from reseau.peers import get_known_peers
from reseau.messages import envoyer_message, envoyer_message_multicast
from reseau.groupes import creer_groupe
from reseau.tcp_serveur import get_groupes, get_messages, get_logs
from reseau.utils import detect_my_ip
from reseau.messages import envoyer_message_dans_groupe

def afficher_menu():
    known_peers = get_known_peers()
    messages = get_messages()
    logs = get_logs()
    groupes = get_groupes()

    try:
        while True:
            print("\nMenu:")
            print("1. Afficher les pairs connus")
            print("2. Afficher les messages")
            print("3. Afficher les logs")
            print("4. Envoyer un message")
            print("5. Envoyer un message en multicast")
            print("6. Afficher les clés publiques reçues")
            print("7. Créer un groupe")
            print("8. Envoyer un message à un groupe existant")
            print("9. Quitter")
            choix = input("> ")

            if choix == '1':
                for peer in known_peers:
                    print(f"- {peer}")
            elif choix == '2':
                print("\n--- Messages directs ---")
                if messages:
                    for sender, msg in messages:
                        print(f"De {sender} : {msg}")
                else:
                    print("Aucun message direct reçu.")

                print("\n--- Messages de groupes ---")
                if groupes:
                    for nom, data in groupes.items():
                        print(f"\n[Groupe : {nom}]")
                        if data["messages"]:
                            for sender, msg in data["messages"]:
                                print(f"De {sender} : {msg}")
                        else:
                            print("Aucun message dans ce groupe.")
                else:
                    print("Aucun groupe enregistré.")
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
                envoyer_message(peer_list[idx], msg)
            elif choix == '5':
                peer_list = list(known_peers)
                if not peer_list:
                    print("Aucun pair disponible.")
                    continue
                print("Paires disponibles :")
                for i, peer in enumerate(peer_list):
                    print(f"{i}. {peer}")
                selection = input("Entrez les indices des pairs à cibler (ex: 0,1) ou 'tous' : ")
                if selection.lower() == 'tous':
                    destinataires = peer_list
                else:
                    try:
                        indices = [int(i.strip()) for i in selection.split(',')]
                        destinataires = [peer_list[i] for i in indices if 0 <= i < len(peer_list)]
                    except Exception:
                        print("Entrée invalide.")
                        continue
                msg = input("Message à envoyer en multicast : ")
                envoyer_message_multicast(destinataires, msg)
            elif choix == '6':
                if public_keys:
                    for ip, key in public_keys.items():
                        print(f"{ip} : {key}")
                else:
                    print("Aucune clé publique reçue.")
            elif choix == '7':
                peer_list = list(known_peers)
                if not peer_list:
                    print("Aucun pair disponible.")
                    continue
                print("Pairs disponibles :")
                for i, peer in enumerate(peer_list):
                    print(f"{i}. {peer}")
                selection = input("Entrez les indices des membres du groupe (ex: 0,1,2) ou 'tous' : ")
                if selection.lower() == 'tous':
                    membres = peer_list
                else:
                    try:
                        indices = [int(i.strip()) for i in selection.split(',')]
                        membres = [peer_list[i] for i in indices if 0 <= i < len(peer_list)]
                    except Exception:
                        print("Entrée invalide.")
                        continue
                nom = input("Nom du groupe : ").strip()
                if nom:
                    creer_groupe(nom, membres)
                else:
                    print("Nom de groupe invalide.")
            elif choix == '8':
                if not groupes:
                    print("Aucun groupe disponible.")
                    continue
                print("Groupes disponibles :")
                noms = list(groupes.keys())
                for i, nom in enumerate(noms):
                    print(f"{i}. {nom}")
                try:
                    idx = int(input("Choisissez un groupe : "))
                    if idx < 0 or idx >= len(noms):
                        print("Index invalide.")
                        continue
                    nom = noms[idx]
                    msg = input("Message à envoyer au groupe : ")
                    envoyer_message_dans_groupe(nom, msg)
                except Exception:
                    print("Entrée invalide.")
            elif choix == '9':
                stop_event.set()
                break
            else:
                print("Choix invalide.")
    except KeyboardInterrupt:
        stop_event.set()