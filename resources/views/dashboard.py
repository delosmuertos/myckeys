from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QLineEdit, QMainWindow, QScrollArea, QMessageBox, QDialog, QTextEdit
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QFont
import os
from app.network_manager import NetworkManager
from resources.views.settings_window import SettingsWindow

SERVICE_TYPE = "_securemsg._tcp.local."
SERVICE_PORT = 50001  # À adapter selon serveur TCP

class CustomTooltip(QWidget):
    def __init__(self, name, ip, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Frame principal pour le style
        main_frame = QFrame(self)
        main_frame.setStyleSheet("""
            QFrame {
                background-color: #D66853;
                color: white;
                border-radius: 8px;
            }
            QLabel {
                color: white;
                background-color: transparent;
            }
        """)

        # Layout externe pour le widget
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(main_frame)

        # Layout pour le contenu dans le frame stylé
        content_layout = QVBoxLayout(main_frame)
        content_layout.setContentsMargins(15, 10, 15, 10)
        content_layout.setSpacing(6)

        # Label du nom
        name_label = QLabel(f"<b>{name}</b>")
        name_label.setStyleSheet("font-size: 16px;")
        content_layout.addWidget(name_label)

        # Layout des détails (icône + textes)
        details_layout = QHBoxLayout()
        details_layout.setSpacing(8)
        details_layout.setContentsMargins(0, 5, 0, 0)

        # Icône de cadenas
        icon_label = QLabel()
        icon_path = os.path.join("resources/img", "lockblanc.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            details_layout.addWidget(icon_label, alignment=Qt.AlignTop)

        # VBox pour les textes de détails
        text_details_layout = QVBoxLayout()
        text_details_layout.setSpacing(2)
        
        detected_label = QLabel("Détecté sur le réseau local")
        detected_label.setStyleSheet("font-size: 13px;")
        text_details_layout.addWidget(detected_label)
        
        ip_label = QLabel(f"IP : {ip}")
        ip_label.setStyleSheet("font-size: 13px;")
        text_details_layout.addWidget(ip_label)

        encryption_label = QLabel("Utilise le chiffrement AES-256")
        encryption_label.setStyleSheet("font-size: 13px;")
        text_details_layout.addWidget(encryption_label)

        details_layout.addLayout(text_details_layout)
        details_layout.addStretch()
        content_layout.addLayout(details_layout)

        self.adjustSize()

    def show_tooltip(self):
        # Vérifie si la souris est toujours sur le widget avant d'afficher
        if self.underMouse():
            if not self.custom_tooltip:
                peer_name = self.peer_info.get('nom', 'Inconnu')
                peer_ip = self.peer_info.get('ip', 'N/A')
                self.custom_tooltip = CustomTooltip(peer_name, peer_ip, parent=self.window())
                
                # Positionne le tooltip à droite de l'icône
                global_pos = self.mapToGlobal(self.rect().topRight())
                tooltip_pos = QPoint(global_pos.x() + 10, global_pos.y() + (self.height() - self.custom_tooltip.height()) // 2)
                
                self.custom_tooltip.move(tooltip_pos)
                self.custom_tooltip.show()

class IconTextButton(QFrame):
    def __init__(self, icon_path, text, parent=None):
        super().__init__(parent)
        self.setObjectName("iconTextButton")
        self.setStyleSheet("""
            QFrame#iconTextButton {
                background: #D66853;
                border-radius: 10px;
            }
            QFrame#iconTextButton:hover {
                background: #c55a47;
            }
            /* Applique un fond transparent à tous les QLabel enfants */
            QFrame#iconTextButton QLabel {
                background: transparent;
                color: white;
                font-size: 15px;
            }
        """)
        self.setMinimumSize(120, 70)
        self.setMaximumWidth(200) 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 7, 0, 7)
        layout.setSpacing(8)
        # Icône
        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        icon_label.setPixmap(pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(icon_label)
        # Texte
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(text_label)
        self.setCursor(Qt.PointingHandCursor)

class CircleIcon(QFrame):
    def __init__(self, icon_path, peer_info, diameter=60, selected=False, parent=None):
        super().__init__(parent)
        self.setObjectName("circleIcon")
        self.peer_info = peer_info
        self.diameter = diameter
        self.selected = selected
        self.icon_path = icon_path
        self.setFixedSize(diameter, diameter)
        self.setMouseTracking(True)
        self.custom_tooltip = None

        # Timer robuste pour gérer l'affichage du tooltip
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self.show_tooltip)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        icon_label = QLabel()
        icon_label.setObjectName("circleIconLabel")
        pixmap = QPixmap(icon_path)
        icon_label.setPixmap(pixmap.scaled(diameter-20, diameter-20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        
        self.update_style()

    def update_style(self):
        try:
            base = "#D66853"
            hover = "#b54a37"
            selected_color = "#a13e2a"
            color = selected_color if self.selected else base
            
            self.setStyleSheet(f"""
                QFrame#circleIcon {{
                    background: {color};
                    border: none;
                    border-radius: {self.diameter//2}px;
                }}
                QFrame#circleIcon:hover {{
                    background: {hover};
                }}
                QLabel#circleIconLabel {{
                    background: transparent;
                }}
            """)
        except Exception as e:
            print(f"[DEBUG] Erreur lors de la mise à jour du style: {e}")

    def set_selected(self, selected):
        try:
            self.selected = selected
            self.update_style()
        except Exception as e:
            print(f"[DEBUG] Erreur lors de la sélection: {e}")

    def enterEvent(self, event):
        # Démarre le timer au lieu d'appeler directement
        self.tooltip_timer.start(400)
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Arrête le timer et masque le tooltip
        self.tooltip_timer.stop()
        self.hide_tooltip()
        super().leaveEvent(event)
    
    def show_tooltip(self):
        # Vérifie si la souris est toujours sur le widget avant d'afficher
        if self.underMouse():
            if not self.custom_tooltip:
                peer_name = self.peer_info.get('nom', 'Inconnu')
                peer_ip = self.peer_info.get('ip', 'N/A')
                self.custom_tooltip = CustomTooltip(peer_name, peer_ip, parent=self.window())
                
                # Positionne le tooltip à droite de l'icône
                global_pos = self.mapToGlobal(self.rect().topRight())
                tooltip_pos = QPoint(global_pos.x() + 10, global_pos.y() + (self.height() - self.custom_tooltip.height()) // 2)
                
                self.custom_tooltip.move(tooltip_pos)
                self.custom_tooltip.show()
    
    def hide_tooltip(self):
        if self.custom_tooltip:
            self.custom_tooltip.close()
            self.custom_tooltip.deleteLater()
            self.custom_tooltip = None

class ContactCell(QFrame):
    def __init__(self, nom, etat, initials, on_click=None, selected=False, parent=None):
        super().__init__(parent)
        self.setObjectName("contactCell")
        self.selected = selected
        self.setFixedHeight(68)
        self.setMinimumWidth(320)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 0, 0)
        layout.setSpacing(18)
        
        # Cercle avec initiales
        self.circle = QLabel(initials)
        self.circle.setObjectName("initialsCircle")
        self.circle.setFixedSize(44, 44)
        self.circle.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.circle)

        # Bloc texte (nom, état)
        text_vbox = QVBoxLayout()
        self.label_nom = QLabel(nom)
        self.label_nom.setObjectName("contactName")
        text_vbox.addWidget(self.label_nom)
        
        self.label_etat = QLabel(etat)
        self.label_etat.setObjectName("contactStatus")
        text_vbox.addWidget(self.label_etat)
        
        layout.addLayout(text_vbox)
        layout.addStretch(1)
        
        if on_click:
            self.mousePressEvent = lambda event: on_click()
        
        self.update_style()

    def set_selected(self, selected):
        self.selected = selected
        self.update_style()

    def update_style(self):
        bg_color = "#e5e5e5" if self.selected else "#f1f1f1"
        hover_bg_color = "#e0e0e0"

        # Feuille de style unifiée pour tout le composant
        self.setStyleSheet(f"""
            QFrame#contactCell {{
                background-color: {bg_color};
                border: none;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                margin-right: 2px;
            }}
            QFrame#contactCell:hover {{
                background-color: {hover_bg_color};
            }}
            QLabel#initialsCircle {{
                background-color: #d8d8d8;
                color: #222;
                font-size: 20px;
                font-weight: bold;
                border-radius: 22px; /* La moitié de 44px pour un cercle parfait */
            }}
            QLabel#contactName {{
                background: transparent;
                font-size: 17px;
                color: #222;
                font-weight: 500;
            }}
            QLabel#contactStatus {{
                background: transparent;
                color: #555;
                font-size: 13px;
            }}
        """)

class PublicKeyWindow(QDialog):
    def __init__(self, peer_name, public_key, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Clé publique de {peer_name}")
        self.setModal(True)
        self.setStyleSheet("background-color: #F5F5F5;")
        self.setMinimumSize(900, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- BARRE SUPÉRIEURE ---
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #404349;")
        top_bar.setFixedHeight(60)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(18, 0, 18, 0)
        
        title_text = f"<span style='color:white;font-size:18px;font-weight:600;'>Clé publique de {peer_name}</span>"
        title_label = QLabel(title_text)
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch(1)
        main_layout.addWidget(top_bar)

        # --- CORPS DE LA FENÊTRE ---
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Colonne de navigation à gauche
        nav_col = QFrame()
        nav_col.setStyleSheet("background-color: #404349;")
        nav_col.setMinimumWidth(220)
        nav_col.setMaximumWidth(260)
        nav_layout = QVBoxLayout(nav_col)
        nav_layout.setContentsMargins(0, 30, 0, 30)
        nav_layout.setSpacing(18)
        
        btn_key_info = QPushButton("Clé Publique")
        btn_key_info.setStyleSheet("""
            QPushButton { background: #D66853; color: white; font-size: 16px; border-radius: 10px; padding: 12px 0; }
        """)
        nav_layout.addWidget(btn_key_info)
        nav_layout.addStretch(1)
        body_layout.addWidget(nav_col)

        # --- CONTENU ---
        content_area = QFrame()
        content_area.setStyleSheet("background-color: #ffffff;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(15)

        info_label = QLabel("Voici la clé publique RSA du contact. Vous pouvez la copier pour la vérifier.")
        info_label.setStyleSheet("font-size: 14px; background-color: transparent;")
        content_layout.addWidget(info_label)

        key_text_edit = QTextEdit()
        key_text_edit.setText(public_key)
        key_text_edit.setReadOnly(True)
        key_text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 13px;
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        content_layout.addWidget(key_text_edit)

        close_button = QPushButton("Fermer")
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #D66853;
                color: white;
                font-size: 15px;
                border-radius: 8px;
                padding: 10px 18px;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #c55a47; }
            QPushButton:pressed { background-color: #b54a37; }
        """)
        close_button.clicked.connect(self.accept)
        content_layout.addWidget(close_button, alignment=Qt.AlignRight)

        body_layout.addWidget(content_area, stretch=1)
        main_layout.addLayout(body_layout)

class Dashboard(QWidget):
    deconnexion_terminee = pyqtSignal()

    def __init__(self, username=None):
        super().__init__()
        self.username = username
        self.setWindowTitle("Dashboard")
        self.setStyleSheet("background-color: #F5F5F5;")
        self.setMinimumSize(1000, 600)

        # --- LOGIQUE RÉSEAU ---
        self.selected_peripherique = None
        self.selected_widget = None
        self.conversations = []  # Liste des contacts/conversations actifs
        self.selected_conversation = None
        self.network_manager = NetworkManager(username or "User")
        self._connect_network_signals()

        # --- INTERFACE GRAPHIQUE ---
        main_vlayout = QVBoxLayout(self)
        main_vlayout.setContentsMargins(0, 0, 0, 0)
        main_vlayout.setSpacing(0)

        # --- BARRE SUPÉRIEURE ---
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #404349;")
        top_bar.setFixedHeight(60)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(18, 0, 18, 0)
        top_bar_layout.setSpacing(0)
        
        # Texte utilisateur connecté
        user_label = QLabel()
        user_label.setStyleSheet("color: white; font-size: 15px; font-weight: 400;")
        if self.username:
            user_label.setText(f"Vous êtes connecté en tant que : <b>{self.username}</b>")
        else:
            user_label.setText("Vous êtes connecté en tant que : <b>Utilisateur</b>")
        user_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        top_bar_layout.addWidget(user_label)
        top_bar_layout.addStretch(1)

        # Bouton Effacement sécurisé
        btn_effacer = QPushButton("Effacement sécurisé")
        btn_effacer.setCursor(Qt.PointingHandCursor)
        btn_effacer.setStyleSheet("""
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
        icon_path = os.path.join("resources/img", "fireblanc.png")
        if os.path.exists(icon_path):
            btn_effacer.setIcon(QIcon(icon_path))
            btn_effacer.setIconSize(QSize(20, 20))
        btn_effacer.clicked.connect(self.effacement_securise)
        top_bar_layout.addWidget(btn_effacer)
        top_bar_layout.addSpacing(16)

        # Bouton Déconnexion
        btn_deco = QPushButton("Déconnexion")
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
        icon_path = os.path.join("resources/img", "logoutblanc.png")
        if os.path.exists(icon_path):
            btn_deco.setIcon(QIcon(icon_path))
            btn_deco.setIconSize(QSize(20, 20))

        btn_deco.clicked.connect(self.deconnexion)
        top_bar_layout.addWidget(btn_deco)
        top_bar_layout.addSpacing(8)
        main_vlayout.addWidget(top_bar)

        # --- CONTENU PRINCIPAL (colonne gauche + colonne centrale + colonne droite) ---
        main_hlayout = QHBoxLayout()
        main_hlayout.setContentsMargins(0, 0, 0, 0)
        main_hlayout.setSpacing(0)

        # Colonne gauche (boutons et périphériques)
        self.left_col = QFrame()
        self.left_col.setStyleSheet("background-color: #404349;")
        self.left_col.setMinimumWidth(180)
        self.left_col.setMaximumWidth(250)
        self.left_layout = QVBoxLayout(self.left_col)
        self.left_layout.setContentsMargins(0, 0, 0, 30)
        self.left_layout.setSpacing(15)

        # Boutons de la colonne gauche
        btn_nvc = IconTextButton(os.path.join("resources/img", "plusblanc.png"), "Nv conversation")
        self.left_layout.addWidget(btn_nvc, alignment=Qt.AlignHCenter)
        btn_nvc.mousePressEvent = lambda event: self.ajouter_conversation()

        btn_lan = IconTextButton(os.path.join("resources/img", "radarblanc.png"), "Recherche LAN")
        self.left_layout.addWidget(btn_lan, alignment=Qt.AlignHCenter)
        btn_lan.mousePressEvent = lambda event: self.rechercher_peripheriques()

        self.peripherique_widgets = []
        self.left_layout.addStretch(1)

        btn_settings = IconTextButton(os.path.join("resources/img", "settingblanc.png"), "Paramètres")
        btn_settings.mousePressEvent = lambda event: self.open_settings_window()
        self.left_layout.addWidget(btn_settings, alignment=Qt.AlignHCenter | Qt.AlignBottom)
        main_hlayout.addWidget(self.left_col)

        # Colonne centrale (liste des conversations)
        self.center_col = QFrame()
        self.center_col.setStyleSheet("background-color: #f1f1f1;")
        self.center_layout = QVBoxLayout(self.center_col)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)
        self.center_layout.setAlignment(Qt.AlignTop)
        main_hlayout.addWidget(self.center_col, stretch=1)

        # Colonne droite (zone de chat)
        self.chat_col = QFrame()
        self.chat_col.setStyleSheet("background-color: #fff;")
        self.chat_layout = QVBoxLayout(self.chat_col)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(0)
        main_hlayout.addWidget(self.chat_col, stretch=2)

        main_vlayout.addLayout(main_hlayout)

        # Timer pour refresh automatique
        self.timer_refresh = QTimer(self)
        self.timer_refresh.timeout.connect(self.rechercher_peripheriques)
        self.timer_refresh.start(30000)  # 30 secondes au lieu de 10 secondes

        # Démarrer les services réseau
        self.network_manager.start()
        self.rechercher_peripheriques()
        self.afficher_chat(None)

    def open_settings_window(self):
        """Ouvre la fenêtre des paramètres."""
        # On garde une référence à la fenêtre pour éviter qu'elle soit supprimée par le garbage collector
        self.settings_win = SettingsWindow()
        self.settings_win.show()

    # --- LOGIQUE RÉSEAU ---
    def _connect_network_signals(self):
        """Connecte les signaux du NetworkManager"""
        self.network_manager.peer_discovered.connect(self._on_peer_discovered)
        self.network_manager.peer_lost.connect(self._on_peer_lost)
        self.network_manager.message_received.connect(self._on_message_received)
        self.network_manager.group_message_received.connect(self._on_group_message_received)
        self.network_manager.log_message.connect(self._on_log_message)

    def _on_peer_discovered(self, ip: str, nom: str):
        """Callback quand un nouveau pair est découvert"""
        print(f"[DEBUG] DASHBOARD: _on_peer_discovered called for IP: {ip}, Name: {nom}")
        
        # Mettre à jour le statut s'il est déjà dans nos conversations
        peer_in_conversations = False
        for conv in self.conversations:
            if conv.get('ip') == ip:
                conv['status'] = 'online'
                peer_in_conversations = True
                print(f"[DEBUG] DASHBOARD: Found matching conversation for {ip}. Changing status to online.")
                break
        
        # Si le statut a changé, rafraîchir la liste des conversations
        if peer_in_conversations:
            QTimer.singleShot(100, self.afficher_conversations)

        # Toujours rafraîchir la liste des périphériques (colonne de gauche)
        self.rechercher_peripheriques()

    def _on_peer_lost(self, ip: str):
        """Callback quand un pair est perdu"""
        print(f"[DEBUG] DASHBOARD: _on_peer_lost called for IP: {ip}")

        # Mettre à jour le statut dans la liste des conversations (colonne centrale)
        peer_in_conversations = False
        for conv in self.conversations:
            if conv.get('ip') == ip:
                print(f"[DEBUG] DASHBOARD: Found matching conversation for {ip}. Changing status to offline.")
                conv['status'] = 'offline'
                peer_in_conversations = True
                break
        
        if not peer_in_conversations:
            print(f"[DEBUG] DASHBOARD: No matching conversation found for {ip} in self.conversations.")

        # Si le statut a changé, rafraîchir la vue
        if peer_in_conversations:
            print("[DEBUG] DASHBOARD: Refreshing conversations view due to peer loss.")
            QTimer.singleShot(100, self.afficher_conversations)

        # Rafraîchir la liste des périphériques (colonne de gauche) pour qu'il disparaisse
        self.rechercher_peripheriques()
        
        # Gérer la sélection si le pair perdu était sélectionné
        if self.selected_peripherique and self.selected_peripherique.get('ip') == ip:
            self.selected_peripherique = None
            self.selected_widget = None

    def _on_message_received(self, sender_ip: str, message: str):
        """Callback quand un message direct est reçu"""
        print(f"[DEBUG] Message reçu de {sender_ip}: {message}")
        # Rafraîchir l'affichage si la conversation actuelle correspond à l'expéditeur
        if (self.selected_conversation and 
            self.selected_conversation.get('type') == 'contact' and 
            self.selected_conversation.get('ip') == sender_ip):
            print(f"[DEBUG] Rafraîchissement de l'affichage du chat pour {sender_ip}")
            # Utiliser QTimer pour éviter les problèmes de thread
            QTimer.singleShot(100, lambda: self.afficher_chat(self.selected_conversation))
        else:
            print(f"[DEBUG] Message ignoré car conversation non sélectionnée ou différente")

    def _on_group_message_received(self, group_name: str, sender_ip: str, message: str):
        """Callback quand un message de groupe est reçu"""
        print(f"[DEBUG] Message de groupe reçu dans '{group_name}' de {sender_ip}: {message}")
        # Rafraîchir l'affichage si la conversation actuelle correspond au groupe
        if (self.selected_conversation and 
            self.selected_conversation.get('type') == 'group' and 
            self.selected_conversation.get('name') == group_name):
            print(f"[DEBUG] Rafraîchissement de l'affichage du chat de groupe pour {group_name}")
            # Utiliser QTimer pour éviter les problèmes de thread
            QTimer.singleShot(100, lambda: self.afficher_chat(self.selected_conversation))
        else:
            print(f"[DEBUG] Message de groupe ignoré car conversation non sélectionnée ou différente")

    def _on_log_message(self, log_entry: str):
        """Callback pour les messages de log"""
        print(f"[LOG] {log_entry}")

    def rechercher_peripheriques(self):
        """Rafraîchit l'affichage des périphériques"""
        print(f"[DEBUG] Recherche de périphériques...")
        
        # Nettoyer les widgets existants de manière sécurisée
        for widget in self.peripherique_widgets:
            try:
                if widget and not widget.isHidden():
                    # S'assurer de cacher le tooltip avant de supprimer le widget
                    widget.hide_tooltip()
                    self.left_layout.removeWidget(widget)
                    widget.deleteLater()
            except Exception as e:
                print(f"[DEBUG] Erreur lors de la suppression du widget: {e}")
        self.peripherique_widgets.clear()

        # Récupérer les pairs connus du NetworkManager
        known_peers = self.network_manager.get_known_peers()
        print(f"[DEBUG] Pairs connus: {known_peers}")
        
        for ip, peer_data in known_peers.items():
            print(f"[DEBUG] Affichage du pair: {ip} - {peer_data}")
            try:
                # On enrichit les informations du pair avec son IP pour le passer au widget
                peer_info_with_ip = peer_data.copy()
                peer_info_with_ip['ip'] = ip
                
                circle_icon = CircleIcon(
                    os.path.join("resources/img", "laptopblanc.png"),
                    peer_info_with_ip,
                    diameter=60,
                    selected=(self.selected_peripherique and self.selected_peripherique.get('ip') == ip)
                )
                # La gestion du tooltip est maintenant dans CircleIcon, plus besoin de setToolTip ici
                periph = {
                    'nom': peer_data.get('nom', 'Inconnu'),
                    'ip': ip,
                    'status': peer_data.get('status', 'online')
                }
                # Utiliser une méthode dédiée pour éviter les problèmes de lambda
                circle_icon.mousePressEvent = lambda event, p=periph, w=circle_icon: self._handle_peripheral_click(p, w)
                self.left_layout.insertWidget(2 + len(self.peripherique_widgets), circle_icon, alignment=Qt.AlignHCenter)
                self.peripherique_widgets.append(circle_icon)
            except Exception as e:
                print(f"[DEBUG] Erreur lors de la création du widget pour {ip}: {e}")
        print(f"[DEBUG] Nombre de widgets créés: {len(self.peripherique_widgets)}")

    def _handle_peripheral_click(self, periph, widget):
        """Gère le clic sur un périphérique de manière sécurisée"""
        try:
            if widget and not widget.isHidden():
                # Cacher le tooltip immédiatement lors du clic
                widget.hide_tooltip()
                self.selectionner_peripherique(periph, widget)
        except Exception as e:
            print(f"[DEBUG] Erreur lors du clic sur le périphérique: {e}")

    def selectionner_peripherique(self, periph, widget):
        """Sélectionne un périphérique et met à jour l'affichage visuel."""
        try:
            # Gérer la désélection visuelle de l'ancien widget
            if self.selected_widget and self.selected_widget != widget:
                try:
                    if self.selected_widget and not self.selected_widget.isHidden():
                        self.selected_widget.set_selected(False)
                except Exception as e:
                    print(f"[DEBUG] Erreur lors de la désélection du widget précédent: {e}")
            
            # Gérer la sélection du nouveau widget
            if widget and not widget.isHidden():
                widget.set_selected(True)
                self.selected_peripherique = periph
                self.selected_widget = widget
            else:
                print(f"[DEBUG] Widget invalide ou caché, sélection annulée")
        except Exception as e:
            print(f"[DEBUG] Erreur lors de la sélection du périphérique: {e}")

    def ajouter_conversation(self):
        """Ajoute le périphérique sélectionné à la liste des conversations sans ouvrir le chat."""
        if self.selected_peripherique:
            periph = self.selected_peripherique
            # Ajouter le contact à la liste des conversations s'il n'y est pas déjà
            if not any(c['ip'] == periph['ip'] for c in self.conversations):
                self.conversations.append(periph)
                # Rafraîchir l'affichage pour montrer le nouveau contact
                self.afficher_conversations()
        else:
            QMessageBox.information(self, "Aucun périphérique sélectionné", 
                                    "Veuillez d'abord sélectionner un périphérique dans la liste de gauche.")

    def afficher_conversations(self):
        # Nettoyer la colonne centrale
        for i in reversed(range(self.center_layout.count())):
            widget = self.center_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        print("[DEBUG] DASHBOARD: --- Refreshing conversations view ---")
        for c in self.conversations:
            print(f"  - Contact: {c.get('nom')}, IP: {c.get('ip')}, Status: {c.get('status')}")
        print("[DEBUG] DASHBOARD: ------------------------------------")

        # Afficher les conversations individuelles
        for conv in self.conversations:
            initials = ''.join([x[0] for x in conv['nom'].split()][:2]).upper()
            etat = conv.get('status', 'Connecté via réseau local')
            is_selected = self.selected_conversation and self.selected_conversation['ip'] == conv['ip']
            
            cell = ContactCell(
                conv['nom'], 
                f"AES-256 – {etat}", 
                initials,
                selected=is_selected,
                on_click=lambda c=conv: self.selectionner_et_afficher_chat(c)
            )
            self.center_layout.addWidget(cell)

        # Afficher les groupes
        groups = self.network_manager.get_groups()
        for group_name, group_info in groups.items():
            initials = 'G'
            cell = ContactCell(
                group_name,
                f"Groupe - {len(group_info.get('membres', []))} membres",
                initials,
                on_click=lambda g=group_name, gi=group_info: self.afficher_chat({'type': 'group', 'name': g, 'info': gi})
            )
            self.center_layout.addWidget(cell)

    def selectionner_et_afficher_chat(self, conv_data):
        """Sélectionne le contact et affiche directement la zone de chat."""
        self.selected_conversation = {
            'type': 'contact',
            'name': conv_data.get('nom'),
            'ip': conv_data.get('ip')
        }

        # S'assurer que l'échange de clés est fait avant d'afficher le chat
        if self.selected_conversation['type'] == 'contact':
            self.network_manager.ensure_key_exchange(self.selected_conversation['ip'])

        self.afficher_conversations()
        self.afficher_chat(self.selected_conversation)

    def afficher_chat(self, conv):
        # Sauvegarder le texte en cours de saisie s'il existe
        current_text = ""
        if hasattr(self, 'message_input') and self.message_input is not None:
            current_text = self.message_input.text()
        # Nettoyer la zone de chat
        for i in reversed(range(self.chat_layout.count())):
            widget = self.chat_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.selected_conversation = conv

        if conv is None:
            # Message d'accueil
            accueil = QLabel("<span style='color:#bbb;font-size:18px;'>Sélectionnez un contact pour commencer à discuter.</span>")
            accueil.setAlignment(Qt.AlignCenter)
            self.chat_layout.addWidget(accueil)
            return

        # En-tête du chat
        header = QFrame()
        header.setStyleSheet("background: #f5f5f5;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)
        header_layout.setSpacing(18)

        # Avatar/Initiales
        initials = 'G' if conv['type'] == 'group' else ''.join([x[0] for x in conv['name'].split()][:2]).upper()
        circle = QLabel(initials)
        circle.setFixedSize(44, 44)
        circle.setAlignment(Qt.AlignCenter)
        circle.setStyleSheet("background-color: #d3d3d3; color: #222; font-size: 20px; font-weight: bold; border-radius: 22px;")
        header_layout.addWidget(circle)

        # Nom et statut
        label_nom = QLabel(f"<b>{conv['name']}</b>")
        label_nom.setStyleSheet("font-size: 18px; color: #222;")
        header_layout.addWidget(label_nom)
        header_layout.addStretch(1)

        # Icônes de droite
        logos_layout = QHBoxLayout()
        logos_layout.setSpacing(12)
        logos_layout.setContentsMargins(0, 0, 0, 4) 
        
        # Icône de clé cliquable
        key_icon_path = os.path.join("resources/img", "door-key.png")
        if os.path.exists(key_icon_path):
            key_icon_label = QLabel()
            pixmap = QPixmap(key_icon_path)
            key_icon_label.setPixmap(pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            key_icon_label.setAlignment(Qt.AlignCenter)
            key_icon_label.setCursor(Qt.PointingHandCursor)
            if conv['type'] == 'contact':
                key_icon_label.mousePressEvent = lambda event, ip=conv['ip']: self._show_peer_public_key(ip)
            logos_layout.addWidget(key_icon_label)

        # Icône de cloche (non cliquable pour l'instant)
        bell_icon_path = os.path.join("resources/img", "bell.png")
        if os.path.exists(bell_icon_path):
            bell_icon_label = QLabel()
            pixmap = QPixmap(bell_icon_path)
            bell_icon_label.setPixmap(pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            bell_icon_label.setAlignment(Qt.AlignCenter)
            logos_layout.addWidget(bell_icon_label)
            
        header_layout.addLayout(logos_layout)
        self.chat_layout.addWidget(header)

        # Zone des messages
        messages_area = QScrollArea()
        messages_area.setWidgetResizable(True)
        messages_area.setStyleSheet("QScrollArea { border: none; background: white; }")
        messages_widget = QWidget()
        messages_layout = QVBoxLayout(messages_widget)
        messages_layout.setContentsMargins(24, 18, 24, 18)
        messages_layout.setSpacing(12)

        # Afficher les messages
        if conv['type'] == 'contact':
            messages = self.network_manager.get_messages()
            
            # Filtrer les messages pour cette conversation spécifique
            contact_messages = []
            my_ip = self.network_manager._get_local_ip()
            contact_ip = conv['ip']
            
            for msg_data in messages:
                # Gérer l'ancien et le nouveau format de message pour la compatibilité
                if len(msg_data) == 3:
                    sender_ip, recipient_ip, message_content = msg_data
                    # Message envoyé par moi à ce contact
                    if sender_ip == my_ip and recipient_ip == contact_ip:
                        contact_messages.append(('sent', message_content))
                    # Message reçu de ce contact par moi
                    elif sender_ip == contact_ip and recipient_ip == my_ip:
                        contact_messages.append(('received', message_content))
                elif len(msg_data) == 2:
                    # Logique de secours pour l'ancien format (peut être supprimée plus tard)
                    sender_ip, message_content = msg_data
                    if sender_ip == contact_ip:
                        contact_messages.append(('received', message_content))
                    elif sender_ip == my_ip: # Affiche tous les messages envoyés
                        contact_messages.append(('sent', message_content))

            
            print(f"[DEBUG] Messages filtrés pour {conv['ip']}: {contact_messages}")
            
            if not contact_messages:
                # Ajouter un message d'information
                info_label = QLabel("Aucun message dans cette conversation")
                info_label.setStyleSheet("color: #999; font-style: italic;")
                info_label.setAlignment(Qt.AlignCenter)
                messages_layout.addWidget(info_label)
            
            for msg_type, message_content in contact_messages:
                msg_widget = QFrame()
                
                # Style différent selon le type de message
                if msg_type == 'sent':
                    msg_widget.setStyleSheet("""
                        QFrame {
                            background: #D66853;
                            border-radius: 10px;
                            padding: 12px;
                            margin: 4px 0;
                        }
                    """)
                    sender_name = "Vous"
                    text_color = "white"
                else:  # received
                    msg_widget.setStyleSheet("""
                        QFrame {
                            background: #f8f9fa;
                            border-radius: 10px;
                            padding: 12px;
                            margin: 4px 0;
                        }
                    """)
                    sender_name = conv['name']
                    text_color = "#333"
                
                msg_layout = QVBoxLayout(msg_widget)
                msg_layout.setContentsMargins(12, 8, 12, 8)
                
                # En-tête du message avec le nom de l'expéditeur
                sender_label = QLabel(f"<b>{sender_name}</b>")
                sender_label.setStyleSheet(f"color: {text_color}; font-size: 13px;")
                msg_layout.addWidget(sender_label)
                
                # Contenu du message
                msg_content = QLabel(message_content)
                msg_content.setWordWrap(True)
                msg_content.setStyleSheet(f"color: {text_color}; font-size: 14px; margin-top: 4px;")
                msg_layout.addWidget(msg_content)
                
                messages_layout.addWidget(msg_widget)
                print(f"[DEBUG] Message ajouté au layout - Type: {msg_type}, De: {sender_name}, Message: {message_content}")
        else:  # groupe
            group_messages = self.network_manager.get_group_messages(conv['name'])
            print(f"[DEBUG] Messages de groupe récupérés pour {conv['name']}: {group_messages}")
            
            for sender_ip, message_content in group_messages:
                msg_widget = QFrame()
                msg_widget.setStyleSheet("""
                    QFrame {
                        background: #f8f9fa;
                        border-radius: 10px;
                        padding: 12px;
                        margin: 4px 0;
                    }
                """)
                msg_layout = QVBoxLayout(msg_widget)
                msg_layout.setContentsMargins(12, 8, 12, 8)
                
                # En-tête du message avec le nom de l'expéditeur
                sender_name = self.network_manager.get_known_peers().get(sender_ip, {}).get('nom', 'Inconnu')
                sender_label = QLabel(f"<b>{sender_name}</b>")
                sender_label.setStyleSheet("color: #666; font-size: 13px;")
                msg_layout.addWidget(sender_label)
                
                # Contenu du message
                msg_content = QLabel(message_content)
                msg_content.setWordWrap(True)
                msg_content.setStyleSheet("color: #333; font-size: 14px; margin-top: 4px;")
                msg_layout.addWidget(msg_content)
                
                messages_layout.addWidget(msg_widget)

        messages_layout.addStretch(1)
        messages_area.setWidget(messages_widget)
        self.chat_layout.addWidget(messages_area, stretch=1)

        # Correction finale : double scroll, puis forcer update et scroll à nouveau
        def scroll_to_last_message():
            count = messages_layout.count()
            if count > 1:
                last_msg_item = messages_layout.itemAt(count - 2)
                last_msg_widget = last_msg_item.widget()
                if last_msg_widget:
                    messages_area.ensureWidgetVisible(last_msg_widget)
            messages_area.verticalScrollBar().setValue(messages_area.verticalScrollBar().maximum())
            # Forcer un update puis rescroll après l'event loop
            def rescroll():
                messages_area.verticalScrollBar().setValue(messages_area.verticalScrollBar().maximum())
            QTimer.singleShot(50, rescroll)
        QTimer.singleShot(0, scroll_to_last_message)

        # Zone de saisie
        input_frame = QFrame()
        input_frame.setStyleSheet("background: #f5f5f5; border-top: 1px solid #d3d3d3;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(18, 10, 18, 10)
        input_layout.setSpacing(8)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Saisissez votre message…")
        self.message_input.setStyleSheet("""
            QLineEdit {
                font-size: 15px;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #ccc;
                background: white;
            }
        """)
        # Restaurer le texte précédemment saisi
        self.message_input.setText(current_text)
        self.message_input.returnPressed.connect(
            lambda: self.envoyer_message_groupe(conv['name']) if conv['type'] == 'group' 
            else self.envoyer_message(conv['ip'])
        )
        input_layout.addWidget(self.message_input)

        send_btn = QPushButton()
        send_btn.setIcon(QIcon(os.path.join("resources/img", "plane.png")))
        send_btn.setFixedSize(40, 40)
        send_btn.setIconSize(QSize(22, 22))
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #D66853;
                border-radius: 20px;
                padding: 0px;
            }
            QPushButton:hover { background: #c55a47; }
        """)
        send_btn.clicked.connect(
            lambda: self.envoyer_message_groupe(conv['name']) if conv['type'] == 'group'
            else self.envoyer_message(conv['ip'])
        )
        input_layout.addWidget(send_btn)

        self.chat_layout.addWidget(input_frame)

    def envoyer_message(self, target_ip: str):
        """Envoie un message à un contact"""
        try:
            if hasattr(self, 'message_input') and self.message_input.text().strip():
                message = self.message_input.text().strip()
                success = self.network_manager.send_message(target_ip, message)
                if success:
                    self.message_input.clear()
                    # Rafraîchir l'affichage après un court délai pour laisser le temps au message d'être traité
                    QTimer.singleShot(100, lambda: self.afficher_chat(self.selected_conversation))
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible d'envoyer le message")
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'envoi du message: {str(e)}")
            QMessageBox.warning(self, "Erreur", f"Une erreur est survenue lors de l'envoi du message: {str(e)}")

    def envoyer_message_groupe(self, group_name: str):
        """Envoie un message à un groupe"""
        try:
            if hasattr(self, 'message_input') and self.message_input.text().strip():
                message = self.message_input.text().strip()
                success = self.network_manager.send_group_message(group_name, message)
                if success:
                    self.message_input.clear()
                    # Rafraîchir l'affichage après un court délai pour laisser le temps au message d'être traité
                    QTimer.singleShot(100, lambda: self.afficher_chat(self.selected_conversation))
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible d'envoyer le message de groupe")
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'envoi du message de groupe: {str(e)}")
            QMessageBox.warning(self, "Erreur", f"Une erreur est survenue lors de l'envoi du message de groupe: {str(e)}")

    def _show_peer_public_key(self, ip: str):
        """Affiche la clé publique du pair dans une boîte de dialogue."""
        public_key = self.network_manager.get_peer_public_key(ip)
        
        if public_key:
            # Remplacer QMessageBox par notre nouvelle fenêtre
            key_window = PublicKeyWindow(
                self.selected_conversation['name'], 
                public_key, 
                self
            )
            key_window.exec_()
        else:
            QMessageBox.warning(self, "Clé non trouvée", "Impossible de récupérer la clé publique pour ce contact.")

    def effacement_securise(self):
        reply = QMessageBox.question(
            self, "Effacement sécurisé",
            "Voulez-vous vraiment effacer tous les messages et logs ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Effacer les messages dans le NetworkManager
            self.network_manager.clear_messages()
            
            # Rafraîchir l'affichage si une conversation est sélectionnée
            if self.selected_conversation:
                print(f"[DEBUG] Rafraîchissement de l'affichage après effacement sécurisé")
                self.afficher_chat(self.selected_conversation)
            else:
                # Si aucune conversation n'est sélectionnée, afficher le message d'accueil
                self.afficher_chat(None)
            
            QMessageBox.information(self, "Info", "Effacement sécurisé effectué")

    def deconnexion(self):
        reply = QMessageBox.question(
            self, 'Déconnexion',
            "Êtes-vous sûr de vouloir vous déconnecter et quitter ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.network_manager.stop()
            self.close()
            self.deconnexion_terminee.emit()

    def afficher_fenetre_auth(self):
        from resources.views.auth_window import AuthWindow
        self.auth_window = AuthWindow()
        self.auth_window.show()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Confirmation',
            "Êtes-vous sûr de vouloir quitter ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()