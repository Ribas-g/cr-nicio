import os
from typing import List, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QWidget, QGridLayout, QFrame, QLineEdit
)

from clashroyalebuildabot.constants import IMAGES_DIR
from clashroyalebuildabot.deck_manager import ACTION_MAPPING


class CardSelectorDialog(QDialog):
    """Diálogo para selecionar uma carta"""
    
    card_selected = pyqtSignal(str)  # Emite o nome da ação selecionada
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_action = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Selecionar Carta")
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Escolha uma carta para substituir:")
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Campo de busca
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar carta...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #34495E;
                border: 2px solid #4B6EAF;
                border-radius: 5px;
                color: white;
                padding: 8px;
                font-size: 14px;
            }
        """)
        self.search_edit.textChanged.connect(self.filter_cards)
        layout.addWidget(self.search_edit)
        
        # Área de scroll com as cartas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #4B6EAF;
                border-radius: 8px;
                background-color: #34495E;
            }
        """)
        
        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(10)
        
        scroll_area.setWidget(self.cards_widget)
        layout.addWidget(scroll_area)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        self.select_button = QPushButton("Selecionar")
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ECC71;
            }
        """)
        self.select_button.clicked.connect(self.accept_selection)
        self.select_button.setEnabled(False)
        buttons_layout.addWidget(self.select_button)
        
        layout.addLayout(buttons_layout)
        
        # Carregar todas as cartas
        self.load_all_cards()
        
    def load_all_cards(self):
        """Carrega todas as cartas disponíveis"""
        self.all_cards = []
        row = 0
        col = 0
        max_cols = 4
        
        for action_name, action_class in ACTION_MAPPING.items():
            card_name = action_class.CARD.name
            image_path = os.path.join(IMAGES_DIR, "cards", f"{card_name}.jpg")
            
            card_widget = self.create_card_widget(card_name, image_path, action_name)
            self.cards_layout.addWidget(card_widget, row, col)
            self.all_cards.append(card_widget)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def create_card_widget(self, card_name: str, image_path: str, action_name: str) -> QFrame:
        """Cria um widget para uma carta individual"""
        card_frame = QFrame()
        card_frame.setFixedSize(120, 140)
        card_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #4B6EAF;
                border-radius: 8px;
                background-color: #2C3E50;
            }
            QFrame:hover {
                border-color: #57A6FF;
                background-color: #34495E;
            }
            QFrame.selected {
                border-color: #27AE60;
                background-color: #27AE60;
            }
        """)
        
        layout = QVBoxLayout(card_frame)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Imagem da carta
        image_label = QLabel()
        image_label.setFixedSize(100, 100)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaled(
                100, 100, Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("?")
            image_label.setStyleSheet("color: white; font-size: 16px;")
        
        # Nome da carta
        name_label = QLabel(card_name.replace("_", " ").title())
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: white; font-size: 10px; font-weight: bold;")
        name_label.setWordWrap(True)
        
        layout.addWidget(image_label)
        layout.addWidget(name_label)
        
        # Armazenar dados da carta
        card_frame.action_name = action_name
        card_frame.card_name = card_name
        card_frame.is_selected = False
        
        # Conectar clique
        card_frame.mousePressEvent = lambda event, frame=card_frame: self.on_card_clicked(frame)
        
        return card_frame
        
    def on_card_clicked(self, card_frame: QFrame):
        """Chamado quando uma carta é clicada"""
        # Desmarcar todas as cartas
        for card in self.all_cards:
            card.is_selected = False
            card.setStyleSheet(card.styleSheet().replace("selected", ""))
        
        # Marcar a carta selecionada
        card_frame.is_selected = True
        card_frame.setStyleSheet(card_frame.styleSheet() + " QFrame.selected { border-color: #27AE60; background-color: #27AE60; }")
        
        self.selected_action = card_frame.action_name
        self.select_button.setEnabled(True)
        
    def filter_cards(self, search_text: str):
        """Filtra as cartas baseado no texto de busca"""
        search_lower = search_text.lower()
        
        for card in self.all_cards:
            card_name = card.card_name.lower()
            action_name = card.action_name.lower()
            
            if search_text == "" or search_lower in card_name or search_lower in action_name:
                card.show()
            else:
                card.hide()
                
    def accept_selection(self):
        """Aceita a seleção da carta"""
        if self.selected_action:
            self.card_selected.emit(self.selected_action)
            self.accept()


class EditableCardWidget(QFrame):
    """Widget para uma carta editável no deck"""
    
    card_clicked = pyqtSignal(str)  # Emite o nome da ação atual
    
    def __init__(self, card_name: str, card_image_path: str, action_name: str):
        super().__init__()
        self.card_name = card_name
        self.action_name = action_name
        self.setFixedSize(80, 100)
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #4B6EAF;
                border-radius: 8px;
                background-color: #2C3E50;
            }
            QFrame:hover {
                border-color: #57A6FF;
                background-color: #34495E;
                cursor: pointer;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Imagem da carta
        self.image_label = QLabel()
        self.image_label.setFixedSize(70, 70)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if card_image_path and os.path.exists(card_image_path):
            pixmap = QPixmap(card_image_path).scaled(
                70, 70, Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("?")
            self.image_label.setStyleSheet("color: white; font-size: 12px;")
        
        # Nome da carta
        self.name_label = QLabel(card_name.replace("_", " ").title())
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("color: white; font-size: 8px; font-weight: bold;")
        self.name_label.setWordWrap(True)
        
        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)
        
        # Conectar clique
        self.mousePressEvent = self.on_clicked
        
    def on_clicked(self, event):
        """Chamado quando a carta é clicada"""
        self.card_clicked.emit(self.action_name)
        
    def update_card(self, new_card_name: str, new_action_name: str):
        """Atualiza a carta com novos dados"""
        self.card_name = new_card_name
        self.action_name = new_action_name
        
        # Atualizar imagem
        image_path = os.path.join(IMAGES_DIR, "cards", f"{new_card_name}.jpg")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaled(
                70, 70, Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("?")
            
        # Atualizar nome
        self.name_label.setText(new_card_name.replace("_", " ").title())
