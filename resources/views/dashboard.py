from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
import os
import socket
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser
import threading
from network.discovery import MyListener, annoncer_service, DecouverteThread

SERVICE_TYPE = "_securemsg._tcp.local."
SERVICE_PORT = 50001  # À adapter selon serveur TCP
# ca marche bien
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
    def __init__(self, username=None):
        super().__init__()
        self.username = username
        self.setWindowTitle("Dashboard")
        self.setStyleSheet("background-color: #F5F5F5;")
        self.setMinimumSize(1000, 600)

        self.selected_peripherique = None
        self.selected_widget = None
        self.conversations = []  # Liste des contacts/conversations actifs
        self.selected_conversation = None

        # Annonce le service zeroconf au lancement
        self.zeroconf, self.service_info = annoncer_service()

        # Layout principal vertical (barre du haut + contenu)
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
        # Texte à gauche : utilisateur connecté
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

        # Espace entre les deux boutons
        top_bar_layout.addSpacing(16)

        # Bouton Déconnexion
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
        icon_path = os.path.join("resources/img", "logoutblanc.png")
        if os.path.exists(icon_path):
            btn_deco.setIcon(QIcon(icon_path))
            btn_deco.setIconSize(QSize(20, 20))
        btn_deco.clicked.connect(self.deconnexion)
        top_bar_layout.addWidget(btn_deco)
        top_bar_layout.addSpacing(8)
        main_vlayout.addWidget(top_bar)

        # --- CONTENU PRINCIPAL (colonne gauche + colonne centrale) ---
        main_hlayout = QHBoxLayout()
        main_hlayout.setContentsMargins(0, 0, 0, 0)
        main_hlayout.setSpacing(0)

        self.left_col = QFrame()
        self.left_col.setStyleSheet("background-color: #404349;")
        self.left_col.setMinimumWidth(180)
        self.left_col.setMaximumWidth(250)
        self.left_layout = QVBoxLayout(self.left_col)
        self.left_layout.setContentsMargins(0, 0, 0, 30)
        self.left_layout.setSpacing(15)

        btn_nvc = IconTextButton(os.path.join("resources/img", "plusblanc.png"), "Nv conversation")
        self.left_layout.addWidget(btn_nvc, alignment=Qt.AlignHCenter)

        btn_lan = IconTextButton(os.path.join("resources/img", "radarblanc.png"), "Recherche LAN")
        self.left_layout.addWidget(btn_lan, alignment=Qt.AlignHCenter)
        btn_lan.mousePressEvent = lambda event: self.rechercher_peripheriques()
        btn_nvc.mousePressEvent = lambda event: self.ajouter_conversation()

        self.peripherique_widgets = []
        self.left_layout.addStretch(1)
        btn_settings = IconTextButton(os.path.join("resources/img", "settingblanc.png"), "Paramètres")
        self.left_layout.addWidget(btn_settings, alignment=Qt.AlignHCenter | Qt.AlignBottom)
        main_hlayout.addWidget(self.left_col)
        # Colonne centrale pour les conversations
        self.center_col = QFrame()
        self.center_col.setStyleSheet("background-color: #f1f1f1;")
        self.center_layout = QVBoxLayout(self.center_col)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)
        main_hlayout.addWidget(self.center_col, stretch=1)
        # Zone de discussion à droite
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
        self.timer_refresh.start(300000)  # 5 minutes en ms
        self.rechercher_peripheriques()  # Premier scan au lancement
        self.afficher_chat(None)  

    def rechercher_peripheriques(self):
        for widget in self.peripherique_widgets:
            self.left_layout.removeWidget(widget)
            widget.deleteLater()
        self.peripherique_widgets.clear()
        self.selected_peripherique = None
        self.selected_widget = None
        self.thread = DecouverteThread()
        self.thread.peripheriques_trouves.connect(self.afficher_peripheriques)
        self.thread.start()

    def afficher_peripheriques(self, peripheriques):
        for widget in self.peripherique_widgets:
            self.left_layout.removeWidget(widget)
            widget.deleteLater()
        self.peripherique_widgets.clear()
        for periph in peripheriques:
            is_selected = (self.selected_peripherique is not None and periph == self.selected_peripherique)
            circle_icon = CircleIcon(os.path.join("resources/img", "laptopblanc.png"), diameter=60, selected=is_selected)
            tooltip = f"Nom : {periph['nom']}\nIP : {periph['ip']}"
            circle_icon.setToolTip(tooltip)
            # Rendre cliquable et sélectionnable
            circle_icon.mousePressEvent = lambda event, p=periph, w=circle_icon: self.selectionner_peripherique(p, w)
            self.left_layout.insertWidget(2 + len(self.peripherique_widgets), circle_icon, alignment=Qt.AlignHCenter)
            self.peripherique_widgets.append(circle_icon)

    def selectionner_peripherique(self, periph, widget):
        # Désélectionner l'ancien
        if self.selected_widget:
            self.selected_widget.set_selected(False)
        # Sélectionner le nouveau
        widget.set_selected(True)
        self.selected_peripherique = periph
        self.selected_widget = widget

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
        # Affichage des cellules des contacts
        for idx, conv in enumerate(self.conversations):
            initials = ''.join([x[0] for x in conv['nom'].split()][:2]).upper()
            etat = conv.get('etat', 'Connecté via réseau local')
            is_selected = (conv == self.selected_conversation)
            cell = ContactCell(conv['nom'], f"AES-256 – {etat}", initials, on_click=lambda c=conv: self.afficher_chat(c), selected=is_selected)
            self.center_layout.addWidget(cell)
            if idx < len(self.conversations) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setFrameShadow(QFrame.Plain)
                sep.setStyleSheet("color: #d3d3d3; background: #d3d3d3;")
                sep.setFixedHeight(1)
                sep.setContentsMargins(0, 0, 0, 0)
                self.center_layout.addWidget(sep)

    def afficher_chat(self, conv):
        # Nettoyer la zone de chat
        for i in reversed(range(self.chat_layout.count())):
            widget = self.chat_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.selected_conversation = conv
        self.afficher_conversations()  # Pour mettre à jour la sélection visuelle
        if conv is None:
            # Afficher un message d'accueil
            accueil = QLabel("<span style='color:#bbb;font-size:18px;'>Sélectionnez un contact pour commencer à discuter.</span>")
            accueil.setAlignment(Qt.AlignCenter)
            self.chat_layout.addWidget(accueil)
        else:
            # En-tête du contact
            header = QFrame()
            header.setStyleSheet("background: #f5f5f5;")
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(24, 12, 24, 12)
            header_layout.setSpacing(18)
            initials = ''.join([x[0] for x in conv['nom'].split()][:2]).upper()
            circle = QLabel(initials)
            circle.setFixedSize(44, 44)
            circle.setAlignment(Qt.AlignCenter)
            circle.setStyleSheet("background-color: #d3d3d3; color: #222; font-size: 20px; font-weight: bold; border-radius: 22px;")
            header_layout.addWidget(circle)
            label_nom = QLabel(f"<b>{conv['nom']}</b>")
            label_nom.setStyleSheet("font-size: 18px; color: #222;")
            header_layout.addWidget(label_nom)
            header_layout.addStretch(1)
            # Logos à droite
            logos_layout = QHBoxLayout()
            logos_layout.setSpacing(12)  # Espacement horizontal entre les logos
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
            # Zone centrale pour les messages
            messages_area = QFrame()
            messages_area.setStyleSheet("background: #fff;")
            messages_layout = QVBoxLayout(messages_area)
            messages_layout.setContentsMargins(24, 18, 24, 18)
            messages_layout.addStretch(1)
            self.chat_layout.addWidget(messages_area, stretch=1)
            # Barre de saisie en bas
            input_frame = QFrame()
            input_frame.setStyleSheet("background: #f5f5f5; border-top: 1px solid #d3d3d3;")
            input_layout = QHBoxLayout(input_frame)
            input_layout.setContentsMargins(18, 10, 18, 10)
            input_layout.setSpacing(8)
            input_text = QLineEdit()
            input_text.setPlaceholderText("Saisissez votre message…")
            input_text.setStyleSheet("font-size: 15px; padding: 8px; border-radius: 6px; border: 1px solid #ccc; background: #fff;")
            input_layout.addWidget(input_text, stretch=1)
            
            send_icon_path = os.path.join("resources/img", "send.png")
            send_btn = QLabel()
            if os.path.exists(send_icon_path):
                send_pix = QPixmap(send_icon_path)
                send_btn.setPixmap(send_pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            send_btn.setCursor(Qt.PointingHandCursor)
            input_layout.addWidget(send_btn)
            self.chat_layout.addWidget(input_frame)

    def effacement_securise(self):
        # TODO: Implémenter la logique d'effacement sécurisé (logs, messages, mémoire, etc.)
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Effacement sécurisé", "Fonction d'effacement sécurisé à implémenter.")

    def deconnexion(self):
        # Arrêter les threads réseau, nettoyer la mémoire
        try:
            if hasattr(self, 'thread') and self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
            if hasattr(self, 'zeroconf'):
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
            # Nettoyage mémoire supplémentaire si besoin
        except Exception as e:
            print("Erreur lors du nettoyage à la déconnexion :", e)
        # Retour à la fenêtre d'authentification
        from resources.views.auth_window import AuthWindow
        self.close()
        self.auth_window = AuthWindow()
        self.auth_window.show() 