"""
Sistema de combos para coordenação inteligente entre cartas.
Gerencia sinergias, timing e sequenciamento de jogadas.
"""

from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
from clashroyalebuildabot import Cards
from .card_roles import CardRole, CardRoleDatabase
from .game_state import GameStateInfo, ThreatLevel


class ComboType(Enum):
    """Tipos de combos disponíveis"""
    TANK_SUPPORT = "tank_support"        # Tanque + Suporte atrás
    QUICK_CYCLE = "quick_cycle"          # Cartas rápidas para pressão
    SPELL_BAIT = "spell_bait"           # Forçar uso de feitiços
    COUNTER_PUSH = "counter_push"        # Contra-ataque após defesa
    BUILDING_SIEGE = "building_siege"    # X-Bow/Mortar + proteção
    AIR_SWARM = "air_swarm"             # Lava Hound + suporte aéreo


@dataclass
class ComboDefinition:
    """Define um combo específico"""
    name: str
    combo_type: ComboType
    primary_card: Cards
    support_cards: List[Cards]
    min_elixir: int
    max_elixir: int
    timing_delay: float  # Segundos entre cartas
    positioning_rules: Dict[str, str]
    success_conditions: List[str]
    priority: int  # 1-10, maior = mais prioritário


@dataclass
class ActiveCombo:
    """Representa um combo em execução"""
    definition: ComboDefinition
    cards_played: List[Cards]
    start_time: float
    expected_next_card: Optional[Cards]
    next_card_timing: float
    is_complete: bool
    success_probability: float


class ComboDatabase:
    """Base de dados com definições de combos"""
    
    COMBOS: List[ComboDefinition] = [
        # Gigante + Mosqueteira (combo clássico)
        ComboDefinition(
            name="Giant Musketeer",
            combo_type=ComboType.TANK_SUPPORT,
            primary_card=Cards.GIANT,
            support_cards=[Cards.MUSKETEER],
            min_elixir=9,
            max_elixir=10,
            timing_delay=2.0,  # Esperar Gigante chegar na ponte
            positioning_rules={
                Cards.GIANT.name: "behind_king_tower",
                Cards.MUSKETEER.name: "behind_giant_when_crossing"
            },
            success_conditions=["giant_crosses_bridge", "musketeer_behind_giant"],
            priority=8
        ),
        
        # Gigante + Bombardeiro
        ComboDefinition(
            name="Giant Bomber",
            combo_type=ComboType.TANK_SUPPORT,
            primary_card=Cards.GIANT,
            support_cards=[Cards.BOMBER],
            min_elixir=8,
            max_elixir=10,
            timing_delay=1.5,
            positioning_rules={
                Cards.GIANT.name: "behind_king_tower",
                Cards.BOMBER.name: "behind_giant"
            },
            success_conditions=["giant_crosses_bridge"],
            priority=7
        ),
        
        # Corredor + Gelo (contra-ataque rápido)
        ComboDefinition(
            name="Hog Ice Spirit",
            combo_type=ComboType.QUICK_CYCLE,
            primary_card=Cards.HOG_RIDER,
            support_cards=[Cards.ICE_SPIRIT],
            min_elixir=6,
            max_elixir=8,
            timing_delay=0.5,
            positioning_rules={
                Cards.HOG_RIDER.name: "bridge",
                Cards.ICE_SPIRIT.name: "in_front_of_hog"
            },
            success_conditions=["enemy_low_elixir"],
            priority=9
        ),
        
        # Golem + Suporte aéreo
        ComboDefinition(
            name="Golem Night Witch",
            combo_type=ComboType.TANK_SUPPORT,
            primary_card=Cards.GOLEM,
            support_cards=[Cards.NIGHT_WITCH, Cards.BABY_DRAGON],
            min_elixir=12,
            max_elixir=15,
            timing_delay=3.0,
            positioning_rules={
                Cards.GOLEM.name: "behind_king_tower",
                Cards.NIGHT_WITCH.name: "behind_golem",
                Cards.BABY_DRAGON.name: "behind_golem"
            },
            success_conditions=["golem_crosses_bridge"],
            priority=6
        ),
        
        # X-Bow + Tesla (siege)
        ComboDefinition(
            name="X-Bow Tesla",
            combo_type=ComboType.BUILDING_SIEGE,
            primary_card=Cards.X_BOW,
            support_cards=[Cards.TESLA],
            min_elixir=9,
            max_elixir=10,
            timing_delay=1.0,
            positioning_rules={
                Cards.X_BOW.name: "offensive_position",
                Cards.TESLA.name: "defensive_position"
            },
            success_conditions=["enemy_no_tanks"],
            priority=7
        ),
        
        # Lava Hound + Balão
        ComboDefinition(
            name="LavaLoon",
            combo_type=ComboType.AIR_SWARM,
            primary_card=Cards.LAVA_HOUND,
            support_cards=[Cards.BALLOON],
            min_elixir=12,
            max_elixir=15,
            timing_delay=4.0,
            positioning_rules={
                Cards.LAVA_HOUND.name: "behind_king_tower",
                Cards.BALLOON.name: "same_lane_as_lava"
            },
            success_conditions=["lava_hound_crosses_bridge"],
            priority=8
        )
    ]
    
    @classmethod
    def get_available_combos(cls, deck: List[Cards]) -> List[ComboDefinition]:
        """Retorna combos disponíveis baseado no deck"""
        available = []
        deck_set = set(deck)
        
        for combo in cls.COMBOS:
            # Verificar se temos a carta principal
            if combo.primary_card not in deck_set:
                continue
                
            # Verificar se temos pelo menos uma carta de suporte
            has_support = any(support in deck_set for support in combo.support_cards)
            if not has_support:
                continue
                
            available.append(combo)
        
        # Ordenar por prioridade
        available.sort(key=lambda c: c.priority, reverse=True)
        return available


class ComboManager:
    """Gerencia execução de combos e coordenação entre cartas"""
    
    def __init__(self, deck: List[Cards]):
        self.deck = deck
        self.available_combos = ComboDatabase.get_available_combos(deck)
        self.active_combos: List[ActiveCombo] = []
        self.combo_history: List[str] = []
        self.last_combo_time = 0.0
        
    def evaluate_combo_opportunities(self, game_state: GameStateInfo, 
                                   cards_in_hand: List[Cards]) -> Optional[ComboDefinition]:
        """Avalia oportunidades de combo baseado no estado atual"""
        
        # Não iniciar combo se estamos defendendo ameaça crítica
        if game_state.should_defend and game_state.get_primary_threat():
            primary_threat = game_state.get_primary_threat()
            if primary_threat.threat_level.value >= 3:
                return None
        
        # Avaliar cada combo disponível
        best_combo = None
        best_score = 0.0
        
        for combo in self.available_combos:
            score = self._evaluate_combo_score(combo, game_state, cards_in_hand)
            if score > best_score and score >= 0.6:  # Threshold mínimo
                best_score = score
                best_combo = combo
        
        return best_combo
    
    def _evaluate_combo_score(self, combo: ComboDefinition, 
                            game_state: GameStateInfo, 
                            cards_in_hand: List[Cards]) -> float:
        """Calcula score de viabilidade de um combo"""
        score = 0.0
        
        # 1. Verificar se temos as cartas necessárias
        if combo.primary_card not in cards_in_hand:
            return 0.0
        
        support_available = sum(1 for card in combo.support_cards if card in cards_in_hand)
        if support_available == 0:
            return 0.0
        
        score += 0.3  # Base score por ter cartas
        
        # 2. Verificar elixir
        if game_state.our_elixir >= combo.min_elixir:
            score += 0.2
            if game_state.our_elixir >= combo.max_elixir:
                score += 0.1  # Bonus por ter elixir extra
        else:
            return 0.0  # Não temos elixir suficiente
        
        # 3. Avaliar timing baseado no tipo de combo
        if combo.combo_type == ComboType.COUNTER_PUSH:
            if game_state.enemy_elixir_deficit >= 4:
                score += 0.3
        elif combo.combo_type == ComboType.TANK_SUPPORT:
            if game_state.game_mode in ["NEUTRAL", "ATTACK"]:
                score += 0.2
        elif combo.combo_type == ComboType.QUICK_CYCLE:
            if game_state.enemy_elixir_deficit >= 2:
                score += 0.4
        
        # 4. Verificar condições de sucesso
        success_bonus = self._check_success_conditions(combo, game_state)
        score += success_bonus * 0.2
        
        # 5. Penalizar se combo foi usado recentemente
        if combo.name in self.combo_history[-3:]:  # Últimos 3 combos
            score *= 0.7
        
        return min(score, 1.0)
    
    def _check_success_conditions(self, combo: ComboDefinition, 
                                game_state: GameStateInfo) -> float:
        """Verifica condições de sucesso do combo"""
        conditions_met = 0
        total_conditions = len(combo.success_conditions)
        
        for condition in combo.success_conditions:
            if condition == "enemy_low_elixir" and game_state.enemy_elixir_deficit >= 3:
                conditions_met += 1
            elif condition == "enemy_no_tanks":
                has_tanks = any(t.card_name.lower() in ['giant', 'golem', 'pekka'] 
                              for t in game_state.threats)
                if not has_tanks:
                    conditions_met += 1
            elif condition in ["giant_crosses_bridge", "golem_crosses_bridge", "lava_hound_crosses_bridge"]:
                # Estas condições são verificadas durante a execução
                conditions_met += 0.5  # Assumir parcialmente verdadeiro
        
        return conditions_met / total_conditions if total_conditions > 0 else 1.0
    
    def start_combo(self, combo: ComboDefinition, current_time: float) -> ActiveCombo:
        """Inicia execução de um combo"""
        active_combo = ActiveCombo(
            definition=combo,
            cards_played=[],
            start_time=current_time,
            expected_next_card=combo.primary_card,
            next_card_timing=current_time,
            is_complete=False,
            success_probability=0.8
        )
        
        self.active_combos.append(active_combo)
        self.last_combo_time = current_time
        return active_combo
    
    def get_next_combo_action(self, current_time: float) -> Optional[Tuple[Cards, str, Tuple[int, int]]]:
        """Retorna a próxima ação de combo (carta, posição, coordenadas)"""
        for combo in self.active_combos:
            if combo.is_complete:
                continue
                
            # Verificar se é hora de jogar a próxima carta
            if current_time >= combo.next_card_timing and combo.expected_next_card:
                card = combo.expected_next_card
                position_rule = combo.definition.positioning_rules.get(card.name, "default")
                coordinates = self._get_position_coordinates(position_rule, combo)
                
                # Atualizar combo
                combo.cards_played.append(card)
                self._update_combo_state(combo, current_time)
                
                return card, position_rule, coordinates
        
        return None
    
    def _get_position_coordinates(self, position_rule: str, combo: ActiveCombo) -> Tuple[int, int]:
        """Converte regra de posicionamento em coordenadas"""
        position_map = {
            "behind_king_tower": (9, 4),
            "bridge": (9, 7),
            "behind_giant": (9, 6),
            "behind_giant_when_crossing": (9, 8),
            "in_front_of_hog": (9, 8),
            "offensive_position": (9, 10),
            "defensive_position": (9, 5),
            "same_lane_as_lava": (9, 6),
            "default": (9, 7)
        }
        
        return position_map.get(position_rule, (9, 7))
    
    def _update_combo_state(self, combo: ActiveCombo, current_time: float):
        """Atualiza estado do combo após jogar uma carta"""
        remaining_support = [card for card in combo.definition.support_cards 
                           if card not in combo.cards_played]
        
        if remaining_support:
            combo.expected_next_card = remaining_support[0]
            combo.next_card_timing = current_time + combo.definition.timing_delay
        else:
            combo.expected_next_card = None
            combo.is_complete = True
            self.combo_history.append(combo.definition.name)
    
    def cleanup_completed_combos(self):
        """Remove combos completados da lista ativa"""
        self.active_combos = [c for c in self.active_combos if not c.is_complete]
    
    def has_active_combo(self) -> bool:
        """Verifica se há algum combo ativo"""
        return len([c for c in self.active_combos if not c.is_complete]) > 0
    
    def get_combo_priority_boost(self, card: Cards) -> float:
        """Retorna boost de prioridade se a carta faz parte de um combo ativo"""
        for combo in self.active_combos:
            if combo.is_complete:
                continue
                
            if card == combo.expected_next_card:
                return 2.0  # Alto boost para próxima carta do combo
            elif card in combo.definition.support_cards:
                return 1.5  # Boost moderado para cartas de suporte
        
        return 1.0  # Sem boost

