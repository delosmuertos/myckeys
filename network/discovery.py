import socket
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser
import threading
from PyQt5.QtCore import QThread, pyqtSignal

SERVICE_TYPE = "_securemsg._tcp.local."
SERVICE_PORT = 50001  # À adapter selon serveur TCP

class MyListener:
    def __init__(self):
        self.peripheriques = {}

    def remove_service(self, zeroconf, type, name):
        if name in self.peripheriques:
            del self.peripheriques[name]

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            ip = socket.inet_ntoa(info.addresses[0])
            nom = name.split("._")[0]
            self.peripheriques[name] = {"nom": nom, "ip": ip}

    def update_service(self, zeroconf, type, name):
        pass

def annoncer_service():
    zeroconf = Zeroconf()
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    info = ServiceInfo(
        SERVICE_TYPE,
        f"{hostname}._securemsg._tcp.local.",
        addresses=[socket.inet_aton(ip)],
        port=SERVICE_PORT,
        properties={b"nom": hostname.encode()},
        server=f"{hostname}.local.",
    )
    zeroconf.register_service(info)
    return zeroconf, info

class DecouverteThread(QThread):
    peripheriques_trouves = pyqtSignal(list)

    def run(self):
        peripheriques = self.decouverte_reseau(timeout=2)
        self.peripheriques_trouves.emit(peripheriques)

    def decouverte_reseau(self, timeout=2):
        zeroconf = Zeroconf()
        listener = MyListener()
        browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)
        threading.Event().wait(timeout)
        zeroconf.close()
        return list(listener.peripheriques.values()) 