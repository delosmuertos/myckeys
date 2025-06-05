import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFrame, QMessageBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt
from passlib.context import CryptContext
from database.db import SessionLocal
from database.models import User

import os
from resources.views.dashboard import Dashboard

# --- Couleurs de la charte graphique ---
COLOR_BG = "#404349"  # fond principal
COLOR_CARD = "#F5F5F5"  # fond du formulaire
COLOR_ACCENT = "#D66853"  # boutons, cercles
COLOR_INPUT = "#E5D8D8"  # fond des champs
COLOR_INPUT_BORDER = "#7D4E57"  # bordure des champs
COLOR_TEXT = "#11151C"  # texte principal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Interface d'authentification ---
class AuthWindow(QWidget):
    """
    Fenêtre d'authentification de l'application.
    
    Cette classe gère l'interface utilisateur et la logique d'authentification.
    Elle permet aux utilisateurs de se connecter avec leur nom d'utilisateur et mot de passe.
    """
    
    def __init__(self):
        """
        Initialise la fenêtre d'authentification.
        Configure la fenêtre et initialise l'interface utilisateur.
        """
        super().__init__()
        self.setWindowTitle("Messagerie chiffrée - Authentification")
        self.setMinimumSize(800, 600)
        
        # Styles de l'interface
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BG};
            }}
            QFrame#card {{
                background-color: {COLOR_CARD};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
            QLabel#title {{
                color: {COLOR_TEXT};
                font-size: 14px;
            }}
            QLineEdit {{
                background-color: {COLOR_INPUT};
                border: 1px solid {COLOR_INPUT_BORDER};
                border-radius: 5px;
                padding: 8px;
                color: {COLOR_TEXT};
            }}
            QLabel#error {{
                color: red;
                font-size: 14px;
            }}
            QPushButton#login {{
                background-color: {COLOR_ACCENT};
                color: white;
                font-size: 15px;
                border-radius: 5px;
            }}
            QPushButton#login:hover {{
                background-color: #c55a47;
            }}
            QPushButton#login:pressed {{
                background-color: #b54a37;
            }}
        """)
        
        self.init_ui()

    def paintEvent(self, event):
        """
        Gère l'événement de peinture de la fenêtre.
        Dessine les cercles décoratifs en arrière-plan.
        
        Args:
            event: L'événement de peinture
        """
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
        """
        Initialise l'interface utilisateur.
        Crée et configure tous les widgets de la fenêtre d'authentification.
        """
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Carte centrale
        card = QFrame(self)
        card.setObjectName("card")
        card.setMinimumSize(350, 380)
        card.setMaximumWidth(500)
        # Centrer la carte
        card_layout = QVBoxLayout()
        card_layout.addWidget(card, alignment=Qt.AlignCenter)
        main_layout.addLayout(card_layout)

        vbox = QVBoxLayout(card)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setSpacing(10)

        # Icône utilisateur
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
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        vbox.addWidget(title)
        vbox.addSpacing(20)  # espace entre le titre et le champ identifiant

        # Champ identifiant
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Identifiant")
        vbox.addWidget(self.input_user)
        vbox.addSpacing(5)
        self.input_user.returnPressed.connect(self.handle_login)

        # Champ mot de passe
        self.input_pwd = QLineEdit()
        self.input_pwd.setPlaceholderText("Mot de passe")
        self.input_pwd.setEchoMode(QLineEdit.Password)
        vbox.addWidget(self.input_pwd)
        self.input_pwd.returnPressed.connect(self.handle_login)

        # Label pour les messages d'erreur
        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.error_label)

        vbox.addSpacing(0)

        # Bouton connexion
        self.btn_login = QPushButton()
        self.btn_login.setObjectName("login")
        self.btn_login.setMinimumSize(200, 65)
        
        # Layout du bouton
        btn_layout = QVBoxLayout(self.btn_login)
        btn_layout.setContentsMargins(10, 8, 10, 8)
        btn_layout.setSpacing(0)
        
        # Icône du bouton
        icon_label = QLabel()
        login_icon_path = os.path.join("resources/img", "log-inblanc.png")
        if os.path.exists(login_icon_path):
            pixmap = QPixmap(login_icon_path)
            icon_label.setPixmap(pixmap.scaled(20, 22))
        icon_label.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(icon_label)
        
        # Texte du bouton
        text_label = QLabel("Se connecter")
        text_label.setStyleSheet("color: white; font-size: 12px;")
        text_label.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(text_label)
        
        self.btn_login.clicked.connect(self.handle_login)
        self.btn_login.setDefault(True)
        vbox.addWidget(self.btn_login, alignment=Qt.AlignHCenter)

    def handle_login(self):
        """
        Gère la tentative de connexion de l'utilisateur.
        Vérifie les identifiants et redirige vers le dashboard si l'authentification réussit.
        """
        user = self.input_user.text()
        pwd = self.input_pwd.text()
        try:
            if not user or not pwd:
                self.error_label.setText("Tous les champs sont obligatoires.")
                return
            
            # Vérification des identifiants
            with SessionLocal() as session:
                db_user = session.query(User).filter_by(username=user).first()
                if not db_user or not pwd_context.verify(pwd, db_user.password):
                    self.error_label.setText("Identifiants incorrects.")
                    return
                
                # Si on arrive ici, l'authentification a réussi
                self.error_label.setText("")
                self.dashboard = Dashboard(username=user)
                self.dashboard.show()
                self.close()
        except Exception as e:
            self.error_label.setText(f"Erreur lors de l'authentification : {str(e)}")
            print("Erreur détaillée :", e)