from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QLineEdit, QMainWindow, QScrollArea, QMessageBox
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont
import os
from app.network_manager import NetworkManager
from resources.views.settings_window import SettingsWindow

SERVICE_TYPE = "_securemsg._tcp.local."
SERVICE_PORT = 50001  # À adapter selon serveur TCP

class IconTextButton(QFrame):
    def __init__(self, icon_path, text, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #D66853;
                border-radius: 10px;
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
        text_label.setStyleSheet("color: white; font-size: 15px;")
        text_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(text_label)
        self.setCursor(Qt.PointingHandCursor)

class CircleIcon(QFrame):
    def __init__(self, icon_path, diameter=60, selected=False, parent=None):
        super().__init__(parent)
        self.diameter = diameter
        self.selected = selected
        self.icon_path = icon_path
        self.setFixedSize(diameter, diameter)
        self.update_style()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        icon_label.setPixmap(pixmap.scaled(diameter-20, diameter-20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

    def update_style(self):
        try:
            base = "#D66853"
            hover = "#b54a37"
            selected_color = "#a13e2a"
            color = selected_color if self.selected else base
            
            self.setStyleSheet(f"""
                QFrame {{
                    background: {color};
                    border: none;
                    border-radius: {self.diameter//2}px;
                }}
                QFrame:hover {{
                    background: {hover};
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

class ContactCell(QFrame):
    def __init__(self, nom, etat, initials, on_click=None, selected=False, parent=None):
        super().__init__(parent)
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
        
        text_vbox.addWidget(self.label_nom)
        self.label_etat = QLabel(etat)
        
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
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                margin-right: 2px;
            }}
            QFrame:hover {{
                background: #e0e0e0;
            }}
        """)
        
        # Style du cercle d'initiales
        self.circle.setStyleSheet(f"""
            QLabel {{
                background-color: #d8d8d8;
                color: #222;
                font-size: 20px;
                font-weight: bold;
                border-radius: 22px;
                border: 2px solid transparent;
            }}
        """)
        
        # Styles pour les autres widgets enfants pour s'assurer qu'ils n'héritent pas du fond
        self.label_nom.setStyleSheet("background: transparent; font-size: 17px; color: #222; font-weight: 500;")
        self.label_etat.setStyleSheet("background: transparent; color:#555;font-size:13px;")

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
                    self.left_layout.removeWidget(widget)
                    widget.deleteLater()
            except Exception as e:
                print(f"[DEBUG] Erreur lors de la suppression du widget: {e}")
        self.peripherique_widgets.clear()

        # Récupérer les pairs connus du NetworkManager
        known_peers = self.network_manager.get_known_peers()
        print(f"[DEBUG] Pairs connus: {known_peers}")
        
        for ip, peer_info in known_peers.items():
            print(f"[DEBUG] Affichage du pair: {ip} - {peer_info}")
            try:
                circle_icon = CircleIcon(
                    os.path.join("resources/img", "laptopblanc.png"),
                    diameter=60,
                    selected=(self.selected_peripherique and self.selected_peripherique.get('ip') == ip)
                )
                tooltip = f"Nom : {peer_info.get('nom', 'Inconnu')}\nIP : {ip}"
                circle_icon.setToolTip(tooltip)
                periph = {
                    'nom': peer_info.get('nom', 'Inconnu'),
                    'ip': ip,
                    'status': peer_info.get('status', 'online')
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
                self.selectionner_peripherique(periph, widget)
        except Exception as e:
            print(f"[DEBUG] Erreur lors du clic sur le périphérique: {e}")

    def selectionner_peripherique(self, periph, widget):
        """Sélectionne un périphérique et l'ajoute à la liste des conversations."""
        try:
            # Gérer la sélection visuelle sur la colonne de gauche
            if self.selected_widget and self.selected_widget != widget:
                try:
                    if self.selected_widget and not self.selected_widget.isHidden():
                        self.selected_widget.set_selected(False)
                except Exception as e:
                    print(f"[DEBUG] Erreur lors de la désélection du widget précédent: {e}")
            
            if widget and not widget.isHidden():
                widget.set_selected(True)
                self.selected_peripherique = periph
                self.selected_widget = widget

                # Ajouter le contact à la liste des conversations (colonne centrale)
                if not any(c['ip'] == periph['ip'] for c in self.conversations):
                    self.conversations.append(periph)
                    self.afficher_conversations()
            else:
                print(f"[DEBUG] Widget invalide ou caché, sélection annulée")
        except Exception as e:
            print(f"[DEBUG] Erreur lors de la sélection du périphérique: {e}")

    def ajouter_conversation(self):
        """Ouvre la fenêtre de chat pour la conversation sélectionnée dans la colonne centrale."""
        if self.selected_conversation:
            self.afficher_chat(self.selected_conversation)
        else:
            QMessageBox.information(self, "Aucune conversation sélectionnée", 
                                    "Veuillez d'abord sélectionner un contact dans la liste centrale.")

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
                on_click=lambda c=conv: self.selectionner_conversation(c)
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

    def selectionner_conversation(self, conv_data):
        """Met en mémoire la conversation sélectionnée et rafraîchit l'affichage."""
        # Créer un objet conversation avec le type, pour être compatible avec afficher_chat
        self.selected_conversation = {
            'type': 'contact',
            'name': conv_data.get('nom'),
            'ip': conv_data.get('ip')
        }
        # Rafraîchir l'affichage pour montrer la sélection
        self.afficher_conversations()

    def afficher_chat(self, conv):
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
        for icon_name in ["door-key.png", "bell.png"]:
            icon_path = os.path.join("resources/img", icon_name)
            if os.path.exists(icon_path):
                icon_label = QLabel()
                pixmap = QPixmap(icon_path)
                icon_label.setPixmap(pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                icon_label.setAlignment(Qt.AlignCenter)
                logos_layout.addWidget(icon_label)
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
            print(f"[DEBUG] Messages récupérés pour {conv['ip']}: {messages}")
            
            # Filtrer les messages pour ce contact (envoyés ET reçus)
            contact_messages = []
            for sender_ip, message_content in messages:
                # Messages envoyés par nous à ce contact
                if sender_ip == self.network_manager._get_local_ip() and conv['ip'] in self.network_manager.get_known_peers():
                    contact_messages.append(('sent', message_content))
                # Messages reçus de ce contact
                elif sender_ip == conv['ip']:
                    contact_messages.append(('received', message_content))
            
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