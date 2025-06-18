# État global partagé entre tous les modules

# tools/config.py
BROADCAST_PORT   = 50000
TCP_PORT         = 50001
BROADCAST_INTERVAL = 5          # secondes
BUFFER_SIZE      = 1024

ma_cle_publique = ""

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
