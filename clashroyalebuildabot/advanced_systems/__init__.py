"""
Advanced Systems for Clash Royale Bot
====================================

Sistemas avançados que transformam o bot em um agente estratégico inteligente.
"""

from .enemy_prediction import AdvancedEnemyPredictor as EnemyCardPredictor
from .dynamic_timing import DynamicTimingManager
from .proactive_defense import ProactiveDefenseManager
from .advanced_elixir_control import AdvancedElixirController
from .intelligent_positioning import IntelligentPositioning, PositionType, UnitInfo
from .phase_control import PhaseController, GamePhase
from .master_integration import MasterBotController, GameState, ActionRecommendation

__version__ = "1.0.0"
__author__ = "Manus AI"

__all__ = [
    "EnemyCardPredictor",
    "DynamicTimingManager", 
    "ProactiveDefenseManager",
    "AdvancedElixirController",
    "IntelligentPositioning",
    "PositionType",
    "UnitInfo",
    "PhaseController",
    "GamePhase",
    "MasterBotController",
    "GameState",
    "ActionRecommendation"
]

