"""
Sistema de Controle de Tempo por Fases
=====================================

Sistema que adapta estratégias e comportamentos baseado na fase atual do jogo,
controlando timing, agressividade e prioridades conforme o tempo passa.
"""

from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
import time
import math

from clashroyalebuildabot.namespaces.cards import Cards


class GamePhase(Enum):
    """Fases do jogo"""
    EARLY_GAME = "early_game"         # 0-60 segundos
    MID_GAME = "mid_game"             # 60-180 segundos  
    LATE_GAME = "late_game"           # 180-300 segundos
    OVERTIME = "overtime"             # 300+ segundos
    SUDDEN_DEATH = "sudden_death"     # Overtime avançado


class PhaseStrategy(Enum):
    """Estratégias por fase"""
    CONSERVATIVE = "conservative"     # Jogo conservador
    BALANCED = "balanced"            # Jogo equilibrado
    AGGRESSIVE = "aggressive"        # Jogo agressivo
    ALL_IN = "all_in"               # Tudo ou nada
    DEFENSIVE = "defensive"          # Puramente defensivo


class PhasePriority(Enum):
    """Prioridades por fase"""
    ELIXIR_ADVANTAGE = "elixir_advantage"     # Ganhar vantagem de elixir
    TOWER_DAMAGE = "tower_damage"             # Causar dano às torres
    CYCLE_CONTROL = "cycle_control"           # Controlar ciclo de cartas
    DEFENSIVE_SETUP = "defensive_setup"       # Configurar defesas
    SPELL_CYCLING = "spell_cycling"           # Ciclar feitiços
    PRESSURE_MAINTAIN = "pressure_maintain"   # Manter pressão constante


@dataclass
class PhaseConfiguration:
    """Configuração de uma fase específica"""
    phase: GamePhase
    strategy: PhaseStrategy
    priorities: List[PhasePriority]
    aggression_level: float  # 0.0 = muito defensivo, 1.0 = muito agressivo
    elixir_spending_rate: float  # Taxa de gasto de elixir
    combo_frequency: float  # Frequência de combos
    risk_tolerance: float  # Tolerância a riscos
    
    # Modificadores específicos
    card_value_modifiers: Dict[str, float] = field(default_factory=dict)
    timing_modifiers: Dict[str, float] = field(default_factory=dict)
    position_modifiers: Dict[str, float] = field(default_factory=dict)


@dataclass
class PhaseTransition:
    """Transição entre fases"""
    from_phase: GamePhase
    to_phase: GamePhase
    trigger_time: float
    transition_actions: List[str]
    strategy_changes: Dict[str, any]


class PhaseController:
    """Controlador principal de fases do jogo"""
    
    def __init__(self):
        # Estado atual
        self.current_phase: GamePhase = GamePhase.EARLY_GAME
        self.game_start_time: float = time.time()
        self.phase_start_time: float = time.time()
        
        # Configurações por fase
        self.phase_configurations = self._initialize_phase_configurations()
        
        # Histórico de fases
        self.phase_history: List[Tuple[GamePhase, float, float]] = []  # fase, início, fim
        
        # Adaptações dinâmicas
        self.dynamic_adjustments: Dict[GamePhase, Dict[str, float]] = {}
        
        # Análise de performance por fase
        self.phase_performance: Dict[GamePhase, List[float]] = {}  # scores de sucesso
        
        # Transições programadas
        self.scheduled_transitions: List[PhaseTransition] = []
        
        # Estado do jogo para decisões
        self.tower_states: Dict[str, int] = {
            "our_left": 100, "our_right": 100, "our_king": 100,
            "enemy_left": 100, "enemy_right": 100, "enemy_king": 100
        }
        
        self.elixir_trends: List[Tuple[float, int]] = []  # (tempo, vantagem_elixir)
        
    def _initialize_phase_configurations(self) -> Dict[GamePhase, PhaseConfiguration]:
        """Inicializa configurações padrão para cada fase"""
        
        configurations = {
            GamePhase.EARLY_GAME: PhaseConfiguration(
                phase=GamePhase.EARLY_GAME,
                strategy=PhaseStrategy.CONSERVATIVE,
                priorities=[
                    PhasePriority.ELIXIR_ADVANTAGE,
                    PhasePriority.DEFENSIVE_SETUP,
                    PhasePriority.CYCLE_CONTROL
                ],
                aggression_level=0.3,
                elixir_spending_rate=0.6,
                combo_frequency=0.4,
                risk_tolerance=0.2,
                card_value_modifiers={
                    "cheap_cards": 1.2,      # Valorizar cartas baratas
                    "expensive_cards": 0.8,  # Desencorajar cartas caras
                    "defensive_cards": 1.1   # Valorizar defesas
                },
                timing_modifiers={
                    "combo_delay": 1.3,      # Combos mais lentos
                    "reaction_time": 1.2     # Reações mais cautelosas
                },
                position_modifiers={
                    "defensive_bias": 1.2,   # Bias defensivo
                    "aggressive_bias": 0.8   # Menos agressividade
                }
            ),
            
            GamePhase.MID_GAME: PhaseConfiguration(
                phase=GamePhase.MID_GAME,
                strategy=PhaseStrategy.BALANCED,
                priorities=[
                    PhasePriority.TOWER_DAMAGE,
                    PhasePriority.PRESSURE_MAINTAIN,
                    PhasePriority.ELIXIR_ADVANTAGE
                ],
                aggression_level=0.6,
                elixir_spending_rate=0.8,
                combo_frequency=0.7,
                risk_tolerance=0.5,
                card_value_modifiers={
                    "combo_cards": 1.2,      # Valorizar combos
                    "win_conditions": 1.3    # Valorizar win conditions
                },
                timing_modifiers={
                    "combo_delay": 1.0,      # Timing normal
                    "reaction_time": 1.0
                },
                position_modifiers={
                    "balanced_approach": 1.0  # Abordagem equilibrada
                }
            ),
            
            GamePhase.LATE_GAME: PhaseConfiguration(
                phase=GamePhase.LATE_GAME,
                strategy=PhaseStrategy.AGGRESSIVE,
                priorities=[
                    PhasePriority.TOWER_DAMAGE,
                    PhasePriority.SPELL_CYCLING,
                    PhasePriority.PRESSURE_MAINTAIN
                ],
                aggression_level=0.8,
                elixir_spending_rate=0.9,
                combo_frequency=0.8,
                risk_tolerance=0.7,
                card_value_modifiers={
                    "damage_spells": 1.4,    # Valorizar feitiços de dano
                    "win_conditions": 1.5,   # Muito valorizar win conditions
                    "defensive_cards": 0.9   # Menos foco em defesa
                },
                timing_modifiers={
                    "combo_delay": 0.8,      # Combos mais rápidos
                    "reaction_time": 0.9     # Reações mais rápidas
                },
                position_modifiers={
                    "aggressive_bias": 1.3,  # Muito agressivo
                    "defensive_bias": 0.8
                }
            ),
            
            GamePhase.OVERTIME: PhaseConfiguration(
                phase=GamePhase.OVERTIME,
                strategy=PhaseStrategy.ALL_IN,
                priorities=[
                    PhasePriority.TOWER_DAMAGE,
                    PhasePriority.SPELL_CYCLING
                ],
                aggression_level=1.0,
                elixir_spending_rate=1.0,
                combo_frequency=0.9,
                risk_tolerance=0.9,
                card_value_modifiers={
                    "damage_spells": 1.6,    # Máxima prioridade para dano
                    "win_conditions": 1.7,   # Máxima prioridade para win conditions
                    "defensive_cards": 0.6   # Mínima prioridade para defesa
                },
                timing_modifiers={
                    "combo_delay": 0.6,      # Combos muito rápidos
                    "reaction_time": 0.7     # Reações muito rápidas
                },
                position_modifiers={
                    "aggressive_bias": 1.5,  # Máxima agressividade
                    "all_in_approach": 1.3
                }
            )
        }
        
        return configurations
    
    def update_game_state(self, 
                         game_time: float,
                         tower_hp: Dict[str, int],
                         elixir_advantage: int,
                         recent_actions: List[str]):
        """Atualiza estado do jogo e verifica transições de fase"""
        
        # Atualizar estado das torres
        self.tower_states.update(tower_hp)
        
        # Registrar tendência de elixir
        current_time = time.time()
        self.elixir_trends.append((current_time, elixir_advantage))
        
        # Manter apenas últimos 30 registros
        if len(self.elixir_trends) > 30:
            self.elixir_trends = self.elixir_trends[-30:]
        
        # Verificar transição de fase
        new_phase = self._determine_current_phase(game_time)
        
        if new_phase != self.current_phase:
            self._transition_to_phase(new_phase)
        
        # Aplicar adaptações dinâmicas
        self._apply_dynamic_adaptations(recent_actions)
    
    def _determine_current_phase(self, game_time: float) -> GamePhase:
        """Determina fase atual baseada no tempo e estado do jogo"""
        
        # Fases baseadas em tempo
        if game_time < 60:
            base_phase = GamePhase.EARLY_GAME
        elif game_time < 180:
            base_phase = GamePhase.MID_GAME
        elif game_time < 300:
            base_phase = GamePhase.LATE_GAME
        else:
            base_phase = GamePhase.OVERTIME
        
        # Modificações baseadas no estado do jogo
        
        # Se alguma torre está muito danificada, acelerar para late game
        min_tower_hp = min([
            self.tower_states["our_left"],
            self.tower_states["our_right"],
            self.tower_states["enemy_left"],
            self.tower_states["enemy_right"]
        ])
        
        if min_tower_hp < 500 and base_phase == GamePhase.MID_GAME:
            return GamePhase.LATE_GAME
        elif min_tower_hp < 200:
            return GamePhase.OVERTIME
        
        # Se há grande desvantagem de elixir consistente, ser mais defensivo
        if len(self.elixir_trends) >= 5:
            recent_advantages = [adv for _, adv in self.elixir_trends[-5:]]
            avg_advantage = sum(recent_advantages) / len(recent_advantages)
            
            if avg_advantage < -3 and base_phase in [GamePhase.LATE_GAME, GamePhase.OVERTIME]:
                # Manter fase atual mas ajustar estratégia
                pass
        
        return base_phase
    
    def _transition_to_phase(self, new_phase: GamePhase):
        """Executa transição para nova fase"""
        
        # Registrar fase anterior
        current_time = time.time()
        if self.current_phase:
            self.phase_history.append((
                self.current_phase,
                self.phase_start_time,
                current_time
            ))
        
        # Atualizar fase atual
        old_phase = self.current_phase
        self.current_phase = new_phase
        self.phase_start_time = current_time
        
        # Executar ações de transição
        self._execute_transition_actions(old_phase, new_phase)
        
        # Log da transição
        print(f"Phase transition: {old_phase.value if old_phase else 'None'} -> {new_phase.value}")
    
    def _execute_transition_actions(self, old_phase: Optional[GamePhase], new_phase: GamePhase):
        """Executa ações específicas da transição"""
        
        transition_actions = {
            (GamePhase.EARLY_GAME, GamePhase.MID_GAME): [
                "increase_aggression",
                "enable_combo_system",
                "start_pressure_plays"
            ],
            (GamePhase.MID_GAME, GamePhase.LATE_GAME): [
                "prioritize_tower_damage",
                "increase_spell_usage",
                "reduce_defensive_focus"
            ],
            (GamePhase.LATE_GAME, GamePhase.OVERTIME): [
                "maximum_aggression",
                "spell_cycle_priority",
                "ignore_elixir_efficiency"
            ]
        }
        
        if old_phase and (old_phase, new_phase) in transition_actions:
            actions = transition_actions[(old_phase, new_phase)]
            
            for action in actions:
                self._apply_transition_action(action)
    
    def _apply_transition_action(self, action: str):
        """Aplica uma ação específica de transição"""
        
        config = self.phase_configurations[self.current_phase]
        
        if action == "increase_aggression":
            config.aggression_level = min(1.0, config.aggression_level + 0.2)
        
        elif action == "enable_combo_system":
            config.combo_frequency = min(1.0, config.combo_frequency + 0.3)
        
        elif action == "prioritize_tower_damage":
            config.card_value_modifiers["damage_spells"] = 1.4
            config.card_value_modifiers["win_conditions"] = 1.5
        
        elif action == "maximum_aggression":
            config.aggression_level = 1.0
            config.risk_tolerance = 1.0
        
        elif action == "spell_cycle_priority":
            if PhasePriority.SPELL_CYCLING not in config.priorities:
                config.priorities.insert(0, PhasePriority.SPELL_CYCLING)
    
    def _apply_dynamic_adaptations(self, recent_actions: List[str]):
        """Aplica adaptações dinâmicas baseadas em ações recentes"""
        
        # Analisar sucesso de ações recentes
        success_indicators = ["tower_damage", "successful_defense", "elixir_advantage_gained"]
        failure_indicators = ["tower_lost", "elixir_disadvantage", "failed_attack"]
        
        success_count = sum(1 for action in recent_actions if action in success_indicators)
        failure_count = sum(1 for action in recent_actions if action in failure_indicators)
        
        if len(recent_actions) > 0:
            success_rate = success_count / len(recent_actions)
            
            # Ajustar configuração baseada no sucesso
            config = self.phase_configurations[self.current_phase]
            
            if success_rate > 0.7:  # Alto sucesso
                # Ser mais agressivo
                config.aggression_level = min(1.0, config.aggression_level + 0.1)
                config.risk_tolerance = min(1.0, config.risk_tolerance + 0.1)
            
            elif success_rate < 0.3:  # Baixo sucesso
                # Ser mais conservador
                config.aggression_level = max(0.1, config.aggression_level - 0.1)
                config.risk_tolerance = max(0.1, config.risk_tolerance - 0.1)
    
    def get_current_configuration(self) -> PhaseConfiguration:
        """Retorna configuração da fase atual"""
        return self.phase_configurations[self.current_phase]
    
    def calculate_card_value_modifier(self, card: Cards, context: str = "neutral") -> float:
        """Calcula modificador de valor para uma carta na fase atual"""
        
        config = self.get_current_configuration()
        base_modifier = 1.0
        
        # Aplicar modificadores da fase
        card_name = card.name.lower()
        
        # Modificadores por tipo de carta
        if self._is_cheap_card(card):
            base_modifier *= config.card_value_modifiers.get("cheap_cards", 1.0)
        elif self._is_expensive_card(card):
            base_modifier *= config.card_value_modifiers.get("expensive_cards", 1.0)
        
        if self._is_defensive_card(card):
            base_modifier *= config.card_value_modifiers.get("defensive_cards", 1.0)
        elif self._is_win_condition(card):
            base_modifier *= config.card_value_modifiers.get("win_conditions", 1.0)
        elif self._is_damage_spell(card):
            base_modifier *= config.card_value_modifiers.get("damage_spells", 1.0)
        
        # Modificadores por contexto
        if context == "attack":
            base_modifier *= config.position_modifiers.get("aggressive_bias", 1.0)
        elif context == "defense":
            base_modifier *= config.position_modifiers.get("defensive_bias", 1.0)
        
        return base_modifier
    
    def calculate_timing_modifier(self, action_type: str) -> float:
        """Calcula modificador de timing para uma ação"""
        
        config = self.get_current_configuration()
        
        timing_modifiers = {
            "combo_execution": config.timing_modifiers.get("combo_delay", 1.0),
            "defensive_reaction": config.timing_modifiers.get("reaction_time", 1.0),
            "spell_timing": config.timing_modifiers.get("spell_delay", 1.0),
            "counter_attack": config.timing_modifiers.get("counter_delay", 1.0)
        }
        
        return timing_modifiers.get(action_type, 1.0)
    
    def should_execute_action(self, action_type: str, risk_level: float) -> bool:
        """Determina se deve executar uma ação baseada na fase atual"""
        
        config = self.get_current_configuration()
        
        # Verificar tolerância a risco
        if risk_level > config.risk_tolerance:
            return False
        
        # Verificar prioridades da fase
        action_priorities = {
            "elixir_spending": PhasePriority.ELIXIR_ADVANTAGE,
            "tower_attack": PhasePriority.TOWER_DAMAGE,
            "defensive_play": PhasePriority.DEFENSIVE_SETUP,
            "spell_cycle": PhasePriority.SPELL_CYCLING,
            "combo_execution": PhasePriority.PRESSURE_MAINTAIN
        }
        
        if action_type in action_priorities:
            required_priority = action_priorities[action_type]
            if required_priority not in config.priorities:
                return False
        
        # Verificar estratégia da fase
        if config.strategy == PhaseStrategy.DEFENSIVE and action_type in ["tower_attack", "aggressive_combo"]:
            return False
        elif config.strategy == PhaseStrategy.ALL_IN and action_type in ["defensive_play", "elixir_conservation"]:
            return False
        
        return True
    
    def get_phase_recommendations(self) -> Dict[str, any]:
        """Retorna recomendações baseadas na fase atual"""
        
        config = self.get_current_configuration()
        
        recommendations = {
            "current_phase": self.current_phase.value,
            "strategy": config.strategy.value,
            "aggression_level": config.aggression_level,
            "priorities": [p.value for p in config.priorities],
            "tactical_advice": [],
            "timing_advice": {},
            "card_preferences": {}
        }
        
        # Conselhos táticos baseados na fase
        if self.current_phase == GamePhase.EARLY_GAME:
            recommendations["tactical_advice"] = [
                "Focus on elixir advantage and cycle control",
                "Avoid expensive commitments",
                "Set up defensive structures",
                "Learn opponent's deck"
            ]
        
        elif self.current_phase == GamePhase.MID_GAME:
            recommendations["tactical_advice"] = [
                "Start applying pressure with combos",
                "Look for tower damage opportunities",
                "Maintain elixir advantage",
                "Adapt to opponent's strategy"
            ]
        
        elif self.current_phase == GamePhase.LATE_GAME:
            recommendations["tactical_advice"] = [
                "Prioritize tower damage",
                "Use spells for guaranteed damage",
                "Take calculated risks",
                "Prepare for overtime"
            ]
        
        elif self.current_phase == GamePhase.OVERTIME:
            recommendations["tactical_advice"] = [
                "Maximum aggression - go for the win",
                "Cycle spells for tower damage",
                "Ignore elixir efficiency",
                "Take any damage opportunity"
            ]
        
        # Conselhos de timing
        recommendations["timing_advice"] = {
            "combo_speed": "fast" if config.aggression_level > 0.7 else "normal",
            "reaction_time": "quick" if config.aggression_level > 0.6 else "careful",
            "spell_usage": "frequent" if PhasePriority.SPELL_CYCLING in config.priorities else "selective"
        }
        
        # Preferências de cartas
        recommendations["card_preferences"] = {
            "cheap_cards": config.card_value_modifiers.get("cheap_cards", 1.0),
            "expensive_cards": config.card_value_modifiers.get("expensive_cards", 1.0),
            "win_conditions": config.card_value_modifiers.get("win_conditions", 1.0),
            "damage_spells": config.card_value_modifiers.get("damage_spells", 1.0),
            "defensive_cards": config.card_value_modifiers.get("defensive_cards", 1.0)
        }
        
        return recommendations
    
    def _is_cheap_card(self, card: Cards) -> bool:
        """Verifica se é carta barata (≤3 elixir)"""
        cheap_cards = [Cards.SKELETONS, Cards.ICE_SPIRIT, Cards.BATS, Cards.GOBLINS, 
                      Cards.ARCHERS, Cards.KNIGHT, Cards.ARROWS, Cards.ZAP]
        return card in cheap_cards
    
    def _is_expensive_card(self, card: Cards) -> bool:
        """Verifica se é carta cara (≥6 elixir)"""
        expensive_cards = [Cards.PEKKA, Cards.GOLEM, Cards.ELECTRO_GIANT, 
                          Cards.LAVA_HOUND, Cards.LIGHTNING, Cards.ROCKET]
        return card in expensive_cards
    
    def _is_defensive_card(self, card: Cards) -> bool:
        """Verifica se é carta defensiva"""
        defensive_cards = [Cards.CANNON, Cards.TESLA, Cards.INFERNO_TOWER, 
                          Cards.TOMBSTONE, Cards.SKELETON_ARMY]
        return card in defensive_cards
    
    def _is_win_condition(self, card: Cards) -> bool:
        """Verifica se é win condition"""
        win_conditions = [Cards.HOG_RIDER, Cards.GIANT, Cards.BALLOON, 
                         Cards.X_BOW, Cards.MORTAR, Cards.GOBLIN_BARREL]
        return card in win_conditions
    
    def _is_damage_spell(self, card: Cards) -> bool:
        """Verifica se é feitiço de dano"""
        damage_spells = [Cards.FIREBALL, Cards.ROCKET, Cards.LIGHTNING, 
                        Cards.ARROWS, Cards.ZAP, Cards.POISON]
        return card in damage_spells
    
    def record_phase_performance(self, success_score: float):
        """Registra performance da fase atual"""
        
        if self.current_phase not in self.phase_performance:
            self.phase_performance[self.current_phase] = []
        
        self.phase_performance[self.current_phase].append(success_score)
        
        # Manter apenas últimos 20 registros por fase
        if len(self.phase_performance[self.current_phase]) > 20:
            self.phase_performance[self.current_phase] = \
                self.phase_performance[self.current_phase][-20:]
    
    def optimize_phase_configurations(self):
        """Otimiza configurações baseado na performance histórica"""
        
        for phase, scores in self.phase_performance.items():
            if len(scores) >= 10:  # Dados suficientes
                avg_score = sum(scores) / len(scores)
                
                config = self.phase_configurations[phase]
                
                if avg_score > 0.7:  # Performance boa
                    # Manter configuração atual ou ser ligeiramente mais agressivo
                    config.aggression_level = min(1.0, config.aggression_level + 0.05)
                
                elif avg_score < 0.3:  # Performance ruim
                    # Ser mais conservador
                    config.aggression_level = max(0.1, config.aggression_level - 0.1)
                    config.risk_tolerance = max(0.1, config.risk_tolerance - 0.1)
    
    def get_time_remaining_in_phase(self) -> float:
        """Retorna tempo restante na fase atual (estimativa)"""
        
        current_time = time.time()
        game_time = current_time - self.game_start_time
        
        phase_durations = {
            GamePhase.EARLY_GAME: 60,
            GamePhase.MID_GAME: 120,  # 60-180
            GamePhase.LATE_GAME: 120,  # 180-300
            GamePhase.OVERTIME: float('inf')  # Sem limite
        }
        
        if self.current_phase == GamePhase.EARLY_GAME:
            return max(0, 60 - game_time)
        elif self.current_phase == GamePhase.MID_GAME:
            return max(0, 180 - game_time)
        elif self.current_phase == GamePhase.LATE_GAME:
            return max(0, 300 - game_time)
        else:  # OVERTIME
            return float('inf')
    
    def is_phase_transition_imminent(self, threshold_seconds: float = 10.0) -> bool:
        """Verifica se transição de fase é iminente"""
        
        time_remaining = self.get_time_remaining_in_phase()
        return time_remaining <= threshold_seconds and time_remaining != float('inf')
    
    def get_current_phase(self, game_time: float) -> GamePhase:
        """Determina a fase atual baseada no tempo de jogo"""
        
        if game_time <= 60:
            return GamePhase.EARLY_GAME
        elif game_time <= 180:
            return GamePhase.MID_GAME
        elif game_time <= 300:
            return GamePhase.LATE_GAME
        else:
            return GamePhase.OVERTIME

