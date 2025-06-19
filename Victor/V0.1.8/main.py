# main.py
from tools.cle_publique import charger_cle_publique
from tools.decouverte import broadcast_presence, listen_for_peers
from tools.tcp_serveur import start_tcp_server
from tools.menu import afficher_menu
from tools.etat import stop_event
import threading

def main():
    charger_cle_publique()

    # Lancement des threads réseau
    threading.Thread(target=broadcast_presence, daemon=True).start()
    threading.Thread(target=listen_for_peers, daemon=True).start()
    threading.Thread(target=start_tcp_server, daemon=True).start()

    # Menu interactif
    afficher_menu()

if __name__ == "__main__":
    main()
