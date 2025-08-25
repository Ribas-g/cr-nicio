"""
Enhanced Bot with Intelligent Systems
====================================

Bot aprimorado com sistemas inteligentes de decisão, combos, defesa e otimização.
"""

import time
import random
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass

from ..core.combo_system import ComboManager
from ..core.defense_system import DefenseManager
from ..core.enhanced_action import EnhancedAction
from ..core.memory_system import MemorySystem
from ..core.elixir_optimizer import ElixirOptimizer

# Sistemas Avançados
from ..advanced_systems.master_integration import MasterBotController, GameState, ActionRecommendation
from ..advanced_systems.enemy_prediction import AdvancedEnemyPredictor as EnemyCardPredictor
from ..advanced_systems.dynamic_timing import DynamicTimingManager
from ..advanced_systems.proactive_defense import ProactiveDefenseManager
from ..advanced_systems.advanced_elixir_control import AdvancedElixirController
from ..advanced_systems.intelligent_positioning import IntelligentPositioning, PositionType
from ..advanced_systems.phase_control import PhaseController
from ..advanced_systems.phase_control import GamePhase as AdvancedGamePhase

from .bot import Bot
from ..namespaces.cards import Cards
from ..namespaces.state import State
from ..utils.logger import logger

from ..core.card_roles import DeckAnalyzer, CardRoleDatabase
from ..core.game_state import GameStateAnalyzer, GameStateInfo
from ..core.combo_system import ComboManager
from ..core.defense_system import DefenseManager
from ..core.enhanced_action import EnhancedAction
from ..core.memory_system import MemorySystem
from ..core.elixir_optimizer import ElixirOptimizer

# Importar ações aprimoradas (se existirem)
try:
    from ..actions.enhanced_giant_action import EnhancedGiantAction
    from ..actions.enhanced_musketeer_action import EnhancedMusketeerAction
    from ..actions.enhanced_hog_rider_action import EnhancedHogRiderAction
    ENHANCED_ACTIONS_AVAILABLE = True
except ImportError:
    ENHANCED_ACTIONS_AVAILABLE = False
    print("⚠️  Ações aprimoradas não disponíveis, usando ações padrão")


class EnhancedBot(Bot):
    """Bot aprimorado com inteligência estratégica e sistemas avançados"""
    
    def __init__(self, actions, config):
        super().__init__(actions, config)
        
        # Configurações de inteligência
        self.intelligence_enabled = config.get("bot", {}).get("intelligence_enabled", True)
        self.combo_system_enabled = config.get("bot", {}).get("combo_system_enabled", True)
        self.defense_system_enabled = config.get("bot", {}).get("defense_system_enabled", True)
        self.strategic_play = config.get("bot", {}).get("strategic_play", True)
        self.advanced_systems_enabled = config.get("bot", {}).get("advanced_systems_enabled", True)
        
        # Sistemas inteligentes básicos
        self.deck_analyzer: Optional[DeckAnalyzer] = None
        self.game_state_analyzer: Optional[GameStateAnalyzer] = None
        self.combo_manager: Optional[ComboManager] = None
        self.defense_manager: Optional[DefenseManager] = None
        self.memory_system: Optional[MemorySystem] = None
        self.elixir_optimizer: Optional[ElixirOptimizer] = None
        
        # Sistemas avançados
        self.master_controller: Optional[MasterBotController] = None
        self.enemy_predictor: Optional[EnemyCardPredictor] = None
        self.timing_manager: Optional[DynamicTimingManager] = None
        self.proactive_defense: Optional[ProactiveDefenseManager] = None
        self.advanced_elixir: Optional[AdvancedElixirController] = None
        self.intelligent_positioning: Optional[IntelligentPositioning] = None
        self.phase_controller: Optional[PhaseController] = None
        
        # Cache e estado
        self.last_game_state: Optional[GameStateInfo] = None
        self.cards_in_hand: List[Cards] = []
        self.enhanced_actions: Dict[str, EnhancedAction] = {}
        
        # Estado do jogo para sistemas avançados
        self.advanced_game_state: Optional[GameState] = None
        self.last_action_recommendation: Optional[ActionRecommendation] = None
        
        # Inicializar sistemas quando deck estiver disponível
        self._initialize_systems()
    
    def _initialize_systems(self):
        """Inicializa sistemas inteligentes baseado no deck"""
        
        # Extrair deck das ações disponíveis (classes)
        deck_cards = []
        for action_class in self.actions:
            if hasattr(action_class, 'CARD') and action_class.CARD:
                deck_cards.append(action_class.CARD)
        
        if not deck_cards:
            print("⚠️  Aviso: Não foi possível extrair deck das ações")
            return
        
        print(f"🎯 Inicializando sistemas inteligentes com deck: {[card.name for card in deck_cards]}")
        
        # Inicializar sistemas básicos
        self.deck_analyzer = DeckAnalyzer(deck_cards)
        self.game_state_analyzer = GameStateAnalyzer(self.deck_analyzer)
        self.combo_manager = ComboManager(deck_cards)
        self.defense_manager = DefenseManager(deck_cards)
        self.memory_system = MemorySystem()
        self.elixir_optimizer = ElixirOptimizer()
        
        # Inicializar sistemas avançados se habilitados
        if self.advanced_systems_enabled:
            print("🚀 Inicializando sistemas avançados...")
            
            self.enemy_predictor = EnemyCardPredictor()
            self.timing_manager = DynamicTimingManager()
            self.proactive_defense = ProactiveDefenseManager()
            self.advanced_elixir = AdvancedElixirController()
            self.intelligent_positioning = IntelligentPositioning()
            self.phase_controller = PhaseController()
            
            # Inicializar controlador principal
            self.master_controller = MasterBotController()
            
            print("✅ Sistemas avançados inicializados!")
        
        print(f"✅ Sistemas básicos inicializados:")
        print(f"   📊 Estratégia do deck: {self.deck_analyzer.strategy}")
        print(f"   🎯 Win condition principal: {self.deck_analyzer.get_primary_win_condition()}")
        print(f"   🔄 Combos disponíveis: {len(self.combo_manager.available_combos)}")
        print(f"   🛡️  Cartas defensivas: {len(self.defense_manager.available_defenses)}")
    
    def get_actions(self):
        """Sobrescreve get_actions para usar ações aprimoradas quando possível"""
        
        # Primeiro, obter ações do método original
        original_actions = super().get_actions()
        
        if not self.intelligence_enabled or not original_actions:
            return original_actions
        
        # Mapeamento de ações aprimoradas (se disponíveis)
        enhanced_action_map = {}
        if ENHANCED_ACTIONS_AVAILABLE:
            enhanced_action_map = {
                Cards.GIANT: EnhancedGiantAction,
                Cards.MUSKETEER: EnhancedMusketeerAction,
                Cards.HOG_RIDER: EnhancedHogRiderAction,
            }
        
        enhanced_actions = []
        
        for action in original_actions:
            # Obter a classe da ação original
            action_class = action.__class__
            
            # Verificar se há uma versão aprimorada disponível
            card_found = None
            for card, enhanced_class in enhanced_action_map.items():
                # Verificar se a carta existe no mapeamento atual
                if card in self.cards_to_actions:
                    if action_class == self.cards_to_actions[card].__class__:
                        card_found = card
                        break
            
            if card_found:
                # Criar ação aprimorada
                enhanced_class = enhanced_action_map[card_found]
                enhanced_action = enhanced_class(
                    index=action.index,
                    tile_x=action.tile_x,
                    tile_y=action.tile_y
                )
                
                # Configurar contexto estratégico
                if hasattr(enhanced_action, 'set_strategic_context'):
                    enhanced_action.set_strategic_context(
                        self.deck_analyzer,
                        self.game_state_analyzer,
                        self.combo_manager
                    )
                
                enhanced_actions.append(enhanced_action)
                print(f"🔧 Ação aprimorada criada: {card_found.name}")
            else:
                # Manter ação original
                enhanced_actions.append(action)
        
        return enhanced_actions
    
    def _update_cards_in_hand(self, state):
        """Atualiza lista de cartas na mão (implementação simplificada)"""
        # Obter ações atuais (instâncias)
        actions = self.get_actions()
        
        # Em implementação real, extrair cartas da mão do estado
        # Por enquanto, assumir que temos todas as cartas do deck
        self.cards_in_hand = []
        for action in actions:
            try:
                if hasattr(action, 'CARD'):
                    self.cards_in_hand.append(action.CARD)
                else:
                    # Tentar obter da classe da ação
                    for card_obj, action_class in self.cards_to_actions.items():
                        if isinstance(action, action_class.__class__):
                            self.cards_in_hand.append(card_obj)
                            break
            except Exception as e:
                print(f"⚠️  Erro obtendo carta da ação: {e}")
                continue
    
    def _check_combo_opportunities(self, state) -> Optional[tuple]:
        """Verifica oportunidades de combo"""
        
        if not self.combo_system_enabled or not self.combo_manager:
            return None
        
        # Verificar se há combo ativo
        if self.combo_manager.has_active_combo():
            combo_action = self.combo_manager.get_next_combo_action(time.time())
            if combo_action:
                card, position_rule, coordinates = combo_action
                
                # Verificar se a carta está disponível
                if card in self.cards_to_actions:
                    print(f"🔄 Executando combo: {card.name} em {coordinates}")
                    return self._execute_card_action(card, coordinates)
                else:
                    print(f"⚠️  Carta do combo não disponível: {card.name}")
                    return None
        
        # Avaliar novas oportunidades de combo
        if self.last_game_state:
            best_combo = self.combo_manager.evaluate_combo_opportunities(
                self.last_game_state, self.cards_in_hand
            )
            
            if best_combo:
                print(f"🎯 Iniciando combo: {best_combo.name}")
                active_combo = self.combo_manager.start_combo(best_combo, time.time())
                
                # Executar primeira carta do combo
                combo_action = self.combo_manager.get_next_combo_action(time.time())
                if combo_action:
                    card, position_rule, coordinates = combo_action
                    
                    # Verificar se a carta está disponível
                    if card in self.cards_to_actions:
                        return self._execute_card_action(card, coordinates)
                    else:
                        print(f"⚠️  Carta do combo não disponível: {card.name}")
                        return None
        
        return None
    
    def _check_defense_needs(self, state) -> Optional[tuple]:
        """Verifica necessidade de defesa"""
        
        if not self.defense_system_enabled or not self.defense_manager or not self.last_game_state:
            return None
        
        if not self.last_game_state.should_defend:
            return None
        
        # Planejar defesa
        defense_response = self.defense_manager.plan_defense(
            self.last_game_state.threats,
            self.cards_in_hand,
            state.numbers.elixir.number
        )
        
        if defense_response:
            print(f"🛡️  Executando defesa: {defense_response.primary_card.name}")
            print(f"   Efetividade esperada: {defense_response.expected_effectiveness:.1%}")
            
            # Executar carta defensiva principal
            card = defense_response.primary_card
            position = defense_response.positioning.get(card, (9, 10))
            
            return self._execute_card_action(card, position)
        
        return None
    
    def _record_enemy_plays(self):
        """Registra jogadas inimigas na memória"""
        
        if not self.memory_system or not self.state:
            return
        
        # Registrar unidades inimigas como jogadas
        for enemy in self.state.enemies:
            try:
                # Determinar contexto da jogada
                context = self._determine_enemy_play_context(enemy)
                
                # Determinar lane
                lane = "left" if enemy.position.tile_x < 9 else "right"
                
                # Estimar custo de elixir (simplificado)
                elixir_cost = self._estimate_card_cost(enemy.unit.name)
                
                self.memory_system.record_enemy_play(
                    card=enemy.unit,
                    position=(enemy.position.tile_x, enemy.position.tile_y),
                    lane=lane,
                    elixir_spent=elixir_cost,
                    context=context
                )
            except Exception as e:
                print(f"Erro registrando jogada inimiga: {e}")
    
    def _determine_enemy_play_context(self, enemy) -> str:
        """Determina o contexto de uma jogada inimiga"""
        
        # Se está no nosso lado, é ataque
        if enemy.position.tile_y > 16:
            return "attack"
        # Se está no lado deles, pode ser defesa ou preparação
        elif enemy.position.tile_y < 8:
            return "defense"
        else:
            return "counter"
    
    def _estimate_card_cost(self, card_name: str) -> int:
        """Estima o custo de elixir de uma carta"""
        
        # Mapeamento simplificado - pode ser expandido
        cost_map = {
            'giant': 5, 'golem': 8, 'pekka': 7, 'mega_knight': 7,
            'hog_rider': 4, 'ram_rider': 5, 'balloon': 5,
            'musketeer': 4, 'wizard': 5, 'archers': 3,
            'knight': 3, 'valkyrie': 4, 'mini_pekka': 4,
            'skeletons': 1, 'goblins': 2, 'spear_goblins': 2
        }
        
        return cost_map.get(card_name.lower(), 4)
    
    def _log_elixir_analysis(self, analysis):
        """Log da análise de elixir"""
        
        if not analysis:
            return
        
        print(f"💰 Elixir: {analysis.current_elixir} ({analysis.elixir_state.value})")
        print(f"   Vantagem: {analysis.elixir_advantage:+d}")
        print(f"   Deve conservar: {analysis.should_conserve}")
        print(f"   Deve gastar: {analysis.should_spend}")
        
        if analysis.opportunities:
            best_opp = analysis.opportunities[0]
            print(f"   Melhor oportunidade: {best_opp.card.name} "
                  f"(valor: {best_opp.expected_value:.2f})")
    
    def _intelligent_card_selection(self, state, elixir_analysis=None) -> Optional[tuple]:
        """Seleção inteligente de cartas usando scores aprimorados"""
        
        # Obter ações atuais (instâncias)
        actions = self.get_actions()
        
        if not actions:
            return None
        
        # Calcular scores para todas as ações
        action_scores = []
        
        for action in actions:
            try:
                # Verificar se é uma instância válida
                if not hasattr(action, 'calculate_score'):
                    print(f"⚠️  Ação {action.__class__.__name__} não tem método calculate_score")
                    continue
                
                # Todas as ações usam calculate_score, mas as aprimoradas têm lógica adicional
                scores = action.calculate_score(state)
                
                if scores and len(scores) > 0:
                    primary_score = scores[0]
                    position_info = scores[1] if len(scores) > 1 else 0.0
                    
                    # Aplicar otimização de elixir se disponível
                    if elixir_analysis:
                        primary_score = self._apply_elixir_optimization(
                            action, primary_score, elixir_analysis
                        )
                    
                    # Aplicar insights da memória
                    if self.memory_system:
                        primary_score = self._apply_memory_insights(
                            action, primary_score
                        )
                    
                    action_scores.append({
                        'action': action,
                        'score': primary_score,
                        'position_info': position_info
                    })
            except Exception as e:
                # Tentar obter o nome da carta da ação
                card_name = "Unknown"
                try:
                    # Verificar se é uma ação aprimorada
                    if hasattr(action, 'CARD'):
                        card_name = action.CARD.name
                    else:
                        # Tentar obter da classe da ação
                        card_name = action.__class__.__name__
                except:
                    pass
                
                print(f"⚠️  Erro calculando score para {card_name}: {e}")
                continue
        
        if not action_scores:
            return None
        
        # Ordenar por score
        action_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Selecionar melhor ação
        best_action_info = action_scores[0]
        
        if best_action_info['score'] <= 0:
            return None
        
        best_action = best_action_info['action']
        position_info = best_action_info['position_info']
        
        # Determinar posição
        if hasattr(best_action, 'get_optimal_position') and self.last_game_state:
            try:
                position = best_action.get_optimal_position(self.last_game_state, state)
            except Exception as e:
                print(f"⚠️  Erro obtendo posição ótima: {e}")
                # Fallback para posição baseada em position_info
                if position_info < -0.5:
                    position = (7, best_action.tile_y)  # Esquerda
                elif position_info > 0.5:
                    position = (11, best_action.tile_y)  # Direita
                else:
                    position = (best_action.tile_x, best_action.tile_y)  # Original
        else:
            # Usar posição baseada em position_info
            if position_info < -0.5:
                position = (7, best_action.tile_y)  # Esquerda
            elif position_info > 0.5:
                position = (11, best_action.tile_y)  # Direita
            else:
                position = (best_action.tile_x, best_action.tile_y)  # Original
        
        print(f"🎮 Jogando: {getattr(best_action, 'CARD', 'Unknown').name} "
              f"(score: {best_action_info['score']:.2f}) em {position}")
        
        return self._execute_card_action(best_action.CARD, position)
    
    def _apply_elixir_optimization(self, action, score: float, analysis) -> float:
        """Aplica otimização de elixir ao score"""
        
        # Tentar obter a carta da ação
        card = None
        try:
            if hasattr(action, 'CARD'):
                card = action.CARD
            else:
                # Tentar obter da classe da ação
                for card_obj, action_class in self.cards_to_actions.items():
                    if isinstance(action, action_class.__class__):
                        card = card_obj
                        break
        except:
            return score
        
        if not card or card not in self.cards_to_actions:
            return score
        
        cost = getattr(card, 'cost', 4)
        
        # Encontrar oportunidade correspondente
        for opp in analysis.opportunities:
            if opp.card == card:
                # Ajustar score baseado na recomendação
                if opp.recommended:
                    score *= 1.3
                else:
                    score *= 0.7
                break
        
        # Ajustar baseado no estado do elixir
        if analysis.elixir_state.value == "critical" and cost > 3:
            score *= 0.5  # Penalizar cartas caras com elixir crítico
        
        if analysis.elixir_state.value == "full":
            score *= 1.2  # Bônus para gastar elixir cheio
        
        return score
    
    def _apply_memory_insights(self, action, score: float) -> float:
        """Aplica insights da memória ao score"""
        
        # Tentar obter a carta da ação
        card = None
        try:
            if hasattr(action, 'CARD'):
                card = action.CARD
            else:
                # Tentar obter da classe da ação
                for card_obj, action_class in self.cards_to_actions.items():
                    if isinstance(action, action_class.__class__):
                        card = card_obj
                        break
        except:
            return score
        
        if not card or card not in self.cards_to_actions:
            return score
        
        insights = self.memory_system.get_strategic_insights()
        
        # Ajustar baseado no estilo do inimigo
        play_style = insights.get('play_style', 'unknown')
        
        if play_style == 'aggressive':
            # Preferir defesas contra jogador agressivo
            if self._is_defense_card(card):
                score *= 1.2
        elif play_style == 'defensive':
            # Preferir ataques contra jogador defensivo
            if self._is_attack_card(card):
                score *= 1.2
        
        # Verificar se devemos esperar esta carta
        if self.memory_system.should_expect_card(card):
            score *= 1.1  # Bônus para cartas esperadas
        
        return score
    
    def _is_defense_card(self, card: Cards) -> bool:
        """Verifica se é uma carta defensiva"""
        
        defense_cards = [
            'cannon', 'tesla', 'inferno_tower', 'bomb_tower',
            'knight', 'valkyrie', 'mini_pekka', 'pekka'
        ]
        
        return any(defense in card.name.lower() for defense in defense_cards)
    
    def _is_attack_card(self, card: Cards) -> bool:
        """Verifica se é uma carta de ataque"""
        
        attack_cards = [
            'giant', 'golem', 'pekka', 'hog_rider', 'balloon',
            'musketeer', 'wizard', 'archers'
        ]
        
        return any(attack in card.name.lower() for attack in attack_cards)
    
    def _execute_card_action(self, card: Cards, position: tuple) -> tuple:
        """Executa ação de uma carta específica"""
        
        # Verificar se a carta existe no mapeamento
        if card not in self.cards_to_actions:
            print(f"❌ Carta {card.name} não encontrada no mapeamento")
            return None
        
        # Obter ações atuais (instâncias)
        actions = self.get_actions()
        
        # Encontrar a ação correspondente à carta e posição
        for action in actions:
            try:
                # Verificar se é a carta correta
                action_card = None
                if hasattr(action, 'CARD'):
                    action_card = action.CARD
                else:
                    # Tentar obter da classe da ação
                    for card_obj, action_class in self.cards_to_actions.items():
                        if isinstance(action, action_class.__class__):
                            action_card = card_obj
                            break
                
                # Verificar se é a carta correta e posição correta
                if action_card == card and hasattr(action, 'tile_x') and hasattr(action, 'tile_y'):
                    if (action.tile_x, action.tile_y) == position:
                        print(f"🎮 Executando ação: {card.name} em {position}")
                        self.play_action(action)
                        return (card, position)
            except Exception as e:
                print(f"⚠️  Erro executando ação: {e}")
                continue
        
        print(f"❌ Ação não encontrada para {card.name} em {position}")
        return None
    
    def _log_game_state(self):
        """Log do estado atual do jogo"""
        
        if not self.last_game_state:
            return
        
        gs = self.last_game_state
        
        print(f"📊 Estado do jogo:")
        print(f"   Fase: {gs.phase.value} | Modo: {gs.game_mode}")
        print(f"   Elixir: {gs.our_elixir} | Déficit inimigo: {gs.enemy_elixir_deficit}")
        print(f"   Ameaças: {len(gs.threats)} | Oportunidades: {len(gs.opportunities)}")
        print(f"   Estratégia: {gs.recommended_strategy}")
        
        if gs.threats:
            primary_threat = gs.get_primary_threat()
            print(f"   🚨 Ameaça principal: {primary_threat.card_name} "
                  f"(nível {primary_threat.threat_level.value})")
        
        if gs.opportunities:
            best_opportunity = gs.get_best_opportunity()
            print(f"   🎯 Melhor oportunidade: {best_opportunity.lane} lane "
                  f"(confiança {best_opportunity.confidence:.1%})")
        
        # Log da memória
        if self.memory_system:
            print(self.memory_system.get_memory_summary())
        
        # Log da otimização de elixir
        if self.elixir_optimizer:
            print(self.elixir_optimizer.get_optimization_summary())
    
    def get_bot_stats(self) -> Dict:
        """Retorna estatísticas do bot"""
        
        stats = {
            'intelligence_enabled': self.intelligence_enabled,
            'systems_initialized': bool(self.deck_analyzer),
        }
        
        if self.deck_analyzer:
            stats.update({
                'deck_strategy': self.deck_analyzer.strategy,
                'primary_win_condition': self.deck_analyzer.get_primary_win_condition().name if self.deck_analyzer.get_primary_win_condition() else None,
                'available_combos': len(self.combo_manager.available_combos) if self.combo_manager else 0,
                'enhanced_actions': len(self.enhanced_actions),
            })
        
        if self.last_game_state:
            stats.update({
                'current_phase': self.last_game_state.phase.value,
                'current_mode': self.last_game_state.game_mode,
                'active_threats': len(self.last_game_state.threats),
                'active_opportunities': len(self.last_game_state.opportunities),
            })
        
        # Estatísticas da memória
        if self.memory_system:
            memory_insights = self.memory_system.get_strategic_insights()
            stats.update({
                'enemy_play_style': memory_insights.get('play_style', 'unknown'),
                'enemy_cards_seen': memory_insights.get('cards_seen', 0),
                'enemy_patterns_found': memory_insights.get('patterns_found', 0),
                'enemy_cycle_length': memory_insights.get('cycle_length'),
            })
        
        # Estatísticas de otimização de elixir
        if self.elixir_optimizer:
            elixir_stats = self.elixir_optimizer.get_elixir_efficiency_stats()
            stats.update({
                'elixir_efficiency': elixir_stats.get('efficiency_score', 0.0),
                'average_elixir_cost': elixir_stats.get('average_cost', 0.0),
                'elixir_leaks': elixir_stats.get('leak_count', 0),
            })
        
        return stats
    
    def toggle_intelligence(self, enabled: bool = None):
        """Liga/desliga sistema de inteligência"""
        
        if enabled is None:
            self.intelligence_enabled = not self.intelligence_enabled
        else:
            self.intelligence_enabled = enabled
        
        print(f"🧠 Sistema de inteligência: {'LIGADO' if self.intelligence_enabled else 'DESLIGADO'}")
    
    def toggle_combo_system(self, enabled: bool = None):
        """Liga/desliga sistema de combos"""
        
        if enabled is None:
            self.combo_system_enabled = not self.combo_system_enabled
        else:
            self.combo_system_enabled = enabled
        
        print(f"🔄 Sistema de combos: {'LIGADO' if self.combo_system_enabled else 'DESLIGADO'}")
    
    def toggle_defense_system(self, enabled: bool = None):
        """Liga/desliga sistema de defesa"""
        
        if enabled is None:
            self.defense_system_enabled = not self.defense_system_enabled
        else:
            self.defense_system_enabled = enabled
        
        print(f"🛡️  Sistema de defesa: {'LIGADO' if self.defense_system_enabled else 'DESLIGADO'}")
    
    def cleanup_systems(self):
        """Limpeza de sistemas (chamado periodicamente)"""
        
        if self.combo_manager:
            self.combo_manager.cleanup_completed_combos()
    
    def _update_advanced_game_state(self):
        """Atualiza o estado do jogo para sistemas avançados"""
        
        if not self.advanced_systems_enabled or not self.master_controller:
            return
        
        try:
            # Determinar fase do jogo
            game_time = getattr(self.state, 'game_time', 0.0)
            try:
                phase = self.phase_controller.get_current_phase(game_time) if self.phase_controller else AdvancedGamePhase.MID_GAME
            except AttributeError:
                # Fallback se o método não existir
                if game_time <= 60:
                    phase = AdvancedGamePhase.EARLY_GAME
                elif game_time <= 180:
                    phase = AdvancedGamePhase.MID_GAME
                elif game_time <= 300:
                    phase = AdvancedGamePhase.LATE_GAME
                else:
                    phase = AdvancedGamePhase.OVERTIME
            
            # Estimar elixir inimigo
            enemy_elixir = 5  # Valor padrão
            if self.advanced_elixir:
                enemy_elixir = self.advanced_elixir.estimate_enemy_elixir()
            
            # Obter HP das torres
            tower_hp = {
                "our_left": 2000,  # Valores padrão - idealmente extrair do estado
                "our_right": 2000,
                "enemy_left": 2000,
                "enemy_right": 2000
            }
            
            # Unidades no campo (simplificado)
            units_on_field = []
            if hasattr(self.state, 'units') and self.state.units:
                for unit in self.state.units:
                    units_on_field.append({
                        "name": unit.name,
                        "position": (unit.x, unit.y),
                        "hp": unit.hp,
                        "is_enemy": unit.is_enemy
                    })
            
            # Criar estado avançado
            self.advanced_game_state = GameState(
                game_time=game_time,
                phase=phase,
                our_elixir=self.state.numbers.elixir.number,
                enemy_elixir_estimate=enemy_elixir,
                elixir_advantage=self.state.numbers.elixir.number - enemy_elixir,
                tower_hp=tower_hp,
                units_on_field=units_on_field,
                our_hand=self.cards_in_hand,
                enemy_cards_seen=self.memory_system.get_seen_cards() if self.memory_system else [],
                recent_enemy_plays=self.memory_system.get_recent_plays() if self.memory_system else [],
                recent_our_plays=[]  # Implementar rastreamento de nossas jogadas
            )
            
            # Atualizar controlador principal
            self.master_controller.update_game_state(
                game_time=getattr(self.state, 'game_time', 0.0),
                our_elixir=self.state.numbers.elixir.number if self.state and self.state.numbers and self.state.numbers.elixir else 5,
                tower_hp={'king': 100, 'left': 100, 'right': 100},  # Placeholder
                units_on_field=[],  # Placeholder - implementar detecção de unidades
                our_hand=self.cards_in_hand,
                recent_enemy_plays=self.memory_system.get_recent_plays() if self.memory_system else [],
                recent_our_plays=[]  # Implementar rastreamento de nossas jogadas
            )
            
        except Exception as e:
            print(f"⚠️  Erro atualizando estado avançado: {e}")
    
    def _get_advanced_recommendation(self):
        """Obtém recomendação dos sistemas avançados"""
        
        if not self.advanced_systems_enabled or not self.master_controller:
            return None
        
        try:
            # Obter recomendação do controlador principal
            recommendation = self.master_controller.get_best_action()
            
            if recommendation and recommendation.confidence > 0.7:
                self.last_action_recommendation = recommendation
                print(f"🎯 Recomendação avançada: {recommendation.action_type}")
                print(f"   Carta: {recommendation.card.name if recommendation.card else 'N/A'}")
                print(f"   Posição: {recommendation.position}")
                print(f"   Confiança: {recommendation.confidence:.2f}")
                print(f"   Razão: {', '.join(recommendation.reasoning)}")
                
                return recommendation
            
        except Exception as e:
            print(f"⚠️  Erro obtendo recomendação avançada: {e}")
        
        return None
    
    def _execute_advanced_recommendation(self, recommendation: ActionRecommendation):
        """Executa recomendação dos sistemas avançados"""
        
        if not recommendation:
            return False
        
        try:
            if recommendation.action_type == "play_card" and recommendation.card:
                # Encontrar ação correspondente à carta
                actions = self.get_actions()
                for action in actions:
                    if hasattr(action, 'CARD') and action.CARD == recommendation.card:
                        # Atualizar posição se especificada
                        if recommendation.position:
                            action.tile_x, action.tile_y = recommendation.position
                        
                        # Executar ação
                        self.play_action(action)
                        
                        print(f"🚀 Executando ação avançada: {recommendation.card.name}")
                        self._log_and_wait(
                            f"Advanced action: {recommendation.card.name}",
                            self.play_action_delay
                        )
                        
                        # Registrar nossa jogada na memória
                        if self.memory_system:
                            card_cost = getattr(recommendation.card, 'cost', 4)
                            self.memory_system.record_our_play(
                                card=recommendation.card,
                                elixir_spent=card_cost,
                                strategy=recommendation.action_type
                            )
                        
                        # Registrar resultado para aprendizado
                        if self.master_controller:
                            self.master_controller.record_action_outcome(
                                success=True,  # Assumir sucesso por enquanto
                                damage_dealt=0  # Implementar rastreamento de dano
                            )
                        
                        return True
            
            elif recommendation.action_type == "wait":
                print(f"⏳ Aguardando {recommendation.timing_delay:.1f}s (recomendação avançada)")
                time.sleep(recommendation.timing_delay)
                return True
            
        except Exception as e:
            print(f"⚠️  Erro executando recomendação avançada: {e}")
        
        return False
    
    def _integrate_advanced_systems(self):
        """Integra sistemas avançados na tomada de decisão"""
        
        if not self.advanced_systems_enabled:
            return None
        
        try:
            # Atualizar estado do jogo
            self._update_advanced_game_state()
            
            # Obter recomendação avançada
            recommendation = self._get_advanced_recommendation()
            
            if recommendation:
                # Tentar executar recomendação
                if self._execute_advanced_recommendation(recommendation):
                    return True
            
        except Exception as e:
            print(f"⚠️  Erro integrando sistemas avançados: {e}")
        
        return False
    
    def __repr__(self):
        return f"EnhancedBot(intelligence={self.intelligence_enabled}, " \
               f"combos={self.combo_system_enabled}, defense={self.defense_system_enabled}, " \
               f"advanced={self.advanced_systems_enabled})"

    def _handle_game_step(self):
        """Método sobrescrito para usar lógica inteligente e sistemas avançados"""
        
        if not self.intelligence_enabled:
            # Usar lógica original se inteligência estiver desabilitada
            return super()._handle_game_step()
        
        try:
            # PRIORIDADE 1: Sistemas Avançados (se habilitados)
            if self.advanced_systems_enabled:
                advanced_result = self._integrate_advanced_systems()
                if advanced_result:
                    return  # Sistema avançado tomou decisão
            
            # PRIORIDADE 2: Sistemas Básicos Inteligentes
            # Analisar estado atual do jogo (otimizado - menos frequente)
            if self.game_state_analyzer and self.state and time.time() % 5 < 0.1:  # A cada ~5 segundos
                self.last_game_state = self.game_state_analyzer.analyze_state(self.state)
                self._log_game_state()
            
            # Atualizar cartas na mão
            self._update_cards_in_hand(self.state)
            
            # Registrar jogadas inimigas na memória (otimizado)
            if time.time() % 2 < 0.1:  # A cada ~2 segundos
                self._record_enemy_plays()
            
            # Analisar otimização de elixir (otimizado)
            elixir_analysis = None
            if self.elixir_optimizer and time.time() % 3 < 0.1:  # A cada ~3 segundos
                actions = self.get_actions()
                elixir_analysis = self.elixir_optimizer.analyze_elixir_situation(
                    self.state.numbers.elixir.number, actions
                )
                self._log_elixir_analysis(elixir_analysis)
            
            # Verificar oportunidades de combo
            combo_action = self._check_combo_opportunities(self.state)
            if combo_action:
                self._execute_intelligent_action(combo_action)
                return
            
            # Verificar necessidade de defesa
            defense_action = self._check_defense_needs(self.state)
            if defense_action:
                self._execute_intelligent_action(defense_action)
                return
            
            # Usar lógica aprimorada para seleção de cartas
            intelligent_action = self._intelligent_card_selection(self.state, elixir_analysis)
            if intelligent_action:
                self._execute_intelligent_action(intelligent_action)
                return
            
            # Fallback para lógica original se nada inteligente for encontrado
            print("🤖 Nenhuma decisão inteligente encontrada, usando lógica padrão")
            return super()._handle_game_step()
            
        except Exception as e:
            print(f"Erro no sistema inteligente: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Fallback para lógica original
            return super()._handle_game_step()
    
    def _execute_intelligent_action(self, action_info):
        """Executa ação inteligente (otimizado)"""
        
        if not action_info:
            return
        
        try:
            # Verificar se é tuple com 2 ou 3 valores
            if len(action_info) == 2:
                card, position = action_info
                tile_x, tile_y = position
                # Encontrar índice da carta
                card_index = None
                for i, action in enumerate(self.get_actions()):
                    if hasattr(action, 'CARD') and action.CARD == card:
                        card_index = i
                        break
            elif len(action_info) == 3:
                card_index, tile_x, tile_y = action_info
            else:
                print(f"Formato de ação inválido: {action_info}")
                return
            
            # Encontrar ação correspondente
            actions = self.get_actions()
            if card_index is not None and card_index < len(actions):
                action = actions[card_index]
                
                # Atualizar posição
                action.tile_x = tile_x
                action.tile_y = tile_y
                
                # Executar ação
                self.play_action(action)
                
                card_name = getattr(action, 'CARD', 'Unknown')
                print(f"🎯 Ação inteligente: {card_name} em ({tile_x}, {tile_y})")
                
                # Delay reduzido para melhor responsividade
                self._log_and_wait(
                    f"Playing {card_name} with intelligent strategy",
                    max(0.1, self.play_action_delay * 0.5)  # Reduzir delay pela metade
                )
                
                # Registrar nossa jogada na memória
                if self.memory_system and hasattr(action, 'CARD'):
                    card_cost = getattr(action.CARD, 'cost', 4)
                    self.memory_system.record_our_play(
                        card=action.CARD,
                        elixir_spent=card_cost,
                        strategy="intelligent_play"
                    )
                
                return
                    
        except Exception as e:
            print(f"Erro executando ação inteligente: {e}")
            # Fallback para lógica original
            return super()._handle_game_step()

