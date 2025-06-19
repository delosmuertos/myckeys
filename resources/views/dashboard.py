from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QLineEdit, QMainWindow, QScrollArea, QMessageBox
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont
import os
import socket
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser
import threading
from network.discovery import MyListener, annoncer_service, DecouverteThread
from network.disconnect import DisconnectManager
import logging
from app.network_manager import NetworkManager

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
        base = "#D66853"
        hover = "#b54a37"
        selected = "#a13e2a"
        color = selected if self.selected else base
        self.setStyleSheet(f"""
            QFrame {{
                background: {color};
                border-radius: {self.diameter//2}px;
            }}
            QFrame:hover {{
                background: {hover};
            }}
        """)

    def set_selected(self, selected):
        self.selected = selected
        self.update_style()

class ContactCell(QFrame):
    def __init__(self, nom, etat, initials, on_click=None, selected=False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(68)
        self.setMinimumWidth(320)
        self.setStyleSheet(f"""
            QFrame {{
                background: #f1f1f1;
                border: none;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 0, 0)
        layout.setSpacing(18)
        # Cercle avec initiales
        circle = QLabel(initials)
        circle.setFixedSize(44, 44)
        circle.setAlignment(Qt.AlignCenter)
        circle.setStyleSheet("""
            background-color: #d8d8d8;
            color: #222;
            font-size: 20px;
            font-weight: bold;
            border-radius: 22px;
        """)
        layout.addWidget(circle)
        # Bloc texte (nom, état)
        text_vbox = QVBoxLayout()
        label_nom = QLabel(nom)
        label_nom.setStyleSheet("font-size: 17px; color: #222; font-weight: 500;")
        text_vbox.addWidget(label_nom)
        label_etat = QLabel(etat)
        label_etat.setStyleSheet("color:#555;font-size:13px;")
        text_vbox.addWidget(label_etat)
        layout.addLayout(text_vbox)
        layout.addStretch(1)
        if on_click:
            self.mousePressEvent = lambda event: on_click()

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
        self.disconnect_manager = DisconnectManager(self)
        btn_deco = self.disconnect_manager.creer_bouton_deconnexion(self)
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
        self.timer_refresh.start(10000)  # 10 secondes au lieu de 5 minutes

        # Démarrer les services réseau
        self.network_manager.start()
        self.rechercher_peripheriques()
        self.afficher_chat(None)

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
        print(f"[DEBUG] Nouveau pair découvert: {nom} ({ip})")
        self.rechercher_peripheriques()

    def _on_peer_lost(self, ip: str):
        """Callback quand un pair est perdu"""
        print(f"[DEBUG] Pair perdu: {ip}")
        self.rechercher_peripheriques()
        if self.selected_peripherique and self.selected_peripherique.get('ip') == ip:
            self.selected_peripherique = None
            self.selected_widget = None
        self.afficher_chat(None)  

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
        
        # Nettoyer les widgets existants
        for widget in self.peripherique_widgets:
            self.left_layout.removeWidget(widget)
            widget.deleteLater()
        self.peripherique_widgets.clear()

        # Récupérer les pairs connus du NetworkManager
        known_peers = self.network_manager.get_known_peers()
        print(f"[DEBUG] Pairs connus: {known_peers}")
        
        for ip, peer_info in known_peers.items():
            print(f"[DEBUG] Affichage du pair: {ip} - {peer_info}")
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
            circle_icon.mousePressEvent = lambda event, p=periph, w=circle_icon: self.selectionner_peripherique(p, w)
            self.left_layout.insertWidget(2 + len(self.peripherique_widgets), circle_icon, alignment=Qt.AlignHCenter)
            self.peripherique_widgets.append(circle_icon)
        
        print(f"[DEBUG] Nombre de widgets créés: {len(self.peripherique_widgets)}")

    def selectionner_peripherique(self, periph, widget):
        """Sélectionne un périphérique et affiche sa conversation"""
        if self.selected_widget:
            self.selected_widget.set_selected(False)
        widget.set_selected(True)
        self.selected_peripherique = periph
        self.selected_widget = widget
        
        # Créer l'objet conversation et afficher le chat
        conversation = {
            'type': 'contact', 
            'name': periph['nom'], 
            'ip': periph['ip']
        }
        self.afficher_chat(conversation)

    def ajouter_conversation(self):
        if self.selected_peripherique and self.selected_peripherique not in self.conversations:
            self.conversations.append(self.selected_peripherique)
            self.afficher_conversations()

    def afficher_conversations(self):
        # Nettoyer la colonne centrale
        for i in reversed(range(self.center_layout.count())):
            widget = self.center_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Afficher les conversations individuelles
        for conv in self.conversations:
            initials = ''.join([x[0] for x in conv['nom'].split()][:2]).upper()
            etat = conv.get('status', 'Connecté via réseau local')
            cell = ContactCell(
                conv['nom'], 
                f"AES-256 – {etat}", 
                initials,
                on_click=lambda c=conv: self.afficher_chat({'type': 'contact', 'name': c['nom'], 'ip': c['ip']})
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
            
            # Filtrer les messages pour ce contact
            contact_messages = [msg for msg in messages if msg[0] == conv['ip']]
            print(f"[DEBUG] Messages filtrés pour {conv['ip']}: {contact_messages}")
            
            for sender_ip, message_content in contact_messages:
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
        send_btn.setIcon(QIcon(os.path.join("resources/img", "send.png")))
        send_btn.setIconSize(QSize(24, 24))
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #D66853;
                border-radius: 6px;
                padding: 8px;
                min-width: 40px;
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
            self.network_manager.clear_messages()
            QMessageBox.information(self, "Info", "Effacement sécurisé effectué")

    def deconnexion(self):
        if self.disconnect_manager.deconnexion_complete(
            zeroconf=None,
            service_info=None,
            threads=None
        ):
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