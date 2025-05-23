from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
import os

class IconTextButton(QFrame):
    def __init__(self, icon_path, text, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #D66853;
                border-radius: 10px;
            }
        """)
        self.setFixedSize(120, 70)
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
    def __init__(self, icon_path, diameter=60, parent=None):
        super().__init__(parent)
        self.setFixedSize(diameter, diameter)
        self.setStyleSheet(f"""
            QFrame {{
                background: #D66853;
                border-radius: {diameter//2}px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        icon_label.setPixmap(pixmap.scaled(diameter-20, diameter-20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.setStyleSheet("background-color: #F5F5F5;")
        self.setFixedSize(1200, 800)

        # Layout principal vertical (barre du haut + contenu)
        main_vlayout = QVBoxLayout(self)
        main_vlayout.setContentsMargins(0, 0, 0, 0)
        main_vlayout.setSpacing(0)

        # --- BARRE SUPÉRIEURE ---
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #212D40;")
        top_bar.setFixedHeight(55)
        main_vlayout.addWidget(top_bar)

        # --- CONTENU PRINCIPAL (colonne gauche + colonne centrale) ---
        main_hlayout = QHBoxLayout()
        main_hlayout.setContentsMargins(0, 0, 0, 0)
        main_hlayout.setSpacing(0)

        # Colonne de gauche
        left_col = QFrame()
        left_col.setStyleSheet("background-color: #364156;")
        left_col.setFixedWidth(180)
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 20, 0, 30)
        left_layout.setSpacing(18)

        # Bouton Nv conversation
        btn_nvc = IconTextButton(os.path.join("resources/img", "plusblanc.png"), "Nv conversation")
        left_layout.addWidget(btn_nvc, alignment=Qt.AlignHCenter)

        # Bouton Recherche LAN
        btn_lan = IconTextButton(os.path.join("resources/img", "radarblanc.png"), "Recherche LAN")
        left_layout.addWidget(btn_lan, alignment=Qt.AlignHCenter)

        # Logos laptopblanc.png
        for _ in range(4):
            circle_icon = CircleIcon(os.path.join("resources/img", "laptopblanc.png"), diameter=60)
            left_layout.addWidget(circle_icon, alignment=Qt.AlignHCenter)
            left_layout.addSpacing(18)

        left_layout.addStretch(1)
       
        # Bouton Paramètres en bas
        btn_settings = IconTextButton(os.path.join("resources/img", "settingblanc.png"), "Paramètres")
        left_layout.addWidget(btn_settings, alignment=Qt.AlignHCenter | Qt.AlignBottom)

        main_hlayout.addWidget(left_col)

        # Colonne centrale (vide pour l'instant)
        center_col = QFrame()
        center_col.setStyleSheet("background-color: #F5F5F5;")
        main_hlayout.addWidget(center_col, stretch=1)

        main_vlayout.addLayout(main_hlayout) 