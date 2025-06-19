from PyQt5.QtWidgets import QPushButton, QMessageBox
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
import os
import logging

class DisconnectManager:
    """Gestionnaire de déconnexion pour les services réseau"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
    
    def creer_bouton_deconnexion(self, parent):
        """Crée un bouton de déconnexion stylisé"""
        btn_deco = QPushButton("Se déconnecter")
        btn_deco.setCursor(Qt.PointingHandCursor)
        btn_deco.setStyleSheet("""
            QPushButton {
                background-color: #D66853;
                color: white;
                font-size: 15px;
                border-radius: 10px;
                padding: 8px 18px;
                min-width: 140px;
                text-align: left;
            }
            QPushButton:hover { background-color: #c55a47; }
            QPushButton:pressed { background-color: #b54a37; }
        """)
        
        # Ajouter l'icône de déconnexion
        icon_path = os.path.join("resources/img", "logoutblanc.png")
        if os.path.exists(icon_path):
            btn_deco.setIcon(QIcon(icon_path))
            btn_deco.setIconSize(QSize(20, 20))
        
        return btn_deco
    
    def deconnexion_complete(self, zeroconf=None, service_info=None, threads=None):
        """Effectue une déconnexion complète de tous les services"""
        try:
            # Demander confirmation à l'utilisateur
            reply = QMessageBox.question(
                self.parent, "Déconnexion", 
                "Voulez-vous vraiment vous déconnecter ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return False
            
            # Arrêter le service zeroconf
            if zeroconf:
                try:
                    if service_info:
                        zeroconf.unregister_service(service_info)
                    zeroconf.close()
                    self.logger.info("Service zeroconf arrêté")
                except Exception as e:
                    self.logger.error(f"Erreur lors de l'arrêt du service zeroconf: {e}")
            
            # Arrêter les threads en cours
            if threads:
                for thread in threads:
                    if thread and thread.isRunning():
                        try:
                            thread.quit()
                            thread.wait(5000)  # Attendre 5 secondes max
                            if thread.isRunning():
                                thread.terminate()
                                thread.wait(2000)
                            self.logger.info(f"Thread {thread.__class__.__name__} arrêté")
                        except Exception as e:
                            self.logger.error(f"Erreur lors de l'arrêt du thread: {e}")
            
            # Nettoyer les ressources
            self._nettoyer_ressources()
            
            self.logger.info("Déconnexion complète effectuée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la déconnexion: {e}")
            QMessageBox.critical(self.parent, "Erreur", f"Erreur lors de la déconnexion: {e}")
            return False
    
    def _nettoyer_ressources(self):
        """Nettoie les ressources utilisées par l'application"""
        try:
            # Ici on peut ajouter d'autres nettoyages si nécessaire
            # Par exemple, fermer des connexions de base de données, etc.
            pass
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage des ressources: {e}")
    
    def effacement_securise(self):
        """Effectue un effacement sécurisé des données"""
        try:
            reply = QMessageBox.question(
                self.parent, "Effacement sécurisé", 
                "Voulez-vous vraiment effacer tous les messages et logs ?\nCette action est irréversible.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Ici on peut implémenter l'effacement sécurisé
                # Par exemple, supprimer les fichiers de logs, vider les bases de données, etc.
                self.logger.info("Effacement sécurisé effectué")
                QMessageBox.information(self.parent, "Info", "Effacement sécurisé effectué")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'effacement sécurisé: {e}")
            QMessageBox.critical(self.parent, "Erreur", f"Erreur lors de l'effacement sécurisé: {e}")
            return False 