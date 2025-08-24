"""
Sistema de papéis das cartas para análise estratégica do deck.
Define os diferentes papéis que cada carta pode desempenhar no jogo.
"""

from enum import Enum
from typing import Dict, List, Set
from clashroyalebuildabot import Cards


class CardRole(Enum):
    """Papéis estratégicos que uma carta pode desempenhar"""
    # Win Conditions - Cartas que atacam diretamente as torres
    WIN_CONDITION = "win_condition"
    
    # Tanques - Cartas com muito HP que absorvem dano
    TANK = "tank"
    
    # Suporte - Cartas que apoiam outras tropas
    SUPPORT = "support"
    
    # Defesa - Cartas especializadas em defender
    DEFENSE = "defense"
    
    # Feitiços - Cartas de dano direto ou utilidade
    SPELL = "spell"
    
    # Swarm - Tropas em grupo/baixo custo
    SWARM = "swarm"
    
    # Anti-Air - Especializadas contra tropas aéreas
    ANTI_AIR = "anti_air"
    
    # Building - Construções
    BUILDING = "building"
    
    # Cycle - Cartas de baixo custo para ciclar
    CYCLE = "cycle"


class CardRoleDatabase:
    """Base de dados com os papéis de cada carta"""
    
    CARD_ROLES: Dict[Cards, Set[CardRole]] = {
        # Win Conditions
        Cards.GIANT: {CardRole.WIN_CONDITION, CardRole.TANK},
        Cards.HOG_RIDER: {CardRole.WIN_CONDITION},
        Cards.ROYAL_GIANT: {CardRole.WIN_CONDITION, CardRole.TANK},
        Cards.GOLEM: {CardRole.WIN_CONDITION, CardRole.TANK},
        Cards.PEKKA: {CardRole.WIN_CONDITION, CardRole.TANK},
        Cards.MEGA_KNIGHT: {CardRole.WIN_CONDITION, CardRole.TANK},
        Cards.ELECTRO_GIANT: {CardRole.WIN_CONDITION, CardRole.TANK},
        Cards.LAVA_HOUND: {CardRole.WIN_CONDITION, CardRole.TANK},
        Cards.BALLOON: {CardRole.WIN_CONDITION},
        Cards.X_BOW: {CardRole.WIN_CONDITION, CardRole.BUILDING},
        Cards.MORTAR: {CardRole.WIN_CONDITION, CardRole.BUILDING},
        
        # Suporte
        Cards.MUSKETEER: {CardRole.SUPPORT, CardRole.ANTI_AIR},
        Cards.ARCHERS: {CardRole.SUPPORT, CardRole.ANTI_AIR, CardRole.CYCLE},
        Cards.WIZARD: {CardRole.SUPPORT, CardRole.ANTI_AIR},
        Cards.BABY_DRAGON: {CardRole.SUPPORT, CardRole.ANTI_AIR},
        Cards.ELECTRO_WIZARD: {CardRole.SUPPORT, CardRole.ANTI_AIR},
        Cards.ICE_WIZARD: {CardRole.SUPPORT, CardRole.DEFENSE},
        Cards.PRINCESS: {CardRole.SUPPORT, CardRole.ANTI_AIR},
        Cards.MAGIC_ARCHER: {CardRole.SUPPORT},
        
        # Defesa
        Cards.CANNON: {CardRole.DEFENSE, CardRole.BUILDING, CardRole.CYCLE},
        Cards.TESLA: {CardRole.DEFENSE, CardRole.BUILDING, CardRole.ANTI_AIR},
        Cards.INFERNO_TOWER: {CardRole.DEFENSE, CardRole.BUILDING},
        Cards.BOMB_TOWER: {CardRole.DEFENSE, CardRole.BUILDING},
        Cards.BARBARIAN_HUT: {CardRole.DEFENSE, CardRole.BUILDING},
        Cards.GOBLIN_HUT: {CardRole.DEFENSE, CardRole.BUILDING},
        Cards.FURNACE: {CardRole.DEFENSE, CardRole.BUILDING},
        Cards.TOMBSTONE: {CardRole.DEFENSE, CardRole.BUILDING, CardRole.CYCLE},
        
        # Feitiços
        Cards.FIREBALL: {CardRole.SPELL},
        Cards.ARROWS: {CardRole.SPELL, CardRole.CYCLE},
        Cards.ZAP: {CardRole.SPELL, CardRole.CYCLE},
        Cards.THE_LOG: {CardRole.SPELL, CardRole.CYCLE},
        Cards.POISON: {CardRole.SPELL},
        Cards.LIGHTNING: {CardRole.SPELL},
        Cards.ROCKET: {CardRole.SPELL},
        Cards.FREEZE: {CardRole.SPELL},
        Cards.TORNADO: {CardRole.SPELL, CardRole.DEFENSE},
        Cards.RAGE: {CardRole.SPELL},
        
        # Swarm
        Cards.GOBLINS: {CardRole.SWARM, CardRole.CYCLE},
        Cards.SKELETON_ARMY: {CardRole.SWARM, CardRole.DEFENSE},
        Cards.MINION_HORDE: {CardRole.SWARM, CardRole.ANTI_AIR},
        Cards.BARBARIANS: {CardRole.SWARM, CardRole.DEFENSE},
        Cards.GUARDS: {CardRole.SWARM, CardRole.DEFENSE},
        Cards.BATS: {CardRole.SWARM, CardRole.CYCLE},
        
        # Outras cartas importantes
        Cards.KNIGHT: {CardRole.TANK, CardRole.CYCLE},
        Cards.VALKYRIE: {CardRole.TANK, CardRole.DEFENSE},
        Cards.MINIPEKKA: {CardRole.DEFENSE, CardRole.SUPPORT},
        Cards.PRINCE: {CardRole.WIN_CONDITION, CardRole.SUPPORT},
        Cards.DARK_PRINCE: {CardRole.SUPPORT, CardRole.DEFENSE},
    }
    
    @classmethod
    def get_roles(cls, card: Cards) -> Set[CardRole]:
        """Retorna os papéis de uma carta"""
        return cls.CARD_ROLES.get(card, {CardRole.SUPPORT})
    
    @classmethod
    def has_role(cls, card: Cards, role: CardRole) -> bool:
        """Verifica se uma carta tem um papel específico"""
        return role in cls.get_roles(card)
    
    @classmethod
    def get_cards_by_role(cls, role: CardRole) -> List[Cards]:
        """Retorna todas as cartas que têm um papel específico"""
        return [card for card, roles in cls.CARD_ROLES.items() if role in roles]


class DeckAnalyzer:
    """Analisa a composição do deck e identifica estratégias"""
    
    def __init__(self, deck: List[Cards]):
        self.deck = deck
        self.roles_count = self._count_roles()
        self.strategy = self._identify_strategy()
    
    def _count_roles(self) -> Dict[CardRole, int]:
        """Conta quantas cartas de cada papel existem no deck"""
        count = {role: 0 for role in CardRole}
        for card in self.deck:
            roles = CardRoleDatabase.get_roles(card)
            for role in roles:
                count[role] += 1
        return count
    
    def _identify_strategy(self) -> str:
        """Identifica a estratégia principal do deck"""
        win_conditions = self.roles_count[CardRole.WIN_CONDITION]
        tanks = self.roles_count[CardRole.TANK]
        spells = self.roles_count[CardRole.SPELL]
        cycle_cards = self.roles_count[CardRole.CYCLE]
        
        if win_conditions >= 2:
            return "DUAL_WIN_CONDITION"
        elif tanks >= 2:
            return "HEAVY_TANK"
        elif cycle_cards >= 4:
            return "CYCLE"
        elif spells >= 3:
            return "SPELL_BAIT"
        elif self.roles_count[CardRole.DEFENSE] >= 4:
            return "DEFENSIVE"
        else:
            return "BALANCED"
    
    def get_primary_win_condition(self) -> Cards:
        """Retorna a win condition principal do deck"""
        win_conditions = [card for card in self.deck 
                         if CardRoleDatabase.has_role(card, CardRole.WIN_CONDITION)]
        
        if not win_conditions:
            return None
            
        # Prioriza tanques pesados
        heavy_tanks = [Cards.GOLEM, Cards.ELECTRO_GIANT, Cards.GIANT, Cards.ROYAL_GIANT]
        for tank in heavy_tanks:
            if tank in win_conditions:
                return tank
                
        return win_conditions[0]
    
    def get_support_cards(self) -> List[Cards]:
        """Retorna cartas de suporte do deck"""
        return [card for card in self.deck 
                if CardRoleDatabase.has_role(card, CardRole.SUPPORT)]
    
    def should_play_aggressive(self, elixir: int, enemy_elixir_spent: int) -> bool:
        """Determina se deve jogar agressivamente baseado na estratégia do deck"""
        if self.strategy == "CYCLE":
            return elixir >= 6 and enemy_elixir_spent >= 8
        elif self.strategy == "HEAVY_TANK":
            return elixir >= 8 and enemy_elixir_spent >= 10
        elif self.strategy == "DEFENSIVE":
            return elixir == 10 and enemy_elixir_spent >= 12
        else:
            return elixir >= 7 and enemy_elixir_spent >= 8
    
    def get_defensive_priority(self) -> List[CardRole]:
        """Retorna a prioridade de cartas para defesa baseada na estratégia"""
        if self.strategy == "CYCLE":
            return [CardRole.CYCLE, CardRole.DEFENSE, CardRole.SWARM]
        elif self.strategy == "HEAVY_TANK":
            return [CardRole.DEFENSE, CardRole.BUILDING, CardRole.SWARM]
        else:
            return [CardRole.DEFENSE, CardRole.SWARM, CardRole.SUPPORT]

