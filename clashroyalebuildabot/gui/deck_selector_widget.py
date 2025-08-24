import os
from typing import List, Dict, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QScrollArea, QFrame, QGridLayout, QTextEdit,
    QDialog, QLineEdit, QFormLayout, QMessageBox
)

from clashroyalebuildabot.constants import IMAGES_DIR
from clashroyalebuildabot.deck_manager import DeckManager
from clashroyalebuildabot.gui.card_selector_dialog import CardSelectorDialog, EditableCardWidget


class DeckCardWidget(QFrame):
    """Widget para exibir uma carta individual"""
    
    def __init__(self, card_name: str, card_image_path: str = None):
        super().__init__()
        self.card_name = card_name
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
        self.name_label = QLabel(card_name.replace("Action", "").replace("_", " "))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("color: white; font-size: 8px; font-weight: bold;")
        self.name_label.setWordWrap(True)
        
        layout.addWidget(self.image_label)
        layout.addWidget(self.name_label)


class DeckPreviewWidget(QWidget):
    """Widget para visualizar um deck completo"""
    
    def __init__(self, deck_info: Dict[str, str], deck_manager: DeckManager, is_editable: bool = False):
        super().__init__()
        self.deck_info = deck_info
        self.deck_manager = deck_manager
        self.is_editable = is_editable
        self.card_widgets = []
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título do deck
        title_label = QLabel(deck_info["name"])
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Descrição
        desc_label = QLabel(deck_info["description"])
        desc_label.setStyleSheet("color: #BDC3C7; font-size: 12px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Grid de cartas
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(5)
        
        try:
            actions = self.deck_manager.get_deck_actions(deck_info["id"])
            
            for i, action in enumerate(actions):
                row = i // 4
                col = i % 4
                
                # Obter nome da carta e caminho da imagem
                card_name = action.CARD.name
                image_path = os.path.join(IMAGES_DIR, "cards", f"{card_name}.jpg")
                
                if is_editable:
                    card_widget = EditableCardWidget(card_name, image_path, action.__name__)
                    card_widget.card_clicked.connect(lambda action_name, index=i: self.on_card_clicked(action_name, index))
                    self.card_widgets.append(card_widget)
                else:
                    card_widget = DeckCardWidget(card_name, image_path)
                
                cards_layout.addWidget(card_widget, row, col)
        
        except Exception as e:
            error_label = QLabel(f"Erro ao carregar deck: {str(e)}")
            error_label.setStyleSheet("color: red; font-size: 12px;")
            cards_layout.addWidget(error_label, 0, 0)
        
        layout.addWidget(cards_widget)
        
    def on_card_clicked(self, action_name: str, index: int):
        """Chamado quando uma carta editável é clicada"""
        if not self.is_editable:
            return
            
        # Abrir diálogo de seleção de carta
        dialog = CardSelectorDialog(self)
        dialog.card_selected.connect(lambda new_action: self.replace_card(index, new_action))
        dialog.exec()
        
    def replace_card(self, index: int, new_action_name: str):
        """Substitui uma carta no deck"""
        if index < len(self.card_widgets):
            # Obter a nova ação
            from clashroyalebuildabot.deck_manager import ACTION_MAPPING
            new_action = ACTION_MAPPING.get(new_action_name)
            if new_action:
                new_card_name = new_action.CARD.name
                self.card_widgets[index].update_card(new_card_name, new_action_name)
                
    def get_current_deck_actions(self) -> List[str]:
        """Retorna as ações atuais do deck editado"""
        return [card.action_name for card in self.card_widgets]


class DeckSelectorWidget(QWidget):
    """Widget principal para seleção de decks"""
    
    deck_changed = pyqtSignal(str)  # Sinal emitido quando o deck muda
    
    def __init__(self, deck_manager: DeckManager):
        super().__init__()
        self.deck_manager = deck_manager
        self.current_preview_widget = None
        self.setup_ui()
        self.load_decks()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Seleção de Deck")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Combo box para seleção
        self.deck_combo = QComboBox()
        self.deck_combo.setStyleSheet("""
            QComboBox {
                background-color: #34495E;
                border: 2px solid #4B6EAF;
                border-radius: 5px;
                color: white;
                padding: 5px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
            QComboBox QAbstractItemView {
                background-color: #34495E;
                color: white;
                selection-background-color: #4B6EAF;
            }
        """)
        self.deck_combo.currentTextChanged.connect(self.on_deck_changed)
        layout.addWidget(self.deck_combo)
        
        # Área de preview do deck
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #4B6EAF;
                border-radius: 8px;
                background-color: #2C3E50;
            }
        """)
        self.preview_area.setMinimumHeight(300)
        layout.addWidget(self.preview_area)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Selecionar Deck")
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
        self.select_button.clicked.connect(self.select_current_deck)
        buttons_layout.addWidget(self.select_button)
        
        self.edit_deck_button = QPushButton("Editar Deck")
        self.edit_deck_button.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F39C12;
            }
        """)
        self.edit_deck_button.clicked.connect(self.edit_current_deck)
        buttons_layout.addWidget(self.edit_deck_button)
        
        self.new_deck_button = QPushButton("Novo Deck")
        self.new_deck_button.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        self.new_deck_button.clicked.connect(self.create_new_deck)
        buttons_layout.addWidget(self.new_deck_button)
        
        layout.addLayout(buttons_layout)
    
    def load_decks(self):
        """Carrega os decks disponíveis"""
        self.deck_combo.clear()
        available_decks = self.deck_manager.get_available_decks()
        
        for deck in available_decks:
            self.deck_combo.addItem(deck["name"], deck["id"])
        
        # Selecionar deck atual
        current_deck_info = self.deck_manager.get_current_deck_info()
        index = self.deck_combo.findData(current_deck_info["id"])
        if index >= 0:
            self.deck_combo.setCurrentIndex(index)
    
    def on_deck_changed(self, deck_name: str):
        """Atualiza o preview quando o deck muda"""
        deck_id = self.deck_combo.currentData()
        if deck_id:
            available_decks = self.deck_manager.get_available_decks()
            deck_info = next((d for d in available_decks if d["id"] == deck_id), None)
            
            if deck_info:
                preview_widget = DeckPreviewWidget(deck_info, self.deck_manager, is_editable=False)
                self.current_preview_widget = preview_widget
                self.preview_area.setWidget(preview_widget)
    
    def select_current_deck(self):
        """Seleciona o deck atual"""
        deck_id = self.deck_combo.currentData()
        if deck_id:
            # Se estamos editando, salvar as mudanças primeiro
            if self.current_preview_widget and hasattr(self.current_preview_widget, 'is_editable') and self.current_preview_widget.is_editable:
                self.save_edited_deck()
            
            self.deck_manager.set_current_deck(deck_id)
            self.deck_changed.emit(deck_id)
            QMessageBox.information(self, "Deck Selecionado", 
                                  f"Deck '{self.deck_combo.currentText()}' selecionado com sucesso!")
            
    def edit_current_deck(self):
        """Entra no modo de edição do deck atual"""
        deck_id = self.deck_combo.currentData()
        if deck_id:
            available_decks = self.deck_manager.get_available_decks()
            deck_info = next((d for d in available_decks if d["id"] == deck_id), None)
            
            if deck_info:
                # Criar preview editável
                preview_widget = DeckPreviewWidget(deck_info, self.deck_manager, is_editable=True)
                self.current_preview_widget = preview_widget
                self.preview_area.setWidget(preview_widget)
                
                # Mudar texto do botão
                self.edit_deck_button.setText("Salvar Edição")
                self.edit_deck_button.clicked.disconnect()
                self.edit_deck_button.clicked.connect(self.save_edited_deck)
                
    def save_edited_deck(self):
        """Salva as mudanças do deck editado"""
        if self.current_preview_widget and hasattr(self.current_preview_widget, 'is_editable') and self.current_preview_widget.is_editable:
            deck_id = self.deck_combo.currentData()
            if deck_id:
                # Obter as ações atuais do deck editado
                current_actions = self.current_preview_widget.get_current_deck_actions()
                
                # Salvar o deck
                deck_info = self.deck_manager.get_current_deck_info()
                self.deck_manager.save_deck(deck_id, deck_info["name"], deck_info["description"], current_actions)
                
                # Voltar ao modo de visualização
                preview_widget = DeckPreviewWidget(deck_info, self.deck_manager, is_editable=False)
                self.current_preview_widget = preview_widget
                self.preview_area.setWidget(preview_widget)
                
                # Restaurar botão
                self.edit_deck_button.setText("Editar Deck")
                self.edit_deck_button.clicked.disconnect()
                self.edit_deck_button.clicked.connect(self.edit_current_deck)
                
                QMessageBox.information(self, "Deck Salvo", "Deck editado e salvo com sucesso!")
    
    def create_new_deck(self):
        """Abre diálogo para criar novo deck"""
        dialog = NewDeckDialog(self.deck_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_decks()  # Recarrega a lista de decks


class NewDeckDialog(QDialog):
    """Diálogo para criar novo deck"""
    
    def __init__(self, deck_manager: DeckManager, parent=None):
        super().__init__(parent)
        self.deck_manager = deck_manager
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Criar Novo Deck")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
                color: white;
            }
        """)
        
        layout = QFormLayout(self)
        layout.setSpacing(15)
        
        # Campos de entrada
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #34495E;
                border: 2px solid #4B6EAF;
                border-radius: 5px;
                color: white;
                padding: 8px;
                font-size: 14px;
            }
        """)
        layout.addRow("Nome do Deck:", self.name_edit)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setStyleSheet("""
            QTextEdit {
                background-color: #34495E;
                border: 2px solid #4B6EAF;
                border-radius: 5px;
                color: white;
                padding: 8px;
                font-size: 14px;
            }
        """)
        layout.addRow("Descrição:", self.desc_edit)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Salvar")
        self.save_button.setStyleSheet("""
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
        self.save_button.clicked.connect(self.save_deck)
        buttons_layout.addWidget(self.save_button)
        
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
        
        layout.addRow("", buttons_layout)
    
    def save_deck(self):
        """Salva o novo deck"""
        name = self.name_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Erro", "Nome do deck é obrigatório!")
            return
        
        # Por enquanto, usa o deck atual como base
        current_deck_info = self.deck_manager.get_current_deck_info()
        current_actions = self.deck_manager.get_deck_actions()
        
        # Converte ações para nomes de string
        card_names = []
        for action in current_actions:
            card_names.append(action.__name__)
        
        # Cria ID único para o deck
        deck_id = f"deck_{len(self.deck_manager.get_available_decks()) + 1}"
        
        try:
            self.deck_manager.save_deck(deck_id, name, description, card_names)
            QMessageBox.information(self, "Sucesso", "Deck criado com sucesso!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar deck: {str(e)}")
