"""
Sistema de Integração Principal
==============================

Sistema que integra todos os componentes avançados do bot:
- Predição de cartas inimigas
- Timing dinâmico de combos
- Defesa proativa
- Controle avançado de elixir
- Posicionamento inteligente
- Controle de fases
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time
import json

from clashroyalebuildabot.namespaces.cards import Cards
from .enemy_prediction import AdvancedEnemyPredictor as EnemyCardPredictor
from .dynamic_timing import DynamicTimingManager
from .proactive_defense import ProactiveDefenseManager
from .advanced_elixir_control import AdvancedElixirController
from .intelligent_positioning import IntelligentPositioning, PositionType, UnitInfo
from .phase_control import PhaseController, GamePhase


@dataclass
class GameState:
    """Estado completo do jogo"""
    # Tempo
    game_time: float
    phase: GamePhase
    
    # Elixir
    our_elixir: int
    enemy_elixir_estimate: int
    elixir_advantage: int
    
    # Torres
    tower_hp: Dict[str, int]
    
    # Unidades no campo
    units_on_field: List[UnitInfo]
    
    # Cartas
    our_hand: List[Cards]
    enemy_cards_seen: List[Cards]
    
    # Histórico recente
    recent_enemy_plays: List[Tuple[Cards, Tuple[int, int], float]]
    recent_our_plays: List[Tuple[Cards, Tuple[int, int], float]]


@dataclass
class ActionRecommendation:
    """Recomendação de ação"""
    action_type: str  # "play_card", "wait", "defend", "attack"
    card: Optional[Cards]
    position: Optional[Tuple[int, int]]
    confidence: float
    reasoning: List[str]
    priority: int  # 1 = baixa, 5 = crítica
    timing_delay: float  # Segundos para esperar antes de executar


class MasterBotController:
    """Controlador principal que integra todos os sistemas"""
    
    def __init__(self):
        # Inicializar todos os subsistemas
        self.enemy_predictor = EnemyCardPredictor()
        self.timing_manager = DynamicTimingManager()
        self.defense_manager = ProactiveDefenseManager()
        self.elixir_controller = AdvancedElixirController()
        self.positioning_system = IntelligentPositioning()
        self.phase_controller = PhaseController()
        
        # Estado do jogo
        self.current_game_state: Optional[GameState] = None
        
        # Histórico de decisões
        self.decision_history: List[Tuple[float, ActionRecommendation, bool]] = []
        
        # Métricas de performance
        self.performance_metrics: Dict[str, List[float]] = {
            "prediction_accuracy": [],
            "timing_success": [],
            "defense_effectiveness": [],
            "elixir_efficiency": [],
            "positioning_success": [],
            "overall_performance": []
        }
        
        # Configurações adaptativas
        self.system_weights: Dict[str, float] = {
            "enemy_prediction": 0.2,
            "timing_optimization": 0.2,
            "defense_priority": 0.25,
            "elixir_control": 0.2,
            "positioning": 0.15
        }
        
        # Cache de recomendações
        self.cached_recommendations: Dict[str, ActionRecommendation] = {}
        self.cache_timestamp: float = 0
        self.cache_duration: float = 1.0  # Cache válido por 1 segundo
    
    def update_game_state(self, 
                         game_time: float,
                         our_elixir: int,
                         tower_hp: Dict[str, int],
                         units_on_field: List[UnitInfo],
                         our_hand: List[Cards],
                         recent_enemy_plays: List[Tuple[Cards, Tuple[int, int], float]],
                         recent_our_plays: List[Tuple[Cards, Tuple[int, int], float]]):
        """Atualiza estado completo do jogo em todos os subsistemas"""
        
        # Atualizar controlador de fases
        self.phase_controller.update_game_state(
            game_time, tower_hp, 
            our_elixir - self.elixir_controller.enemy_current_elixir,
            [play[0].name for play in recent_our_plays]
        )
        
        # Atualizar preditor de cartas inimigas
        self.enemy_predictor.update_enemy_plays(recent_enemy_plays)
        
        # Atualizar gerenciador de timing
        self.timing_manager.update_game_context(
            game_time=game_time,
            our_elixir=our_elixir,
            enemy_elixir=self.elixir_controller.enemy_current_elixir,
            our_tower_hp=[tower_hp.get('king', 100), tower_hp.get('left', 100), tower_hp.get('right', 100)],
            enemy_tower_hp=[100, 100, 100],  # Placeholder - implementar detecção
            recent_enemy_plays=[play[0] if isinstance(play, tuple) else play for play in recent_enemy_plays],
            elixir_advantage=our_elixir - self.elixir_controller.enemy_current_elixir
        )
        
        # Atualizar sistema de defesa
        self.defense_manager.analyze_enemy_pattern(recent_enemy_plays)
        
        # Atualizar controlador de elixir
        self.elixir_controller.update_elixir_state(
            our_elixir, recent_enemy_plays, recent_our_plays, game_time
        )
        
        # Criar estado do jogo
        self.current_game_state = GameState(
            game_time=game_time,
            phase=self.phase_controller.current_phase,
            our_elixir=our_elixir,
            enemy_elixir_estimate=self.elixir_controller.enemy_current_elixir,
            elixir_advantage=our_elixir - self.elixir_controller.enemy_current_elixir,
            tower_hp=tower_hp.copy(),
            units_on_field=units_on_field.copy(),
            our_hand=our_hand.copy(),
            enemy_cards_seen=self.enemy_predictor.get_known_enemy_cards(),
            recent_enemy_plays=recent_enemy_plays.copy(),
            recent_our_plays=recent_our_plays.copy()
        )
        
        # Invalidar cache
        self.cache_timestamp = 0
    
    def get_best_action(self) -> ActionRecommendation:
        """Retorna a melhor ação recomendada integrando todos os sistemas"""
        
        if not self.current_game_state:
            return ActionRecommendation(
                action_type="wait",
                card=None,
                position=None,
                confidence=0.0,
                reasoning=["No game state available"],
                priority=1,
                timing_delay=1.0
            )
        
        # Verificar cache
        current_time = time.time()
        if (current_time - self.cache_timestamp < self.cache_duration and 
            "best_action" in self.cached_recommendations):
            return self.cached_recommendations["best_action"]
        
        # Gerar recomendações de todos os sistemas
        recommendations = self._generate_all_recommendations()
        
        # Integrar e priorizar recomendações
        best_action = self._integrate_recommendations(recommendations)
        
        # Atualizar cache
        self.cached_recommendations["best_action"] = best_action
        self.cache_timestamp = current_time
        
        return best_action
    
    def _generate_all_recommendations(self) -> Dict[str, List[ActionRecommendation]]:
        """Gera recomendações de todos os subsistemas"""
        
        recommendations = {
            "defense": [],
            "attack": [],
            "elixir": [],
            "positioning": [],
            "timing": []
        }
        
        state = self.current_game_state
        
        # 1. Recomendações de defesa
        defense_recs = self._get_defense_recommendations()
        recommendations["defense"].extend(defense_recs)
        
        # 2. Recomendações de ataque
        attack_recs = self._get_attack_recommendations()
        recommendations["attack"].extend(attack_recs)
        
        # 3. Recomendações de elixir
        elixir_recs = self._get_elixir_recommendations()
        recommendations["elixir"].extend(elixir_recs)
        
        # 4. Recomendações de posicionamento
        positioning_recs = self._get_positioning_recommendations()
        recommendations["positioning"].extend(positioning_recs)
        
        # 5. Recomendações de timing
        timing_recs = self._get_timing_recommendations()
        recommendations["timing"].extend(timing_recs)
        
        return recommendations
    
    def _get_defense_recommendations(self) -> List[ActionRecommendation]:
        """Gera recomendações defensivas"""
        
        recommendations = []
        state = self.current_game_state
        
        # Verificar ameaças imediatas
        defense_info = self.defense_manager.get_defense_recommendations()
        
        for threat in defense_info["immediate_threats"]:
            if threat["confidence"] > 0.6:
                # Encontrar melhor contador
                threat_card_name = threat["card"].upper()
                threat_card = getattr(Cards, threat_card_name, None)
                if not threat_card:
                    continue
                
                for card in state.our_hand:
                    if self._is_good_counter(card, threat_card):
                        # Calcular posição defensiva
                        position_rec = self.positioning_system.get_positioning_recommendations(
                            card, state.units_on_field, "defense"
                        )
                        
                        recommendations.append(ActionRecommendation(
                            action_type="defend",
                            card=card,
                            position=(position_rec["primary_position"]["x"], 
                                    position_rec["primary_position"]["y"]),
                            confidence=threat["confidence"] * 0.9,
                            reasoning=[f"Counter {threat['card']} threat", 
                                     f"Threat level: {threat['threat_level']}"],
                            priority=5 if threat["threat_level"] == "HIGH" else 4,
                            timing_delay=max(0, threat["time_to_threat"] - 1.0)
                        ))
                        break
        
        return recommendations
    
    def _get_attack_recommendations(self) -> List[ActionRecommendation]:
        """Gera recomendações de ataque"""
        
        recommendations = []
        state = self.current_game_state
        
        # Verificar oportunidades de ataque
        elixir_info = self.elixir_controller.get_elixir_recommendations()
        
        for opportunity in elixir_info["opportunities"]:
            if opportunity["type"] in ["counter_attack", "heavy_push"]:
                # Encontrar cartas de ataque disponíveis
                for card in state.our_hand:
                    if self._is_attack_card(card):
                        # Verificar se devemos gastar elixir agora
                        should_spend, reason = self.elixir_controller.should_spend_elixir_now(
                            card, "attack"
                        )
                        
                        if should_spend:
                            # Calcular posição ofensiva
                            position_rec = self.positioning_system.get_positioning_recommendations(
                                card, state.units_on_field, "attack"
                            )
                            
                            recommendations.append(ActionRecommendation(
                                action_type="attack",
                                card=card,
                                position=(position_rec["primary_position"]["x"],
                                        position_rec["primary_position"]["y"]),
                                confidence=opportunity["confidence"],
                                reasoning=[f"Attack opportunity: {opportunity['type']}", reason],
                                priority=4 if opportunity["type"] == "heavy_push" else 3,
                                timing_delay=0.5
                            ))
        
        return recommendations
    
    def _get_elixir_recommendations(self) -> List[ActionRecommendation]:
        """Gera recomendações de gestão de elixir"""
        
        recommendations = []
        state = self.current_game_state
        
        elixir_info = self.elixir_controller.get_elixir_recommendations()
        
        # Verificar necessidade de prevenir leak
        if state.our_elixir >= 9:
            # Encontrar carta barata para ciclar
            cheap_cards = [card for card in state.our_hand 
                          if self._estimate_card_cost(card) <= 3]
            
            if cheap_cards:
                best_cheap = min(cheap_cards, key=self._estimate_card_cost)
                
                position_rec = self.positioning_system.get_positioning_recommendations(
                    best_cheap, state.units_on_field, "neutral"
                )
                
                recommendations.append(ActionRecommendation(
                    action_type="cycle",
                    card=best_cheap,
                    position=(position_rec["primary_position"]["x"],
                            position_rec["primary_position"]["y"]),
                    confidence=0.9,
                    reasoning=["Prevent elixir leak", f"Elixir at {state.our_elixir}"],
                    priority=4,
                    timing_delay=0.0
                ))
        
        # Verificar estratégia de conservação
        elif elixir_info["spending_advice"]["urgency"] == "low":
            recommendations.append(ActionRecommendation(
                action_type="wait",
                card=None,
                position=None,
                confidence=0.7,
                reasoning=["Conservative elixir strategy", 
                          elixir_info["spending_advice"]["reason"]],
                priority=2,
                timing_delay=2.0
            ))
        
        return recommendations
    
    def _get_positioning_recommendations(self) -> List[ActionRecommendation]:
        """Gera recomendações de posicionamento"""
        
        recommendations = []
        state = self.current_game_state
        
        # Verificar se há tropas mal posicionadas que precisam de suporte
        allied_units = [unit for unit in state.units_on_field if not unit.is_enemy]
        
        for unit in allied_units:
            if self._needs_support(unit, state.units_on_field):
                # Encontrar carta de suporte
                support_cards = [card for card in state.our_hand 
                               if self._is_support_card(card)]
                
                if support_cards:
                    best_support = support_cards[0]  # Simplificado
                    
                    position_rec = self.positioning_system.get_positioning_recommendations(
                        best_support, state.units_on_field, "support"
                    )
                    
                    recommendations.append(ActionRecommendation(
                        action_type="support",
                        card=best_support,
                        position=(position_rec["primary_position"]["x"],
                                position_rec["primary_position"]["y"]),
                        confidence=0.6,
                        reasoning=[f"Support {unit.card.name}", "Improve positioning"],
                        priority=3,
                        timing_delay=1.0
                    ))
        
        return recommendations
    
    def _get_timing_recommendations(self) -> List[ActionRecommendation]:
        """Gera recomendações de timing"""
        
        recommendations = []
        state = self.current_game_state
        
        # Verificar combos disponíveis
        combo_opportunities = self.timing_manager.get_available_combos(state.our_hand)
        
        for combo in combo_opportunities:
            if combo["confidence"] > 0.7:
                # Verificar se é o momento certo para o combo
                timing_info = self.timing_manager.calculate_optimal_timing(
                    combo["cards"], state.units_on_field, state.elixir_advantage
                )
                
                if timing_info["should_execute"]:
                    # Posição para primeira carta do combo
                    first_card = combo["cards"][0]
                    position_rec = self.positioning_system.get_positioning_recommendations(
                        first_card, state.units_on_field, "attack"
                    )
                    
                    recommendations.append(ActionRecommendation(
                        action_type="combo",
                        card=first_card,
                        position=(position_rec["primary_position"]["x"],
                                position_rec["primary_position"]["y"]),
                        confidence=combo["confidence"],
                        reasoning=[f"Execute {combo['name']} combo", 
                                 f"Optimal timing window"],
                        priority=4,
                        timing_delay=timing_info["delay"]
                    ))
        
        return recommendations
    
    def _integrate_recommendations(self, 
                                 recommendations: Dict[str, List[ActionRecommendation]]) -> ActionRecommendation:
        """Integra todas as recomendações e escolhe a melhor"""
        
        all_recommendations = []
        
        # Coletar todas as recomendações
        for category, recs in recommendations.items():
            for rec in recs:
                # Aplicar peso do sistema
                weight = self.system_weights.get(category, 1.0)
                rec.confidence *= weight
                all_recommendations.append(rec)
        
        if not all_recommendations:
            return ActionRecommendation(
                action_type="wait",
                card=None,
                position=None,
                confidence=0.5,
                reasoning=["No recommendations available"],
                priority=1,
                timing_delay=1.0
            )
        
        # Ordenar por prioridade e confiança
        all_recommendations.sort(
            key=lambda x: (x.priority, x.confidence), 
            reverse=True
        )
        
        # Aplicar modificadores da fase atual
        best_rec = all_recommendations[0]
        phase_config = self.phase_controller.get_current_configuration()
        
        # Ajustar confiança baseado na fase
        if best_rec.action_type == "attack":
            best_rec.confidence *= phase_config.aggression_level
        elif best_rec.action_type == "defend":
            best_rec.confidence *= (2.0 - phase_config.aggression_level)
        
        # Ajustar timing baseado na fase
        if best_rec.card:
            timing_modifier = self.phase_controller.calculate_timing_modifier(
                best_rec.action_type
            )
            best_rec.timing_delay *= timing_modifier
        
        return best_rec
    
    def execute_action(self, action: ActionRecommendation) -> bool:
        """Executa uma ação e registra o resultado"""
        
        # Registrar decisão
        current_time = time.time()
        self.decision_history.append((current_time, action, False))  # Sucesso será atualizado depois
        
        # Aqui seria a integração com o sistema de execução real do bot
        # Por enquanto, simular execução
        
        print(f"Executing action: {action.action_type}")
        if action.card:
            print(f"  Card: {action.card.name}")
        if action.position:
            print(f"  Position: {action.position}")
        print(f"  Confidence: {action.confidence:.2f}")
        print(f"  Reasoning: {', '.join(action.reasoning)}")
        
        return True  # Simular sucesso
    
    def record_action_outcome(self, success: bool, damage_dealt: int = 0):
        """Registra resultado da última ação"""
        
        if self.decision_history:
            timestamp, action, _ = self.decision_history[-1]
            self.decision_history[-1] = (timestamp, action, success)
            
            # Atualizar sistemas com feedback
            if action.card:
                # Feedback para sistema de elixir
                self.elixir_controller.record_spending_outcome(
                    action.card, action.action_type, success, damage_dealt
                )
                
                # Feedback para sistema de posicionamento
                if action.position:
                    self.positioning_system.record_positioning_outcome(
                        action.card, 
                        self.positioning_system.Position(action.position[0], action.position[1]),
                        success
                    )
            
            # Feedback para controlador de fases
            success_score = 0.8 if success else 0.2
            if damage_dealt > 0:
                success_score += min(0.2, damage_dealt / 1000.0)
            
            self.phase_controller.record_phase_performance(success_score)
            
            # Atualizar métricas
            self._update_performance_metrics(success, damage_dealt)
    
    def _update_performance_metrics(self, success: bool, damage_dealt: int):
        """Atualiza métricas de performance"""
        
        # Métrica geral
        overall_score = 0.7 if success else 0.3
        if damage_dealt > 0:
            overall_score += min(0.3, damage_dealt / 1000.0)
        
        self.performance_metrics["overall_performance"].append(overall_score)
        
        # Manter apenas últimos 50 registros
        for metric in self.performance_metrics.values():
            if len(metric) > 50:
                metric[:] = metric[-50:]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema"""
        
        if not self.current_game_state:
            return {"status": "No game state"}
        
        state = self.current_game_state
        
        status = {
            "game_state": {
                "phase": state.phase.value,
                "game_time": state.game_time,
                "elixir_advantage": state.elixir_advantage,
                "our_elixir": state.our_elixir,
                "enemy_elixir": state.enemy_elixir_estimate
            },
            
            "subsystem_status": {
                "enemy_prediction": self.enemy_predictor.get_prediction_summary(),
                "defense_analysis": self.defense_manager.get_defense_recommendations(),
                "elixir_control": self.elixir_controller.get_elixir_recommendations(),
                "phase_control": self.phase_controller.get_phase_recommendations()
            },
            
            "performance_metrics": {
                metric: sum(values) / len(values) if values else 0.0
                for metric, values in self.performance_metrics.items()
            },
            
            "recent_decisions": [
                {
                    "timestamp": timestamp,
                    "action": action.action_type,
                    "card": action.card.name if action.card else None,
                    "success": success,
                    "confidence": action.confidence
                }
                for timestamp, action, success in self.decision_history[-5:]
            ]
        }
        
        return status
    
    def optimize_system_weights(self):
        """Otimiza pesos dos subsistemas baseado na performance"""
        
        if len(self.decision_history) < 20:
            return  # Dados insuficientes
        
        # Analisar sucesso por tipo de ação
        action_success = {}
        
        for _, action, success in self.decision_history[-20:]:
            action_type = action.action_type
            if action_type not in action_success:
                action_success[action_type] = []
            action_success[action_type].append(success)
        
        # Ajustar pesos baseado no sucesso
        for action_type, successes in action_success.items():
            success_rate = sum(successes) / len(successes)
            
            if action_type == "defend" and success_rate > 0.7:
                self.system_weights["defense_priority"] = min(0.4, 
                    self.system_weights["defense_priority"] + 0.05)
            elif action_type == "attack" and success_rate > 0.7:
                self.system_weights["timing_optimization"] = min(0.3,
                    self.system_weights["timing_optimization"] + 0.05)
    
    # Métodos auxiliares
    def _is_good_counter(self, our_card: Cards, enemy_card: Cards) -> bool:
        """Verifica se nossa carta é um bom contador"""
        # Implementação simplificada
        counters = {
            Cards.GIANT: [Cards.INFERNO_TOWER, Cards.MINIPEKKA, Cards.PEKKA],
            Cards.HOG_RIDER: [Cards.CANNON, Cards.TESLA, Cards.TOMBSTONE],
            Cards.BALLOON: [Cards.MUSKETEER, Cards.ARCHERS, Cards.TESLA],
            Cards.SKELETON_ARMY: [Cards.ZAP, Cards.ARROWS, Cards.VALKYRIE]
        }
        return our_card in counters.get(enemy_card, [])
    
    def _is_attack_card(self, card: Cards) -> bool:
        """Verifica se é carta de ataque"""
        attack_cards = [Cards.GIANT, Cards.HOG_RIDER, Cards.BALLOON, Cards.PEKKA]
        return card in attack_cards
    
    def _is_support_card(self, card: Cards) -> bool:
        """Verifica se é carta de suporte"""
        support_cards = [Cards.MUSKETEER, Cards.WIZARD, Cards.ARCHERS]
        return card in support_cards
    
    def _estimate_card_cost(self, card: Cards) -> int:
        """Estima custo de uma carta"""
        return self.elixir_controller._estimate_card_cost(card)
    
    def _needs_support(self, unit: UnitInfo, all_units: List[UnitInfo]) -> bool:
        """Verifica se unidade precisa de suporte"""
        # Implementação simplificada
        if unit.card in [Cards.GIANT, Cards.GOLEM]:
            # Tanques precisam de suporte
            nearby_support = [u for u in all_units 
                            if not u.is_enemy and 
                            u.position.distance_to(unit.position) < 4 and
                            u.card in [Cards.MUSKETEER, Cards.WIZARD]]
            return len(nearby_support) == 0
        return False

