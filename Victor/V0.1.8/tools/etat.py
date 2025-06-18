# État global partagé entre tous les modules

# Liste des pairs détectés sur le réseau
known_peers = set()

# Messages directs reçus
messages = []

# Logs de debug/info/erreur
logs = []

# Dictionnaire IP → clé publique
public_keys = {}

# Groupes connus localement (nom → {membres, messages})
groupes = {}

# Stopper proprement les threads (broadcast, TCP)
import threading
stop_event = threading.Event()
