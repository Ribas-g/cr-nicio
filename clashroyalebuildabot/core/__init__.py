"""
Módulo core do sistema aprimorado.
Contém os sistemas fundamentais de inteligência do bot.
"""

from .card_roles import CardRole, CardRoleDatabase, DeckAnalyzer
from .game_state import GameStateAnalyzer, GameStateInfo, ThreatLevel, GamePhase
from .combo_system import ComboManager, ComboType, ComboDefinition
from .defense_system import DefenseManager, ThreatAnalyzer, DefenseType
from .enhanced_action import EnhancedAction

__all__ = [
    'CardRole', 'CardRoleDatabase', 'DeckAnalyzer',
    'GameStateAnalyzer', 'GameStateInfo', 'ThreatLevel', 'GamePhase',
    'ComboManager', 'ComboType', 'ComboDefinition',
    'DefenseManager', 'ThreatAnalyzer', 'DefenseType',
    'EnhancedAction'
]

