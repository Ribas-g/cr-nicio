"""
Sistema Avançado de Controle de Elixir
=====================================

Sistema que monitora e controla precisamente o elixir próprio e do oponente,
criando oportunidades táticas baseadas em vantagens/desvantagens de elixir.
"""

from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
import time
import math
from collections import deque

from clashroyalebuildabot.namespaces.cards import Cards


class ElixirState(Enum):
    """Estados de elixir"""
    CRITICAL = "critical"     # 0-2 elixir
    LOW = "low"              # 3-4 elixir
    MEDIUM = "medium"        # 5-6 elixir
    HIGH = "high"            # 7-8 elixir
    FULL = "full"            # 9-10 elixir


class ElixirStrategy(Enum):
    """Estratégias de elixir"""
    AGGRESSIVE_SPEND = "aggressive_spend"     # Gastar agressivamente
    CONSERVATIVE = "conservative"             # Conservar elixir
    CYCLE_FAST = "cycle_fast"                # Ciclar rapidamente
    WAIT_FOR_ADVANTAGE = "wait_for_advantage" # Esperar vantagem
    PUNISH_OPPONENT = "punish_opponent"       # Punir oponente
    EMERGENCY_DEFENSE = "emergency_defense"   # Defesa de emergência


class ElixirOpportunity(Enum):
    """Oportunidades baseadas em elixir"""
    COUNTER_ATTACK = "counter_attack"         # Contra-ataque
    HEAVY_PUSH = "heavy_push"                # Push pesado
    CYCLE_PRESSURE = "cycle_pressure"         # Pressão por ciclo
    SPELL_PUNISHMENT = "spell_punishment"     # Punir com feitiços
    DEFENSIVE_SETUP = "defensive_setup"       # Configurar defesa


@dataclass
class ElixirAdvantage:
    """Vantagem de elixir em um momento específico"""
    timestamp: float
    our_elixir: int
    enemy_elixir: int
    advantage: int  # Positivo = nossa vantagem, negativo = desvantagem
    confidence: float
    duration_estimate: float  # Quanto tempo a vantagem deve durar
    opportunity: ElixirOpportunity


@dataclass
class ElixirPrediction:
    """Predição de elixir futuro"""
    time_offset: float  # Segundos no futuro
    predicted_our_elixir: int
    predicted_enemy_elixir: int
    predicted_advantage: int
    confidence: float
    recommended_action: ElixirStrategy


class AdvancedElixirController:
    """Controlador avançado de elixir"""
    
    def __init__(self):
        # Estado atual
        self.our_current_elixir: int = 5
        self.enemy_current_elixir: int = 5
        self.last_update_time: float = time.time()
        
        # Histórico de elixir
        self.elixir_history: deque = deque(maxlen=100)  # (timestamp, our_elixir, enemy_elixir)
        self.spending_history: deque = deque(maxlen=50)  # (timestamp, amount, player)
        
        # Rastreamento de regeneração
        self.elixir_generation_rate: float = 1.0  # 1 elixir por segundo
        self.double_elixir_active: bool = False
        self.double_elixir_start_time: Optional[float] = None
        
        # Análise de padrões
        self.enemy_spending_patterns: Dict[str, List[int]] = {}  # contexto -> gastos
        self.our_spending_efficiency: Dict[str, float] = {}     # ação -> eficiência
        
        # Predições e oportunidades
        self.current_advantages: List[ElixirAdvantage] = []
        self.predicted_states: List[ElixirPrediction] = []
        
        # Estratégias adaptativas
        self.current_strategy: ElixirStrategy = ElixirStrategy.CONSERVATIVE
        self.strategy_success_rates: Dict[ElixirStrategy, List[bool]] = {}
        
        # Controle de timing
        self.optimal_spending_windows: List[Tuple[float, float, str]] = []  # (start, end, reason)
        self.elixir_leak_prevention: bool = True
        
        # Análise de valor esperado
        self.card_value_analysis: Dict[Cards, Dict[str, float]] = {}  # carta -> contexto -> valor
        self.combo_elixir_efficiency: Dict[str, float] = {}
    
    def update_elixir_state(self, our_elixir: int, 
                           enemy_cards_played: List[Tuple[Cards, float]],
                           our_cards_played: List[Tuple[Cards, float]],
                           game_time: float):
        """Atualiza estado completo de elixir"""
        
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        # Atualizar nosso elixir
        self.our_current_elixir = our_elixir
        
        # Calcular elixir inimigo baseado em cartas jogadas
        self._update_enemy_elixir(enemy_cards_played, time_diff)
        
        # Registrar no histórico
        self.elixir_history.append((current_time, our_elixir, self.enemy_current_elixir))
        
        # Registrar gastos
        for card, timestamp in our_cards_played:
            cost = self._estimate_card_cost(card)
            self.spending_history.append((timestamp, cost, "us"))
        
        for card, timestamp in enemy_cards_played:
            cost = self._estimate_card_cost(card)
            self.spending_history.append((timestamp, cost, "enemy"))
        
        # Detectar double elixir
        self._detect_double_elixir(game_time)
        
        # Analisar vantagens atuais
        self._analyze_current_advantages()
        
        # Gerar predições
        self._generate_elixir_predictions()
        
        # Atualizar estratégia
        self._update_optimal_strategy()
        
        self.last_update_time = current_time
    
    def _update_enemy_elixir(self, enemy_cards: List[Tuple[Cards, float]], time_diff: float):
        """Atualiza estimativa de elixir inimigo"""
        
        # Regeneração natural
        generation_rate = self.elixir_generation_rate
        if self.double_elixir_active:
            generation_rate *= 2
        
        elixir_generated = min(10 - self.enemy_current_elixir, time_diff * generation_rate)
        self.enemy_current_elixir = min(10, self.enemy_current_elixir + elixir_generated)
        
        # Subtrair elixir gasto
        for card, timestamp in enemy_cards:
            cost = self._estimate_card_cost(card)
            self.enemy_current_elixir = max(0, self.enemy_current_elixir - cost)
    
    def _estimate_card_cost(self, card: Cards) -> int:
        """Estima custo de elixir de uma carta"""
        cost_mapping = {
            # Cartas baratas (1-3)
            'skeletons': 1, 'ice_spirit': 1, 'heal_spirit': 1,
            'bats': 2, 'spear_goblins': 2, 'goblins': 2, 'zap': 2,
            'skeleton_army': 3, 'archers': 3, 'knight': 3, 'arrows': 3,
            'cannon': 3, 'tombstone': 3, 'bomber': 3,
            
            # Cartas médias (4-5)
            'musketeer': 4, 'minipekka': 4, 'valkyrie': 4, 'hog_rider': 4,
            'fireball': 4, 'tesla': 4, 'ice_golem': 2, 'poison': 4,
            'giant': 5, 'wizard': 5, 'balloon': 5, 'inferno_tower': 5,
            
            # Cartas caras (6+)
            'lightning': 6, 'rocket': 6, 'pekka': 7, 'golem': 8,
            'electro_giant': 8, 'lava_hound': 7, 'mega_knight': 7
        }
        
        card_name = card.name.lower()
        return cost_mapping.get(card_name, 4)  # Default 4
    
    def _detect_double_elixir(self, game_time: float):
        """Detecta início do double elixir"""
        
        if game_time >= 120 and not self.double_elixir_active:  # 2 minutos
            self.double_elixir_active = True
            self.double_elixir_start_time = time.time()
            self.elixir_generation_rate = 2.0
    
    def _analyze_current_advantages(self):
        """Analisa vantagens de elixir atuais"""
        
        current_time = time.time()
        advantage = self.our_current_elixir - self.enemy_current_elixir
        
        # Determinar oportunidade baseada na vantagem
        opportunity = None
        confidence = 0.5
        duration = 5.0
        
        if advantage >= 4:  # Grande vantagem
            opportunity = ElixirOpportunity.HEAVY_PUSH
            confidence = 0.9
            duration = 8.0
        elif advantage >= 2:  # Vantagem moderada
            opportunity = ElixirOpportunity.COUNTER_ATTACK
            confidence = 0.8
            duration = 6.0
        elif advantage <= -4:  # Grande desvantagem
            opportunity = ElixirOpportunity.DEFENSIVE_SETUP
            confidence = 0.9
            duration = 10.0
        elif advantage <= -2:  # Desvantagem moderada
            opportunity = ElixirOpportunity.CYCLE_PRESSURE
            confidence = 0.7
            duration = 5.0
        
        if opportunity:
            elixir_advantage = ElixirAdvantage(
                timestamp=current_time,
                our_elixir=self.our_current_elixir,
                enemy_elixir=self.enemy_current_elixir,
                advantage=advantage,
                confidence=confidence,
                duration_estimate=duration,
                opportunity=opportunity
            )
            
            # Adicionar à lista (remover antigas)
            self.current_advantages = [adv for adv in self.current_advantages 
                                     if current_time - adv.timestamp < adv.duration_estimate]
            self.current_advantages.append(elixir_advantage)
    
    def _generate_elixir_predictions(self):
        """Gera predições de elixir futuro"""
        
        self.predicted_states = []
        current_time = time.time()
        
        # Predições para próximos 15 segundos
        for seconds_ahead in [3, 6, 9, 12, 15]:
            predicted_our = self._predict_our_elixir(seconds_ahead)
            predicted_enemy = self._predict_enemy_elixir(seconds_ahead)
            predicted_advantage = predicted_our - predicted_enemy
            
            # Calcular confiança baseada na distância temporal
            confidence = max(0.3, 1.0 - (seconds_ahead / 20.0))
            
            # Determinar ação recomendada
            recommended_action = self._determine_recommended_action(
                predicted_our, predicted_enemy, predicted_advantage
            )
            
            prediction = ElixirPrediction(
                time_offset=seconds_ahead,
                predicted_our_elixir=predicted_our,
                predicted_enemy_elixir=predicted_enemy,
                predicted_advantage=predicted_advantage,
                confidence=confidence,
                recommended_action=recommended_action
            )
            
            self.predicted_states.append(prediction)
    
    def _predict_our_elixir(self, seconds_ahead: float) -> int:
        """Prediz nosso elixir em X segundos"""
        
        generation_rate = self.elixir_generation_rate
        if self.double_elixir_active:
            generation_rate = 2.0
        
        # Regeneração natural
        predicted = min(10, self.our_current_elixir + (seconds_ahead * generation_rate))
        
        # Considerar gastos planejados (estimativa conservadora)
        if self.current_strategy == ElixirStrategy.AGGRESSIVE_SPEND:
            predicted = max(0, predicted - 4)  # Gastar ~4 elixir
        elif self.current_strategy == ElixirStrategy.CYCLE_FAST:
            predicted = max(0, predicted - 2)  # Gastar ~2 elixir
        
        return int(predicted)
    
    def _predict_enemy_elixir(self, seconds_ahead: float) -> int:
        """Prediz elixir inimigo em X segundos"""
        
        generation_rate = self.elixir_generation_rate
        if self.double_elixir_active:
            generation_rate = 2.0
        
        # Regeneração natural
        predicted = min(10, self.enemy_current_elixir + (seconds_ahead * generation_rate))
        
        # Analisar padrões de gasto inimigo
        recent_spending = [spend for timestamp, spend, player in self.spending_history 
                          if player == "enemy" and time.time() - timestamp < 30]
        
        if recent_spending:
            avg_spending_rate = sum(recent_spending) / len(recent_spending)
            predicted_spending = avg_spending_rate * (seconds_ahead / 10.0)  # Normalizar
            predicted = max(0, predicted - predicted_spending)
        
        return int(predicted)
    
    def _determine_recommended_action(self, our_elixir: int, enemy_elixir: int, 
                                    advantage: int) -> ElixirStrategy:
        """Determina ação recomendada baseada em predição"""
        
        if advantage >= 4:
            return ElixirStrategy.AGGRESSIVE_SPEND
        elif advantage >= 2:
            return ElixirStrategy.PUNISH_OPPONENT
        elif advantage <= -4:
            return ElixirStrategy.EMERGENCY_DEFENSE
        elif advantage <= -2:
            return ElixirStrategy.CONSERVATIVE
        elif our_elixir >= 8:
            return ElixirStrategy.CYCLE_FAST  # Evitar leak
        else:
            return ElixirStrategy.WAIT_FOR_ADVANTAGE
    
    def _update_optimal_strategy(self):
        """Atualiza estratégia ótima baseada no estado atual"""
        
        # Analisar situação atual
        current_advantage = self.our_current_elixir - self.enemy_current_elixir
        our_state = self._get_elixir_state(self.our_current_elixir)
        enemy_state = self._get_elixir_state(self.enemy_current_elixir)
        
        # Determinar estratégia baseada em múltiplos fatores
        if current_advantage >= 3 and our_state in [ElixirState.HIGH, ElixirState.FULL]:
            self.current_strategy = ElixirStrategy.AGGRESSIVE_SPEND
        elif current_advantage <= -3 and our_state == ElixirState.LOW:
            self.current_strategy = ElixirStrategy.EMERGENCY_DEFENSE
        elif our_state == ElixirState.FULL:
            self.current_strategy = ElixirStrategy.CYCLE_FAST
        elif enemy_state == ElixirState.LOW and our_state >= ElixirState.MEDIUM:
            self.current_strategy = ElixirStrategy.PUNISH_OPPONENT
        elif current_advantage < 0:
            self.current_strategy = ElixirStrategy.CONSERVATIVE
        else:
            self.current_strategy = ElixirStrategy.WAIT_FOR_ADVANTAGE
    
    def _get_elixir_state(self, elixir: int) -> ElixirState:
        """Converte valor de elixir para estado"""
        
        if elixir <= 2:
            return ElixirState.CRITICAL
        elif elixir <= 4:
            return ElixirState.LOW
        elif elixir <= 6:
            return ElixirState.MEDIUM
        elif elixir <= 8:
            return ElixirState.HIGH
        else:
            return ElixirState.FULL
    
    def calculate_card_value(self, card: Cards, context: str = "neutral") -> float:
        """Calcula valor esperado de uma carta no contexto atual"""
        
        base_cost = self._estimate_card_cost(card)
        
        # Valor base (custo normalizado)
        base_value = base_cost / 10.0
        
        # Modificadores contextuais
        context_multipliers = {
            "attack": 1.2,
            "defense": 1.1,
            "counter_attack": 1.5,
            "emergency": 0.8,  # Menos eficiente sob pressão
            "advantage": 1.3,  # Mais eficiente com vantagem
            "disadvantage": 0.9
        }
        
        multiplier = context_multipliers.get(context, 1.0)
        
        # Modificadores baseados no estado de elixir
        our_state = self._get_elixir_state(self.our_current_elixir)
        enemy_state = self._get_elixir_state(self.enemy_current_elixir)
        
        if our_state == ElixirState.FULL and base_cost <= 3:
            multiplier *= 1.3  # Cartas baratas são mais valiosas quando full
        elif our_state == ElixirState.LOW and base_cost >= 6:
            multiplier *= 0.6  # Cartas caras são menos valiosas quando low
        
        if enemy_state == ElixirState.LOW:
            multiplier *= 1.2  # Todas as cartas são mais valiosas contra inimigo low
        
        # Histórico de eficiência da carta
        if card in self.card_value_analysis and context in self.card_value_analysis[card]:
            historical_value = self.card_value_analysis[card][context]
            # Média ponderada: 70% histórico, 30% cálculo atual
            final_value = (historical_value * 0.7) + (base_value * multiplier * 0.3)
        else:
            final_value = base_value * multiplier
        
        return final_value
    
    def should_spend_elixir_now(self, card: Cards, context: str = "neutral") -> Tuple[bool, str]:
        """Determina se deve gastar elixir agora"""
        
        card_cost = self._estimate_card_cost(card)
        
        # Verificar se temos elixir suficiente
        if self.our_current_elixir < card_cost:
            return False, "Insufficient elixir"
        
        # Verificar estratégia atual
        if self.current_strategy == ElixirStrategy.CONSERVATIVE:
            if card_cost > 4:
                return False, "Conservative strategy - avoid expensive cards"
        
        elif self.current_strategy == ElixirStrategy.EMERGENCY_DEFENSE:
            if context != "defense":
                return False, "Emergency defense mode - only defensive cards"
        
        elif self.current_strategy == ElixirStrategy.CYCLE_FAST:
            if card_cost > 3:
                return False, "Cycle mode - only cheap cards"
        
        # Verificar valor esperado
        card_value = self.calculate_card_value(card, context)
        value_threshold = 0.6  # Threshold mínimo
        
        if card_value < value_threshold:
            return False, f"Card value too low: {card_value:.2f}"
        
        # Verificar leak prevention
        if self.elixir_leak_prevention and self.our_current_elixir >= 9:
            return True, "Preventing elixir leak"
        
        # Verificar oportunidades
        for advantage in self.current_advantages:
            if advantage.opportunity == ElixirOpportunity.COUNTER_ATTACK and context == "attack":
                return True, "Counter-attack opportunity"
            elif advantage.opportunity == ElixirOpportunity.HEAVY_PUSH and card_cost >= 5:
                return True, "Heavy push opportunity"
        
        # Decisão padrão baseada na estratégia
        strategy_decisions = {
            ElixirStrategy.AGGRESSIVE_SPEND: (True, "Aggressive spending strategy"),
            ElixirStrategy.PUNISH_OPPONENT: (context == "attack", "Punish opponent strategy"),
            ElixirStrategy.WAIT_FOR_ADVANTAGE: (card_value > 0.8, "Wait for advantage strategy"),
            ElixirStrategy.CYCLE_FAST: (card_cost <= 3, "Fast cycle strategy")
        }
        
        return strategy_decisions.get(self.current_strategy, (False, "Unknown strategy"))
    
    def get_optimal_spending_sequence(self, available_cards: List[Cards], 
                                    target_elixir_spent: int) -> List[Tuple[Cards, float]]:
        """Retorna sequência ótima de gastos"""
        
        sequence = []
        remaining_elixir = self.our_current_elixir
        target_remaining = target_elixir_spent
        
        # Ordenar cartas por valor/custo
        card_efficiency = []
        for card in available_cards:
            cost = self._estimate_card_cost(card)
            value = self.calculate_card_value(card)
            efficiency = value / cost if cost > 0 else 0
            card_efficiency.append((card, cost, efficiency))
        
        # Ordenar por eficiência
        card_efficiency.sort(key=lambda x: x[2], reverse=True)
        
        # Selecionar cartas até atingir target
        current_time = time.time()
        delay_accumulator = 0.0
        
        for card, cost, efficiency in card_efficiency:
            if target_remaining >= cost and remaining_elixir >= cost:
                sequence.append((card, current_time + delay_accumulator))
                target_remaining -= cost
                remaining_elixir -= cost
                delay_accumulator += 1.0  # 1 segundo entre cartas
                
                if target_remaining <= 0:
                    break
        
        return sequence
    
    def record_spending_outcome(self, card: Cards, context: str, 
                              success: bool, damage_dealt: int = 0):
        """Registra resultado de gasto para aprendizado"""
        
        # Atualizar análise de valor da carta
        if card not in self.card_value_analysis:
            self.card_value_analysis[card] = {}
        
        if context not in self.card_value_analysis[card]:
            self.card_value_analysis[card][context] = 0.5  # Valor inicial neutro
        
        # Calcular novo valor baseado no resultado
        cost = self._estimate_card_cost(card)
        outcome_value = 0.8 if success else 0.2
        
        # Bonus por dano causado
        if damage_dealt > 0:
            damage_bonus = min(0.3, damage_dealt / 1000.0)  # Normalizar dano
            outcome_value += damage_bonus
        
        # Atualizar com média ponderada
        current_value = self.card_value_analysis[card][context]
        new_value = (current_value * 0.8) + (outcome_value * 0.2)
        self.card_value_analysis[card][context] = new_value
        
        # Atualizar taxa de sucesso da estratégia
        if self.current_strategy not in self.strategy_success_rates:
            self.strategy_success_rates[self.current_strategy] = []
        
        self.strategy_success_rates[self.current_strategy].append(success)
        
        # Manter apenas últimos 20 resultados
        if len(self.strategy_success_rates[self.current_strategy]) > 20:
            self.strategy_success_rates[self.current_strategy] = \
                self.strategy_success_rates[self.current_strategy][-20:]
    
    def get_elixir_recommendations(self) -> Dict[str, any]:
        """Retorna recomendações de elixir atuais"""
        
        recommendations = {
            "current_state": {
                "our_elixir": self.our_current_elixir,
                "enemy_elixir": self.enemy_current_elixir,
                "advantage": self.our_current_elixir - self.enemy_current_elixir,
                "our_state": self._get_elixir_state(self.our_current_elixir).value,
                "enemy_state": self._get_elixir_state(self.enemy_current_elixir).value
            },
            "current_strategy": self.current_strategy.value,
            "opportunities": [],
            "predictions": [],
            "spending_advice": {}
        }
        
        # Oportunidades atuais
        for advantage in self.current_advantages:
            recommendations["opportunities"].append({
                "type": advantage.opportunity.value,
                "advantage": advantage.advantage,
                "confidence": advantage.confidence,
                "duration": advantage.duration_estimate
            })
        
        # Predições
        for prediction in self.predicted_states:
            recommendations["predictions"].append({
                "time_offset": prediction.time_offset,
                "predicted_advantage": prediction.predicted_advantage,
                "recommended_action": prediction.recommended_action.value,
                "confidence": prediction.confidence
            })
        
        # Conselhos de gasto
        if self.our_current_elixir >= 9:
            recommendations["spending_advice"]["urgency"] = "high"
            recommendations["spending_advice"]["reason"] = "Prevent elixir leak"
        elif self.current_strategy == ElixirStrategy.AGGRESSIVE_SPEND:
            recommendations["spending_advice"]["urgency"] = "high"
            recommendations["spending_advice"]["reason"] = "Aggressive spending window"
        elif self.current_strategy == ElixirStrategy.CONSERVATIVE:
            recommendations["spending_advice"]["urgency"] = "low"
            recommendations["spending_advice"]["reason"] = "Conservative approach"
        else:
            recommendations["spending_advice"]["urgency"] = "medium"
            recommendations["spending_advice"]["reason"] = "Standard play"
        
        return recommendations
    
    def optimize_elixir_efficiency(self):
        """Otimiza eficiência de elixir baseada em dados históricos"""
        
        # Analisar padrões de sucesso por estratégia
        for strategy, results in self.strategy_success_rates.items():
            if len(results) >= 10:  # Dados suficientes
                success_rate = sum(results) / len(results)
                
                # Ajustar preferência por estratégias bem-sucedidas
                if success_rate > 0.7:
                    # Estratégia bem-sucedida - usar mais frequentemente
                    pass  # Implementar lógica de preferência
                elif success_rate < 0.3:
                    # Estratégia mal-sucedida - evitar
                    pass  # Implementar lógica de evitação
        
        # Otimizar valores de cartas baseado em performance
        for card, contexts in self.card_value_analysis.items():
            for context, value in contexts.items():
                # Ajustar valores baseado em tendências
                if value > 0.8:
                    # Carta muito eficiente - priorizar
                    self.card_value_analysis[card][context] = min(1.0, value * 1.05)
                elif value < 0.3:
                    # Carta pouco eficiente - desencorajar
                    self.card_value_analysis[card][context] = max(0.1, value * 0.95)
    
    def estimate_enemy_elixir(self) -> int:
        """Estima o elixir atual do inimigo"""
        
        # Implementação simplificada - pode ser melhorada com análise mais sofisticada
        # Por enquanto, usar estimativa baseada em padrões típicos
        
        if hasattr(self, 'enemy_current_elixir'):
            return self.enemy_current_elixir
        
        # Estimativa padrão baseada em tempo de jogo
        # Assumir que o inimigo está no mesmo nível de elixir
        return 5  # Valor padrão conservador

