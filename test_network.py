#!/usr/bin/env python3
"""
Script de test pour vérifier la communication UDP entre deux machines
"""
import socket
import json
import time
import threading

BROADCAST_PORT = 50000

def test_broadcast(username):
    """Teste l'envoi de broadcasts"""
    print(f"[TEST] Démarrage du test broadcast pour {username}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        for i in range(5):  # Envoyer 5 broadcasts
            message = {
                "type": "TEST_BROADCAST",
                "username": username,
                "sequence": i
            }
            try:
                s.sendto(json.dumps(message).encode(), ('<broadcast>', BROADCAST_PORT))
                print(f"[TEST] Broadcast {i} envoyé: {message}")
            except Exception as e:
                print(f"[TEST] Erreur broadcast: {e}")
            time.sleep(2)

def test_listen():
    """Teste l'écoute des broadcasts"""
    print(f"[TEST] Démarrage du test d'écoute sur le port {BROADCAST_PORT}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', BROADCAST_PORT))
        s.settimeout(15)  # Timeout de 15 secondes
        
        try:
            while True:
                try:
                    data, addr = s.recvfrom(1024)
                    message = json.loads(data.decode())
                    print(f"[TEST] Message reçu de {addr}: {message}")
                except socket.timeout:
                    print("[TEST] Timeout - Aucun message reçu")
                    break
                except Exception as e:
                    print(f"[TEST] Erreur réception: {e}")
        except KeyboardInterrupt:
            print("[TEST] Arrêt du test d'écoute")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_network.py broadcast <username>  # Pour tester l'envoi")
        print("  python test_network.py listen                # Pour tester l'écoute")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode == "broadcast":
        if len(sys.argv) < 3:
            print("Erreur: nom d'utilisateur requis pour le mode broadcast")
            sys.exit(1)
        username = sys.argv[2]
        test_broadcast(username)
    elif mode == "listen":
        test_listen()
    else:
        print("Mode invalide. Utilisez 'broadcast' ou 'listen'")
        sys.exit(1) 