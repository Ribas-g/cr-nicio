"""
Módulo de ações do bot.
Contém implementações de cartas específicas.
"""

# Ações originais
from .archers_action import ArchersAction
from .arrows_action import ArrowsAction
from .baby_dragon_action import BabyDragonAction
from .bats_action import BatsAction
from .cannon_action import CannonAction
from .fireball_action import FireballAction
from .giant_action import GiantAction
from .goblin_barrel_action import GoblinBarrelAction
from .knight_action import KnightAction
from .minions_action import MinionsAction
from .minipekka_action import MinipekkaAction
from .musketeer_action import MusketeerAction
from .skeletons_action import SkeletonsAction
from .spear_goblins_action import SpearGoblinsAction
from .witch_action import WitchAction
from .zap_action import ZapAction

# Ações aprimoradas
from .enhanced_giant_action import EnhancedGiantAction
from .enhanced_musketeer_action import EnhancedMusketeerAction
from .enhanced_hog_rider_action import EnhancedHogRiderAction

__all__ = [
    # Ações originais
    "ArchersAction",
    "ArrowsAction",
    "BabyDragonAction",
    "BatsAction",
    "CannonAction",
    "FireballAction",
    "GiantAction",
    "GoblinBarrelAction",
    "KnightAction",
    "MinionsAction",
    "MinipekkaAction",
    "MusketeerAction",
    "SkeletonsAction",
    "SpearGoblinsAction",
    "WitchAction",
    "ZapAction",
    
    # Ações aprimoradas
    'EnhancedGiantAction',
    'EnhancedMusketeerAction', 
    'EnhancedHogRiderAction'
]

