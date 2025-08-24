"""
Bot de Clash Royale Aprimorado
==============================

Sistema inteligente de bot para Clash Royale com:
- Análise de deck e papéis das cartas
- Sistema de combos coordenados
- Defesa inteligente com priorização de ameaças
- Ações contextuais das cartas

Versão: 2.0.0
Autor: Assistente IA
Data: 2025-08-24
"""

# Exports for clashroyalebuildabot
from . import constants
from .bot import Bot
from .detectors import CardDetector
from .detectors import Detector
from .detectors import NumberDetector
from .detectors import OnnxDetector
from .detectors import ScreenDetector
from .detectors import UnitDetector
from .emulator import Emulator
from .namespaces import Cards
from .namespaces import Screens
from .namespaces import State
from .namespaces import Units
from .visualizer import Visualizer

# Sistemas core (sem importar enhanced_bot aqui)
from .core.card_roles import CardRole, CardRoleDatabase, DeckAnalyzer
from .core.game_state import GameStateAnalyzer, GameStateInfo
from .core.combo_system import ComboManager, ComboType
from .core.defense_system import DefenseManager, ThreatAnalyzer
from .core.enhanced_action import EnhancedAction

__version__ = "2.0.0"
__author__ = "Assistente IA"

__all__ = [
    "constants",
    "Visualizer",
    "Cards",
    "Units",
    "State",
    "Detector",
    "OnnxDetector",
    "ScreenDetector",
    "NumberDetector",
    "UnitDetector",
    "CardDetector",
    "Emulator",
    "Bot",
    
    # Sistemas core
    'CardRole', 'CardRoleDatabase', 'DeckAnalyzer',
    'GameStateAnalyzer', 'GameStateInfo',
    'ComboManager', 'ComboType',
    'DefenseManager', 'ThreatAnalyzer',
    'EnhancedAction',
]

