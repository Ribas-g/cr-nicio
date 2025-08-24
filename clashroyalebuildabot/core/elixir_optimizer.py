"""
Sistema de otimização de elixir para maximizar eficiência de custo-benefício.
Analisa quando gastar elixir e quando economizar.
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import time
from clashroyalebuildabot import Cards


class ElixirState(Enum):
    """Estados do elixir"""
    CRITICAL = "critical"      # 0-2 elixir
    LOW = "low"               # 3-5 elixir
    MEDIUM = "medium"         # 6-8 elixir
    HIGH = "high"             # 9-10 elixir
    FULL = "full"             # 10 elixir (perdendo)


class SpendingPriority(Enum):
    """Prioridades de gasto de elixir"""
    CRITICAL_DEFENSE = "critical_defense"    # Defesa essencial
    HIGH_VALUE_ATTACK = "high_value_attack"  # Ataque de alto valor
    EFFICIENT_DEFENSE = "efficient_defense"  # Defesa eficiente
    MODERATE_ATTACK = "moderate_attack"      # Ataque moderado
    CYCLE_PLAY = "cycle_play"               # Jogada de ciclo
    LUXURY_PLAY = "luxury_play"             # Jogada de luxo


@dataclass
class ElixirOpportunity:
    """Oportunidade de gasto de elixir"""
    card: Cards
    cost: int
    priority: SpendingPriority
    expected_value: float
    timing_score: float
    risk_level: float
    recommended: bool


@dataclass
class ElixirAnalysis:
    """Análise completa do elixir"""
    current_elixir: int
    elixir_state: ElixirState
    enemy_elixir_estimate: int
    elixir_advantage: int
    should_conserve: bool
    should_spend: bool
    optimal_spending: int
    opportunities: List[ElixirOpportunity]


class ElixirOptimizer:
    """Sistema principal de otimização de elixir"""
    
    def __init__(self):
        self.last_spending_time = 0.0
        self.spending_history = []
        self.conservation_periods = []
        self.elixir_leak_count = 0
        
        # Configurações
        self.max_elixir_leak = 3  # Máximo de vazamentos por jogo
        self.conservation_threshold = 2  # Elixir mínimo para conservar
        self.aggressive_threshold = 8  # Elixir para jogar agressivamente
    
    def analyze_elixir_situation(self, current_elixir: int, available_actions: List,
                                enemy_elixir_estimate: int = None) -> ElixirAnalysis:
        """Analisa a situação atual do elixir"""
        
        # Determinar estado do elixir
        elixir_state = self._determine_elixir_state(current_elixir)
        
        # Estimar elixir inimigo se não fornecido
        if enemy_elixir_estimate is None:
            enemy_elixir_estimate = self._estimate_enemy_elixir()
        
        # Calcular vantagem de elixir
        elixir_advantage = current_elixir - enemy_elixir_estimate
        
        # Determinar se deve conservar ou gastar
        should_conserve = self._should_conserve_elixir(current_elixir, elixir_advantage)
        should_spend = self._should_spend_elixir(current_elixir, elixir_advantage)
        
        # Calcular gasto ótimo
        optimal_spending = self._calculate_optimal_spending(current_elixir, elixir_advantage)
        
        # Analisar oportunidades
        opportunities = self._analyze_opportunities(available_actions, current_elixir, elixir_advantage)
        
        return ElixirAnalysis(
            current_elixir=current_elixir,
            elixir_state=elixir_state,
            enemy_elixir_estimate=enemy_elixir_estimate,
            elixir_advantage=elixir_advantage,
            should_conserve=should_conserve,
            should_spend=should_spend,
            optimal_spending=optimal_spending,
            opportunities=opportunities
        )
    
    def _determine_elixir_state(self, elixir: int) -> ElixirState:
        """Determina o estado atual do elixir"""
        
        if elixir <= 2:
            return ElixirState.CRITICAL
        elif elixir <= 5:
            return ElixirState.LOW
        elif elixir <= 8:
            return ElixirState.MEDIUM
        elif elixir < 10:
            return ElixirState.HIGH
        else:
            return ElixirState.FULL
    
    def _estimate_enemy_elixir(self) -> int:
        """Estima o elixir do inimigo baseado no histórico"""
        
        # Implementação simplificada - pode ser melhorada
        # Assumir que o inimigo está no mesmo nível de elixir
        return 5  # Placeholder
    
    def _should_conserve_elixir(self, current_elixir: int, advantage: int) -> bool:
        """Determina se deve conservar elixir"""
        
        # Conservar se elixir muito baixo
        if current_elixir <= self.conservation_threshold:
            return True
        
        # Conservar se em desvantagem significativa
        if advantage <= -3:
            return True
        
        # Conservar se próximo de vazar elixir
        if current_elixir >= 9:
            return False  # Deve gastar para não vazar
        
        return False
    
    def _should_spend_elixir(self, current_elixir: int, advantage: int) -> bool:
        """Determina se deve gastar elixir"""
        
        # Sempre gastar se elixir cheio
        if current_elixir >= 10:
            return True
        
        # Gastar se em vantagem significativa
        if advantage >= 3:
            return True
        
        # Gastar se elixir alto
        if current_elixir >= self.aggressive_threshold:
            return True
        
        return False
    
    def _calculate_optimal_spending(self, current_elixir: int, advantage: int) -> int:
        """Calcula o gasto ótimo de elixir"""
        
        if current_elixir >= 10:
            return min(current_elixir, 10)  # Gastar tudo se cheio
        
        if advantage >= 3:
            return min(current_elixir - 2, 8)  # Manter 2 de reserva
        
        if current_elixir >= 8:
            return min(current_elixir - 1, 7)  # Manter 1 de reserva
        
        return max(0, current_elixir - 3)  # Conservar pelo menos 3
    
    def _analyze_opportunities(self, available_actions: List, current_elixir: int, 
                             advantage: int) -> List[ElixirOpportunity]:
        """Analisa oportunidades de gasto de elixir"""
        
        opportunities = []
        
        for action in available_actions:
            if not hasattr(action, 'CARD'):
                continue
            
            card = action.CARD
            cost = getattr(card, 'cost', 4)  # Custo padrão se não definido
            
            # Verificar se pode pagar
            if cost > current_elixir:
                continue
            
            # Calcular prioridade
            priority = self._calculate_spending_priority(card, cost, advantage)
            
            # Calcular valor esperado
            expected_value = self._calculate_expected_value(card, cost, advantage)
            
            # Calcular score de timing
            timing_score = self._calculate_timing_score(card, current_elixir)
            
            # Calcular nível de risco
            risk_level = self._calculate_risk_level(card, cost, current_elixir)
            
            # Determinar se é recomendado
            recommended = self._is_recommended_play(card, cost, priority, expected_value)
            
            opportunity = ElixirOpportunity(
                card=card,
                cost=cost,
                priority=priority,
                expected_value=expected_value,
                timing_score=timing_score,
                risk_level=risk_level,
                recommended=recommended
            )
            
            opportunities.append(opportunity)
        
        # Ordenar por valor esperado
        opportunities.sort(key=lambda x: x.expected_value, reverse=True)
        
        return opportunities
    
    def _calculate_spending_priority(self, card: Cards, cost: int, advantage: int) -> SpendingPriority:
        """Calcula a prioridade de gasto para uma carta"""
        
        # Defesas críticas sempre têm prioridade máxima
        if self._is_critical_defense(card):
            return SpendingPriority.CRITICAL_DEFENSE
        
        # Ataques de alto valor quando em vantagem
        if advantage >= 2 and self._is_high_value_attack(card):
            return SpendingPriority.HIGH_VALUE_ATTACK
        
        # Defesas eficientes
        if self._is_efficient_defense(card):
            return SpendingPriority.EFFICIENT_DEFENSE
        
        # Ataques moderados
        if self._is_moderate_attack(card):
            return SpendingPriority.MODERATE_ATTACK
        
        # Jogadas de ciclo
        if cost <= 3:
            return SpendingPriority.CYCLE_PLAY
        
        return SpendingPriority.LUXURY_PLAY
    
    def _is_critical_defense(self, card: Cards) -> bool:
        """Verifica se é uma defesa crítica"""
        
        critical_defenses = [
            'inferno_tower', 'cannon', 'tesla', 'bomb_tower',
            'mini_pekka', 'pekka', 'valkyrie', 'knight'
        ]
        
        return any(defense in card.name.lower() for defense in critical_defenses)
    
    def _is_high_value_attack(self, card: Cards) -> bool:
        """Verifica se é um ataque de alto valor"""
        
        high_value_attacks = [
            'giant', 'golem', 'pekka', 'mega_knight',
            'hog_rider', 'ram_rider', 'balloon'
        ]
        
        return any(attack in card.name.lower() for attack in high_value_attacks)
    
    def _is_efficient_defense(self, card: Cards) -> bool:
        """Verifica se é uma defesa eficiente"""
        
        efficient_defenses = [
            'archers', 'musketeer', 'wizard', 'electro_wizard',
            'skeletons', 'goblins', 'spear_goblins'
        ]
        
        return any(defense in card.name.lower() for defense in efficient_defenses)
    
    def _is_moderate_attack(self, card: Cards) -> bool:
        """Verifica se é um ataque moderado"""
        
        moderate_attacks = [
            'knight', 'valkyrie', 'mini_pekka', 'baby_dragon'
        ]
        
        return any(attack in card.name.lower() for attack in moderate_attacks)
    
    def _calculate_expected_value(self, card: Cards, cost: int, advantage: int) -> float:
        """Calcula o valor esperado de uma carta"""
        
        base_value = 1.0
        
        # Ajustar baseado no custo
        if cost <= 3:
            base_value *= 1.2  # Cartas baratas são mais eficientes
        elif cost >= 7:
            base_value *= 0.8  # Cartas caras são menos eficientes
        
        # Ajustar baseado na vantagem
        if advantage >= 3:
            base_value *= 1.3  # Melhor quando em vantagem
        elif advantage <= -3:
            base_value *= 0.7  # Pior quando em desvantagem
        
        # Ajustar baseado no tipo de carta
        if self._is_critical_defense(card):
            base_value *= 1.5
        elif self._is_high_value_attack(card):
            base_value *= 1.3
        
        return base_value
    
    def _calculate_timing_score(self, card: Cards, current_elixir: int) -> float:
        """Calcula o score de timing para uma carta"""
        
        # Cartas baratas são melhores com elixir baixo
        cost = getattr(card, 'cost', 4)
        
        if cost <= 3 and current_elixir <= 6:
            return 1.2
        elif cost >= 6 and current_elixir >= 8:
            return 1.1
        else:
            return 1.0
    
    def _calculate_risk_level(self, card: Cards, cost: int, current_elixir: int) -> float:
        """Calcula o nível de risco de uma jogada"""
        
        risk = 0.5  # Risco base
        
        # Risco aumenta com custo
        if cost >= 7:
            risk += 0.3
        elif cost <= 3:
            risk -= 0.2
        
        # Risco aumenta com elixir baixo
        if current_elixir <= 4:
            risk += 0.2
        
        return min(1.0, max(0.0, risk))
    
    def _is_recommended_play(self, card: Cards, cost: int, priority: SpendingPriority, 
                           expected_value: float) -> bool:
        """Determina se uma jogada é recomendada"""
        
        # Sempre recomendar defesas críticas
        if priority == SpendingPriority.CRITICAL_DEFENSE:
            return True
        
        # Recomendar se valor esperado alto
        if expected_value >= 1.2:
            return True
        
        # Recomendar jogadas de ciclo com valor decente
        if priority == SpendingPriority.CYCLE_PLAY and expected_value >= 1.0:
            return True
        
        return False
    
    def record_spending(self, card: Cards, cost: int, timestamp: float = None):
        """Registra um gasto de elixir"""
        
        if timestamp is None:
            timestamp = time.time()
        
        self.spending_history.append({
            'card': card,
            'cost': cost,
            'timestamp': timestamp
        })
        
        self.last_spending_time = timestamp
    
    def get_elixir_efficiency_stats(self) -> Dict:
        """Retorna estatísticas de eficiência do elixir"""
        
        if not self.spending_history:
            return {}
        
        total_spent = sum(record['cost'] for record in self.spending_history)
        total_plays = len(self.spending_history)
        avg_cost = total_spent / total_plays
        
        # Calcular vazamentos de elixir
        leak_count = self.elixir_leak_count
        
        return {
            'total_spent': total_spent,
            'total_plays': total_plays,
            'average_cost': avg_cost,
            'leak_count': leak_count,
            'efficiency_score': self._calculate_efficiency_score(avg_cost, leak_count)
        }
    
    def _calculate_efficiency_score(self, avg_cost: float, leak_count: int) -> float:
        """Calcula score de eficiência do elixir"""
        
        # Score baseado no custo médio (menor é melhor)
        cost_score = max(0, 1.0 - (avg_cost - 4.0) / 4.0)
        
        # Penalizar vazamentos
        leak_penalty = min(1.0, leak_count / self.max_elixir_leak)
        
        return max(0, cost_score - leak_penalty)
    
    def get_optimization_summary(self) -> str:
        """Retorna resumo da otimização para logging"""
        
        stats = self.get_elixir_efficiency_stats()
        
        if not stats:
            return "💰 Otimização de Elixir: Sem dados suficientes"
        
        summary = f"💰 Otimização de Elixir:\n"
        summary += f"   Custo médio: {stats['average_cost']:.1f}\n"
        summary += f"   Total gasto: {stats['total_spent']}\n"
        summary += f"   Vazamentos: {stats['leak_count']}\n"
        summary += f"   Eficiência: {stats['efficiency_score']:.1%}"
        
        return summary
