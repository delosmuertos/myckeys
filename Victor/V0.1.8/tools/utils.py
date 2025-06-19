import socket

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Google DNS, pas de données envoyées
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"