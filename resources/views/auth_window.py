import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFrame
)
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt

import os
from resources.views.dashboard import Dashboard

# --- Couleurs de la charte graphique ---
COLOR_BG = "rgb(54, 65, 86)"  # fond principal
COLOR_CARD = "#F5F5F5"  # fond du formulaire
COLOR_ACCENT = "#D66853"  # boutons, cercles
COLOR_INPUT = "#E5D8D8"  # fond des champs
COLOR_INPUT_BORDER = "#7D4E57"  # bordure des champs
COLOR_TEXT = "#11151C"  # texte principal

# --- Interface d'authentification ---
class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Messagerie chiffrée - Authentification")
        self.setFixedSize(1000, 900)
        self.setStyleSheet(f"background-color: {COLOR_BG};")
        self.init_ui()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor(COLOR_ACCENT))

        # Cercles concentriques à gauche
        center_x_left = 0
        center_y_left = self.height() // 2
        for r in [20, 80, 140, 200]:
            painter.drawEllipse(center_x_left - r, center_y_left - r, 2*r, 2*r)

        # Cercles concentriques en bas à droite
        center_x_right = self.width()
        center_y_right = self.height()
        for r in [50, 120, 180, 240]:
            painter.drawEllipse(center_x_right - r, center_y_right - r, 2*r, 2*r)

    def init_ui(self):
        # Carte centrale
        card = QFrame(self)
        card.setStyleSheet(f"background: {COLOR_CARD}; border-radius: 16px;")
        card.setFixedSize(350, 380)
        card.move((self.width() - card.width()) // 2, (self.height() - card.height()) // 2)

        vbox = QVBoxLayout(card)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setSpacing(15)

        # Icône utilisateur (image user.png)
        icon_label = QLabel()
        user_icon_path = os.path.join("resources/img", "user.png")
        if os.path.exists(user_icon_path):
            icon_pix = QPixmap(user_icon_path)
            icon_pix = icon_pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pix)
        else:
            icon_label.setText("[user.png]")
        icon_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(icon_label)

        # Titre
        title = QLabel("Bienvenue sur votre messagerie chiffrée")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 16px; font-weight: 500;")
        vbox.addWidget(title)

        # Champ identifiant
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Identifiant")
        self.input_user.setStyleSheet(f"background: {COLOR_INPUT}; border: 2px solid {COLOR_INPUT_BORDER}; border-radius: 6px; padding: 8px; color: {COLOR_TEXT};")
        vbox.addWidget(self.input_user)

        # Champ mot de passe
        self.input_pwd = QLineEdit()
        self.input_pwd.setPlaceholderText("Mot de passe")
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.input_pwd.setStyleSheet(f"background: {COLOR_INPUT}; border: 2px solid {COLOR_INPUT_BORDER}; border-radius: 6px; padding: 8px; color: {COLOR_TEXT};")
        vbox.addWidget(self.input_pwd)

        vbox.addSpacing(15)  # 30 pixels d'espace, ajuste la valeur selon ton besoin

        # Bouton connexion avec icône log-in.png au-dessus du texte
        self.btn_login = QPushButton()
        self.btn_login.setFixedSize(200, 65)
        self.btn_login.setStyleSheet(f"background: {COLOR_ACCENT}; color: white; font-size: 15px; border-radius: 8px;")
        
        # Créer un layout vertical pour le bouton
        btn_layout = QVBoxLayout(self.btn_login)
        
        # Icône
        icon_label = QLabel()
        login_icon_path = os.path.join("resources/img", "log-in.png")
        if os.path.exists(login_icon_path):
            pixmap = QPixmap(login_icon_path)
            white_pixmap = QPixmap(pixmap.size())
            white_pixmap.fill(Qt.white)
            white_pixmap.setMask(pixmap.createMaskFromColor(Qt.transparent))
            icon_label.setPixmap(white_pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(icon_label)
        
        # Texte
        text_label = QLabel("Se connecter")
        text_label.setStyleSheet("color: white; font-size: 15px;")
        text_label.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(text_label)
        
        self.btn_login.clicked.connect(self.handle_login)
        vbox.addWidget(self.btn_login, alignment=Qt.AlignHCenter)

    def handle_login(self):
        user = self.input_user.text()
        pwd = self.input_pwd.text()
        try:
            if not user or not pwd:
                raise ValueError("Tous les champs sont obligatoires.")
            # Ici, on pourrait vérifier les identifiants
            print("avant ouverture du dashboard")
            self.dashboard = Dashboard()
            self.dashboard.show()
            self.close()
        except Exception as e:
                print("Erreur lors de l'ouverture du Dashboard :", e)