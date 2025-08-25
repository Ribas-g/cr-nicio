"""
Sistema de Timing Dinâmico de Combos
===================================

Sistema que adapta o timing de combos baseado no contexto do jogo,
estado do oponente e oportunidades táticas.
"""

from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
import time
import math

from clashroyalebuildabot.namespaces.cards import Cards


class TimingContext(Enum):
    """Contextos que afetam o timing"""
    EARLY_GAME = "early_game"           # Primeiros 60 segundos
    MID_GAME = "mid_game"               # 60-180 segundos
    LATE_GAME = "late_game"             # 180+ segundos
    OVERTIME = "overtime"               # Tempo extra
    
    ELIXIR_ADVANTAGE = "elixir_advantage"     # Vantagem de elixir
    ELIXIR_DISADVANTAGE = "elixir_disadvantage" # Desvantagem de elixir
    
    ENEMY_LOW_ELIXIR = "enemy_low_elixir"     # Inimigo com pouco elixir
    ENEMY_HIGH_ELIXIR = "enemy_high_elixir"   # Inimigo com muito elixir
    
    COUNTER_ATTACK = "counter_attack"         # Oportunidade de contra-ataque
    DEFENSIVE_PRESSURE = "defensive_pressure" # Sob pressão defensiva
    
    TOWER_DAMAGE = "tower_damage"             # Torre com pouco HP
    EQUAL_TOWERS = "equal_towers"             # Torres equilibradas


class TimingPriority(Enum):
    """Prioridades de timing"""
    IMMEDIATE = 1.0      # Executar imediatamente
    HIGH = 0.8          # Executar em breve
    MEDIUM = 0.6        # Executar quando conveniente
    LOW = 0.4           # Executar se necessário
    WAIT = 0.2          # Aguardar melhor momento


@dataclass
class TimingWindow:
    """Janela de tempo para execução de combo"""
    start_time: float
    end_time: float
    priority: TimingPriority
    context: TimingContext
    confidence: float
    reason: str


@dataclass
class ComboTiming:
    """Timing específico para um combo"""
    combo_name: str
    cards: List[Cards]
    base_delay: float = 0.5  # Delay base entre cartas
    context_modifiers: Dict[TimingContext, float] = field(default_factory=dict)
    elixir_requirements: int = 8
    optimal_windows: List[TimingWindow] = field(default_factory=list)
    
    def get_adjusted_delay(self, context: TimingContext) -> float:
        """Retorna delay ajustado para o contexto"""
        modifier = self.context_modifiers.get(context, 1.0)
        return self.base_delay * modifier


class DynamicTimingManager:
    """Gerenciador principal de timing dinâmico"""
    
    def __init__(self):
        # Configurações de timing por combo
        self.combo_timings: Dict[str, ComboTiming] = {}
        self._initialize_combo_timings()
        
        # Estado atual do jogo
        self.game_start_time: float = time.time()
        self.current_contexts: List[TimingContext] = []
        
        # Histórico de execuções
        self.execution_history: List[Tuple[str, float, bool]] = []  # (combo, tempo, sucesso)
        
        # Análise de padrões
        self.success_rates: Dict[str, Dict[TimingContext, float]] = {}
        self.optimal_timing_patterns: Dict[str, List[float]] = {}
        
        # Predições de oportunidades
        self.predicted_windows: List[TimingWindow] = []
        
    def _initialize_combo_timings(self):
        """Inicializa configurações de timing para combos conhecidos"""
        
        # Giant + Musketeer
        self.combo_timings["giant_musketeer"] = ComboTiming(
            combo_name="giant_musketeer",
            cards=[Cards.GIANT, Cards.MUSKETEER],
            base_delay=1.5,  # Esperar Giant avançar um pouco
            context_modifiers={
                TimingContext.EARLY_GAME: 1.2,      # Mais cauteloso
                TimingContext.LATE_GAME: 0.8,       # Mais agressivo
                TimingContext.OVERTIME: 0.6,        # Muito agressivo
                TimingContext.ELIXIR_ADVANTAGE: 0.7, # Aproveitar vantagem
                TimingContext.ENEMY_LOW_ELIXIR: 0.5, # Punir rapidamente
                TimingContext.COUNTER_ATTACK: 0.4,   # Contra-ataque rápido
            },
            elixir_requirements=9
        )
        
        # Hog Rider + Ice Spirit
        self.combo_timings["hog_ice_spirit"] = ComboTiming(
            combo_name="hog_ice_spirit",
            cards=[Cards.HOG_RIDER, Cards.ICE_SPIRIT],
            base_delay=0.3,  # Timing muito rápido
            context_modifiers={
                TimingContext.EARLY_GAME: 1.0,
                TimingContext.LATE_GAME: 0.8,
                TimingContext.OVERTIME: 0.6,
                TimingContext.ELIXIR_ADVANTAGE: 0.9,
                TimingContext.ENEMY_LOW_ELIXIR: 0.2,  # Muito rápido
                TimingContext.COUNTER_ATTACK: 0.1,    # Instantâneo
            },
            elixir_requirements=5
        )
        
        # Golem + Night Witch
        self.combo_timings["golem_night_witch"] = ComboTiming(
            combo_name="golem_night_witch",
            cards=[Cards.GOLEM, Cards.NIGHT_WITCH],
            base_delay=2.0,  # Esperar Golem se posicionar
            context_modifiers={
                TimingContext.EARLY_GAME: 1.5,      # Muito cauteloso
                TimingContext.MID_GAME: 1.0,
                TimingContext.LATE_GAME: 0.8,
                TimingContext.OVERTIME: 1.2,        # Mais cauteloso em overtime
                TimingContext.ELIXIR_ADVANTAGE: 0.8,
                TimingContext.ENEMY_LOW_ELIXIR: 0.6,
            },
            elixir_requirements=12
        )
        
        # LavaLoon
        self.combo_timings["lava_balloon"] = ComboTiming(
            combo_name="lava_balloon",
            cards=[Cards.LAVA_HOUND, Cards.BALLOON],
            base_delay=3.0,  # Esperar Lava Hound avançar
            context_modifiers={
                TimingContext.EARLY_GAME: 1.3,
                TimingContext.LATE_GAME: 0.9,
                TimingContext.OVERTIME: 0.7,
                TimingContext.ELIXIR_ADVANTAGE: 0.8,
                TimingContext.ENEMY_LOW_ELIXIR: 0.6,
                TimingContext.TOWER_DAMAGE: 0.5,     # Aproveitar torre fraca
            },
            elixir_requirements=12
        )
        
        # Spell Bait Combo
        self.combo_timings["goblin_barrel_princess"] = ComboTiming(
            combo_name="goblin_barrel_princess",
            cards=[Cards.PRINCESS, Cards.GOBLIN_BARREL],
            base_delay=1.0,
            context_modifiers={
                TimingContext.EARLY_GAME: 1.2,
                TimingContext.LATE_GAME: 0.8,
                TimingContext.OVERTIME: 0.6,
                TimingContext.ENEMY_LOW_ELIXIR: 0.3,
                TimingContext.COUNTER_ATTACK: 0.4,
            },
            elixir_requirements=6
        )
    
    def update_game_context(self, 
                          game_time: float,
                          our_elixir: int,
                          enemy_elixir: int,
                          our_tower_hp: List[int],
                          enemy_tower_hp: List[int],
                          recent_enemy_plays: List[Cards],
                          elixir_advantage: int):
        """Atualiza contexto atual do jogo"""
        
        self.current_contexts = []
        
        # Contexto temporal
        if game_time < 60:
            self.current_contexts.append(TimingContext.EARLY_GAME)
        elif game_time < 180:
            self.current_contexts.append(TimingContext.MID_GAME)
        elif game_time < 300:
            self.current_contexts.append(TimingContext.LATE_GAME)
        else:
            self.current_contexts.append(TimingContext.OVERTIME)
        
        # Contexto de elixir
        if elixir_advantage >= 3:
            self.current_contexts.append(TimingContext.ELIXIR_ADVANTAGE)
        elif elixir_advantage <= -3:
            self.current_contexts.append(TimingContext.ELIXIR_DISADVANTAGE)
        
        if enemy_elixir <= 3:
            self.current_contexts.append(TimingContext.ENEMY_LOW_ELIXIR)
        elif enemy_elixir >= 8:
            self.current_contexts.append(TimingContext.ENEMY_HIGH_ELIXIR)
        
        # Contexto de torres
        min_our_hp = min(our_tower_hp) if our_tower_hp else 100
        min_enemy_hp = min(enemy_tower_hp) if enemy_tower_hp else 100
        
        if min_our_hp < 500 or min_enemy_hp < 500:
            self.current_contexts.append(TimingContext.TOWER_DAMAGE)
        else:
            self.current_contexts.append(TimingContext.EQUAL_TOWERS)
        
        # Contexto tático
        if len(recent_enemy_plays) > 0 and self._is_counter_attack_opportunity(recent_enemy_plays):
            self.current_contexts.append(TimingContext.COUNTER_ATTACK)
        
        if our_elixir < 5 and enemy_elixir > 7:
            self.current_contexts.append(TimingContext.DEFENSIVE_PRESSURE)
    
    def _is_counter_attack_opportunity(self, recent_plays: List[Cards]) -> bool:
        """Determina se há oportunidade de contra-ataque"""
        
        # Cartas que indicam oportunidade de contra-ataque
        heavy_cards = [Cards.GOLEM, Cards.PEKKA, Cards.ELECTRO_GIANT, Cards.LAVA_HOUND]
        expensive_spells = [Cards.LIGHTNING, Cards.ROCKET, Cards.FIREBALL]
        
        for card in recent_plays[-2:]:  # Últimas 2 cartas
            if card in heavy_cards or card in expensive_spells:
                return True
        
        return False
    
    def calculate_combo_timing(self, combo_name: str, 
                             available_cards: List[Cards],
                             our_elixir: int) -> Optional[Tuple[float, TimingPriority]]:
        """Calcula timing ótimo para um combo específico"""
        
        if combo_name not in self.combo_timings:
            return None
        
        combo_timing = self.combo_timings[combo_name]
        
        # Verificar se temos as cartas necessárias
        if not all(card in available_cards for card in combo_timing.cards):
            return None
        
        # Verificar se temos elixir suficiente
        if our_elixir < combo_timing.elixir_requirements:
            return None
        
        # Calcular delay baseado no contexto atual
        total_delay = combo_timing.base_delay
        context_multiplier = 1.0
        
        for context in self.current_contexts:
            if context in combo_timing.context_modifiers:
                context_multiplier *= combo_timing.context_modifiers[context]
        
        adjusted_delay = total_delay * context_multiplier
        
        # Calcular prioridade baseada no contexto
        priority = self._calculate_combo_priority(combo_name)
        
        return (adjusted_delay, priority)
    
    def _calculate_combo_priority(self, combo_name: str) -> TimingPriority:
        """Calcula prioridade de execução do combo"""
        
        base_priority = 0.6  # Prioridade média
        
        # Ajustes baseados no contexto
        for context in self.current_contexts:
            if context == TimingContext.ENEMY_LOW_ELIXIR:
                base_priority += 0.3
            elif context == TimingContext.COUNTER_ATTACK:
                base_priority += 0.25
            elif context == TimingContext.ELIXIR_ADVANTAGE:
                base_priority += 0.2
            elif context == TimingContext.OVERTIME:
                base_priority += 0.15
            elif context == TimingContext.TOWER_DAMAGE:
                base_priority += 0.1
            elif context == TimingContext.DEFENSIVE_PRESSURE:
                base_priority -= 0.2
            elif context == TimingContext.ELIXIR_DISADVANTAGE:
                base_priority -= 0.3
        
        # Ajustes específicos por combo
        combo_adjustments = {
            "hog_ice_spirit": {
                TimingContext.COUNTER_ATTACK: 0.2,
                TimingContext.ENEMY_LOW_ELIXIR: 0.3
            },
            "giant_musketeer": {
                TimingContext.ELIXIR_ADVANTAGE: 0.2,
                TimingContext.LATE_GAME: 0.1
            },
            "golem_night_witch": {
                TimingContext.EARLY_GAME: -0.3,  # Evitar early game
                TimingContext.OVERTIME: -0.2     # Evitar overtime
            }
        }
        
        if combo_name in combo_adjustments:
            for context in self.current_contexts:
                if context in combo_adjustments[combo_name]:
                    base_priority += combo_adjustments[combo_name][context]
        
        # Converter para enum
        if base_priority >= 0.9:
            return TimingPriority.IMMEDIATE
        elif base_priority >= 0.7:
            return TimingPriority.HIGH
        elif base_priority >= 0.5:
            return TimingPriority.MEDIUM
        elif base_priority >= 0.3:
            return TimingPriority.LOW
        else:
            return TimingPriority.WAIT
    
    def predict_optimal_windows(self, 
                              enemy_elixir_prediction: List[Tuple[float, int]],
                              enemy_card_predictions: List[Tuple[Cards, float]]) -> List[TimingWindow]:
        """Prediz janelas ótimas para execução de combos"""
        
        windows = []
        current_time = time.time()
        
        # Analisar predições de elixir inimigo
        for time_offset, predicted_elixir in enemy_elixir_prediction:
            future_time = current_time + time_offset
            
            if predicted_elixir <= 3:  # Inimigo com pouco elixir
                window = TimingWindow(
                    start_time=future_time,
                    end_time=future_time + 5.0,  # Janela de 5 segundos
                    priority=TimingPriority.HIGH,
                    context=TimingContext.ENEMY_LOW_ELIXIR,
                    confidence=0.8,
                    reason="Enemy predicted to have low elixir"
                )
                windows.append(window)
        
        # Analisar predições de cartas inimigas
        for card, confidence in enemy_card_predictions:
            if confidence > 0.7:
                # Se carta cara for predita, criar janela de contra-ataque
                card_cost = self._estimate_card_cost(card)
                if card_cost >= 6:
                    window = TimingWindow(
                        start_time=current_time + 2.0,  # Após carta ser jogada
                        end_time=current_time + 8.0,
                        priority=TimingPriority.HIGH,
                        context=TimingContext.COUNTER_ATTACK,
                        confidence=confidence,
                        reason=f"Counter-attack opportunity after {card.name}"
                    )
                    windows.append(window)
        
        # Ordenar por prioridade e confiança
        windows.sort(key=lambda w: (w.priority.value, w.confidence), reverse=True)
        
        self.predicted_windows = windows[:5]  # Manter apenas top 5
        return self.predicted_windows
    
    def _estimate_card_cost(self, card: Cards) -> int:
        """Estima custo de elixir de uma carta"""
        cost_mapping = {
            'skeleton_army': 3, 'goblins': 2, 'archers': 3, 'knight': 3,
            'musketeer': 4, 'minipekka': 4, 'valkyrie': 4, 'hog_rider': 4,
            'giant': 5, 'wizard': 5, 'pekka': 7, 'golem': 8,
            'arrows': 3, 'fireball': 4, 'zap': 2, 'lightning': 6,
        }
        return cost_mapping.get(card.name.lower(), 4)
    
    def should_execute_combo_now(self, combo_name: str,
                               available_cards: List[Cards],
                               our_elixir: int) -> Tuple[bool, str]:
        """Determina se deve executar combo agora"""
        
        timing_result = self.calculate_combo_timing(combo_name, available_cards, our_elixir)
        
        if not timing_result:
            return False, "Combo not available or insufficient elixir"
        
        delay, priority = timing_result
        
        # Decisão baseada na prioridade
        if priority == TimingPriority.IMMEDIATE:
            return True, "Immediate execution required"
        elif priority == TimingPriority.HIGH:
            # Verificar se estamos em janela ótima
            current_time = time.time()
            for window in self.predicted_windows:
                if window.start_time <= current_time <= window.end_time:
                    return True, f"Optimal window: {window.reason}"
            return True, "High priority execution"
        elif priority == TimingPriority.MEDIUM:
            # Executar se não há riscos óbvios
            if TimingContext.DEFENSIVE_PRESSURE not in self.current_contexts:
                return True, "Medium priority, safe to execute"
            return False, "Medium priority but under defensive pressure"
        else:
            return False, f"Priority too low: {priority.name}"
    
    def record_combo_execution(self, combo_name: str, success: bool):
        """Registra execução de combo para aprendizado"""
        
        current_time = time.time()
        self.execution_history.append((combo_name, current_time, success))
        
        # Atualizar taxas de sucesso por contexto
        if combo_name not in self.success_rates:
            self.success_rates[combo_name] = {}
        
        for context in self.current_contexts:
            if context not in self.success_rates[combo_name]:
                self.success_rates[combo_name][context] = []
            
            self.success_rates[combo_name][context].append(success)
            
            # Manter apenas últimas 20 execuções por contexto
            if len(self.success_rates[combo_name][context]) > 20:
                self.success_rates[combo_name][context] = \
                    self.success_rates[combo_name][context][-20:]
    
    def get_combo_success_rate(self, combo_name: str, context: TimingContext) -> float:
        """Retorna taxa de sucesso de um combo em um contexto específico"""
        
        if (combo_name not in self.success_rates or 
            context not in self.success_rates[combo_name]):
            return 0.5  # Taxa neutra se não há dados
        
        results = self.success_rates[combo_name][context]
        if not results:
            return 0.5
        
        return sum(results) / len(results)
    
    def adapt_timing_based_on_performance(self):
        """Adapta timing baseado na performance histórica"""
        
        for combo_name, combo_timing in self.combo_timings.items():
            for context in TimingContext:
                success_rate = self.get_combo_success_rate(combo_name, context)
                
                # Ajustar modificadores baseado na taxa de sucesso
                if success_rate < 0.3:  # Taxa muito baixa
                    # Tornar mais conservador
                    if context in combo_timing.context_modifiers:
                        combo_timing.context_modifiers[context] *= 1.2
                    else:
                        combo_timing.context_modifiers[context] = 1.2
                        
                elif success_rate > 0.8:  # Taxa muito alta
                    # Tornar mais agressivo
                    if context in combo_timing.context_modifiers:
                        combo_timing.context_modifiers[context] *= 0.9
                    else:
                        combo_timing.context_modifiers[context] = 0.9
    
    def get_timing_recommendations(self) -> Dict[str, any]:
        """Retorna recomendações de timing atuais"""
        
        recommendations = {
            "current_contexts": [ctx.value for ctx in self.current_contexts],
            "optimal_combos": [],
            "predicted_windows": [],
            "timing_advice": {}
        }
        
        # Avaliar todos os combos disponíveis
        for combo_name in self.combo_timings.keys():
            priority = self._calculate_combo_priority(combo_name)
            
            if priority.value >= 0.6:  # Medium ou maior
                recommendations["optimal_combos"].append({
                    "combo": combo_name,
                    "priority": priority.name,
                    "priority_value": priority.value
                })
        
        # Adicionar janelas preditas
        for window in self.predicted_windows:
            recommendations["predicted_windows"].append({
                "start_time": window.start_time,
                "end_time": window.end_time,
                "priority": window.priority.name,
                "context": window.context.value,
                "confidence": window.confidence,
                "reason": window.reason
            })
        
        # Conselhos gerais de timing
        if TimingContext.ENEMY_LOW_ELIXIR in self.current_contexts:
            recommendations["timing_advice"]["general"] = "Aggressive timing - enemy has low elixir"
        elif TimingContext.DEFENSIVE_PRESSURE in self.current_contexts:
            recommendations["timing_advice"]["general"] = "Conservative timing - under pressure"
        elif TimingContext.ELIXIR_ADVANTAGE in self.current_contexts:
            recommendations["timing_advice"]["general"] = "Moderate aggression - elixir advantage"
        else:
            recommendations["timing_advice"]["general"] = "Standard timing - balanced situation"
        
        return recommendations
    
    def get_available_combos(self, available_cards: List[Cards]) -> List[Dict]:
        """Retorna combos disponíveis com as cartas atuais"""
        
        available_combos = []
        
        for combo_name, combo_timing in self.combo_timings.items():
            # Verificar se temos as cartas necessárias
            if all(card in available_cards for card in combo_timing.cards):
                # Calcular confiança baseada no contexto atual
                confidence = 0.5  # Base
                
                # Ajustar baseado na taxa de sucesso
                for context in self.current_contexts:
                    success_rate = self.get_combo_success_rate(combo_name, context)
                    confidence = max(confidence, success_rate)
                
                # Ajustar baseado na prioridade
                priority = self._calculate_combo_priority(combo_name)
                confidence *= priority.value
                
                available_combos.append({
                    "name": combo_name,
                    "cards": combo_timing.cards,
                    "confidence": confidence,
                    "priority": priority.name,
                    "base_delay": combo_timing.base_delay,
                    "elixir_requirements": combo_timing.elixir_requirements
                })
        
        # Ordenar por confiança
        available_combos.sort(key=lambda x: x["confidence"], reverse=True)
        
        return available_combos
    
    def calculate_optimal_timing(self, cards: List[Cards], units_on_field: List, elixir_advantage: int) -> Dict:
        """Calcula timing ótimo para um conjunto de cartas"""
        
        # Análise básica de timing
        should_execute = True
        delay = 0.5  # Delay padrão
        
        # Ajustar baseado no contexto
        if TimingContext.ENEMY_LOW_ELIXIR in self.current_contexts:
            delay = 0.2  # Executar rapidamente
        elif TimingContext.DEFENSIVE_PRESSURE in self.current_contexts:
            delay = 1.0  # Esperar mais
        elif TimingContext.ELIXIR_ADVANTAGE in self.current_contexts:
            delay = 0.3  # Executar moderadamente rápido
        
        # Ajustar baseado na vantagem de elixir
        if elixir_advantage >= 3:
            delay *= 0.8  # Mais agressivo
        elif elixir_advantage <= -3:
            delay *= 1.3  # Mais conservador
        
        # Verificar se há unidades no campo que podem interferir
        if units_on_field:
            delay += 0.5  # Esperar um pouco mais
        
        return {
            "should_execute": should_execute,
            "delay": max(0.1, delay),
            "confidence": 0.7,
            "reason": "Optimal timing calculated based on context"
        }

