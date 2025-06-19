from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
from PyQt5.QtCore import Qt
from app.crypto_manager import CryptoManager

class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
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
        top_bar_layout.setSpacing(0)
        title_label = QLabel("<span style='color:white;font-size:20px;font-weight:600;'>Paramètres</span>")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch(1)
        main_layout.addWidget(top_bar)

        # --- CONTENU PRINCIPAL ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Colonne de navigation à gauche (sections)
        nav_col = QFrame()
        nav_col.setStyleSheet("background-color: #404349;")
        nav_col.setMinimumWidth(220)
        nav_col.setMaximumWidth(260)
        nav_layout = QVBoxLayout(nav_col)
        nav_layout.setContentsMargins(0, 30, 0, 30)
        nav_layout.setSpacing(18)
        # Ajoutez ici d'autres boutons de section si besoin
        btn_crypto = QPushButton("Chiffrement & Certificat")
        btn_crypto.setStyleSheet("""
            QPushButton { background: #D66853; color: white; font-size: 16px; border-radius: 10px; padding: 12px 0; }
            QPushButton:hover { background: #c55a47; }
            QPushButton:pressed { background: #b54a37; }
        """)
        btn_crypto.setCursor(Qt.PointingHandCursor)
        btn_crypto.clicked.connect(lambda: self.show_section('crypto'))
        nav_layout.addWidget(btn_crypto)
        nav_layout.addStretch(1)
        content_layout.addWidget(nav_col)

        # Colonne centrale (contenu de la section)
        self.section_area = QScrollArea()
        self.section_area.setWidgetResizable(True)
        content_layout.addWidget(self.section_area, stretch=1)
        main_layout.addLayout(content_layout)

        self.sections = {}
        self.init_crypto_section()
        self.show_section('crypto')

    def init_crypto_section(self):
        section = QFrame()
        section.setStyleSheet("background: #fff; border-radius: 12px;")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(18)
        title = QLabel("<span style='font-size:18px;font-weight:600;'>Chiffrement & Certificat</span>")
        layout.addWidget(title)
        self.info_label = QLabel()
        self.info_label.setStyleSheet("font-size:15px;")
        layout.addWidget(self.info_label)
        self.refresh_info()
        regen_btn = QPushButton("Régénérer le certificat")
        regen_btn.setStyleSheet("""
            QPushButton { background: #D66853; color: white; font-size: 15px; border-radius: 8px; padding: 10px 18px; }
            QPushButton:hover { background: #c55a47; }
            QPushButton:pressed { background: #b54a37; }
        """)
        regen_btn.setCursor(Qt.PointingHandCursor)
        regen_btn.clicked.connect(self.regenerate_cert)
        layout.addWidget(regen_btn, alignment=Qt.AlignLeft)
        layout.addStretch(1)
        self.sections['crypto'] = section

    def show_section(self, key):
        if key in self.sections:
            self.section_area.takeWidget()
            self.section_area.setWidget(self.sections[key])

    def refresh_info(self):
        try:
            info = CryptoManager.get_certificate_info()
            text = f"<b>Sujet :</b> {info['subject']}<br>"
            text += f"<b>Émetteur :</b> {info['issuer']}<br>"
            text += f"<b>Série :</b> {info['serial']}<br>"
            text += f"<b>Valide du :</b> {info['not_before']}<br>"
            text += f"<b>Valide jusqu'au :</b> {info['not_after']}"
        except Exception as e:
            text = f"<span style='color:red'>Certificat non trouvé ou invalide.<br>{e}</span>"
        self.info_label.setText(text)

    def regenerate_cert(self):
        CryptoManager.generate_key_and_cert()
        self.refresh_info()
