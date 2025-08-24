"""
Classe base aprimorada para ações das cartas com suporte a combos e análise contextual.
Substitui a Action original com funcionalidades inteligentes.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict
from clashroyalebuildabot.namespaces.cards import Card
from .card_roles import CardRole, CardRoleDatabase, DeckAnalyzer
from .game_state import GameStateAnalyzer, GameStateInfo
from .combo_system import ComboManager


class EnhancedAction(ABC):
    """Classe base aprimorada para ações das cartas"""
    
    CARD: Card = None
    
    def __init__(self, index: int, tile_x: int, tile_y: int):
        self.index = index
        self.tile_x = tile_x
        self.tile_y = tile_y
        
        # Contexto estratégico
        self.deck_analyzer: Optional[DeckAnalyzer] = None
        self.game_state_analyzer: Optional[GameStateAnalyzer] = None
        self.combo_manager: Optional[ComboManager] = None
        
        # Cache de informações
        self._roles_cache: Optional[List[CardRole]] = None
        self._strategic_context: Optional[Dict] = None
    
    def set_strategic_context(self, deck_analyzer: DeckAnalyzer, 
                            game_state_analyzer: GameStateAnalyzer,
                            combo_manager: ComboManager):
        """Define o contexto estratégico para a ação"""
        self.deck_analyzer = deck_analyzer
        self.game_state_analyzer = game_state_analyzer
        self.combo_manager = combo_manager
    
    def get_card_roles(self) -> List[CardRole]:
        """Retorna os papéis desta carta"""
        if self._roles_cache is None:
            self._roles_cache = list(CardRoleDatabase.get_roles(self.CARD))
        return self._roles_cache
    
    def has_role(self, role: CardRole) -> bool:
        """Verifica se esta carta tem um papel específico"""
        return role in self.get_card_roles()
    
    def calculate_enhanced_score(self, state) -> List[float]:
        """Calcula score aprimorado considerando contexto estratégico"""
        
        # Score base da implementação original
        base_score = self.calculate_score(state)
        if not isinstance(base_score, list):
            base_score = [base_score] if base_score else [0.0]
        
        # Se não temos contexto estratégico, usar score original
        if not self.deck_analyzer or not self.game_state_analyzer:
            return base_score
        
        # Analisar estado do jogo
        game_state = self.game_state_analyzer.analyze_state(state)
        
        # Aplicar modificadores estratégicos
        enhanced_score = self._apply_strategic_modifiers(base_score, game_state, state)
        
        # Aplicar boost de combo se aplicável
        combo_boost = self.combo_manager.get_combo_priority_boost(self.CARD) if self.combo_manager else 1.0
        enhanced_score = [score * combo_boost for score in enhanced_score]
        
        return enhanced_score
    
    def _apply_strategic_modifiers(self, base_score: List[float], 
                                 game_state: GameStateInfo, state) -> List[float]:
        """Aplica modificadores baseados na estratégia e contexto"""
        
        if not base_score or base_score[0] == 0:
            return base_score
        
        modified_score = base_score.copy()
        primary_score = modified_score[0]
        
        # 1. Modificadores baseados no papel da carta
        role_modifier = self._get_role_modifier(game_state)
        primary_score *= role_modifier
        
        # 2. Modificadores baseados na fase do jogo
        phase_modifier = self._get_phase_modifier(game_state)
        primary_score *= phase_modifier
        
        # 3. Modificadores baseados na estratégia do deck
        strategy_modifier = self._get_strategy_modifier(game_state, state)
        primary_score *= strategy_modifier
        
        # 4. Modificadores situacionais
        situational_modifier = self._get_situational_modifier(game_state, state)
        primary_score *= situational_modifier
        
        modified_score[0] = max(0.0, min(2.0, primary_score))  # Clamp entre 0 e 2
        return modified_score
    
    def _get_role_modifier(self, game_state: GameStateInfo) -> float:
        """Modificador baseado no papel da carta e situação atual"""
        
        # Cartas defensivas têm prioridade quando há ameaças
        if self.has_role(CardRole.DEFENSE) and game_state.should_defend:
            threat = game_state.get_primary_threat()
            if threat and threat.requires_immediate_response:
                return 1.8
            return 1.4
        
        # Win conditions têm prioridade quando há oportunidade de ataque
        if self.has_role(CardRole.WIN_CONDITION) and game_state.should_attack:
            opportunity = game_state.get_best_opportunity()
            if opportunity and opportunity.confidence >= 0.7:
                return 1.6
            return 1.2
        
        # Cartas de suporte têm prioridade moderada quando há tanque no campo
        if self.has_role(CardRole.SUPPORT):
            # Verificar se há tanque aliado no campo (implementação simplificada)
            return 1.3 if game_state.game_mode == "ATTACK" else 1.0
        
        # Feitiços têm prioridade quando inimigo tem swarm
        if self.has_role(CardRole.SPELL):
            # Verificar se há múltiplas unidades inimigas (swarm)
            if len(game_state.threats) >= 3:
                return 1.5
        
        return 1.0
    
    def _get_phase_modifier(self, game_state: GameStateInfo) -> float:
        """Modificador baseado na fase do jogo"""
        
        # Cartas de cycle são melhores no início
        if self.has_role(CardRole.CYCLE):
            if game_state.phase.value == "early":
                return 1.2
            elif game_state.phase.value == "late":
                return 0.9
        
        # Tanques pesados são melhores no meio/final
        if self.has_role(CardRole.TANK) and not self.has_role(CardRole.CYCLE):
            if game_state.phase.value in ["mid", "late"]:
                return 1.3
            elif game_state.phase.value == "early":
                return 0.8
        
        return 1.0
    
    def _get_strategy_modifier(self, game_state: GameStateInfo, state) -> float:
        """Modificador baseado na estratégia do deck"""
        
        if not self.deck_analyzer:
            return 1.0
        
        strategy = self.deck_analyzer.strategy
        
        # Deck de cycle favorece cartas de baixo custo
        if strategy == "CYCLE" and self.has_role(CardRole.CYCLE):
            return 1.4
        
        # Deck defensivo favorece cartas de defesa
        if strategy == "DEFENSIVE" and self.has_role(CardRole.DEFENSE):
            return 1.3
        
        # Deck de tanque pesado favorece win conditions grandes
        if strategy == "HEAVY_TANK" and self.has_role(CardRole.WIN_CONDITION):
            if self.CARD.name in ["GOLEM", "ELECTRO_GIANT", "GIANT"]:
                return 1.5
        
        return 1.0
    
    def _get_situational_modifier(self, game_state: GameStateInfo, state) -> float:
        """Modificador baseado em situações específicas"""
        
        # Forçar jogada quando elixir está cheio
        if state.numbers.elixir.number >= 9:
            return 1.2
        
        # Reduzir prioridade de cartas caras quando elixir baixo
        expensive_cards = ["GOLEM", "ELECTRO_GIANT", "PEKKA", "MEGA_KNIGHT"]
        if self.CARD.name in expensive_cards and state.numbers.elixir.number <= 5:
            return 0.6
        
        # Aumentar prioridade de contra-ataque após defesa bem-sucedida
        if (game_state.enemy_elixir_deficit >= 4 and 
            self.has_role(CardRole.WIN_CONDITION)):
            return 1.4
        
        return 1.0
    
    def get_optimal_position(self, game_state: GameStateInfo, state) -> Tuple[int, int]:
        """Retorna posição ótima baseada no contexto estratégico"""
        
        # Se faz parte de um combo ativo, usar posição do combo
        if self.combo_manager and self.combo_manager.has_active_combo():
            combo_action = self.combo_manager.get_next_combo_action(0.0)  # Tempo simplificado
            if combo_action and combo_action[0] == self.CARD:
                return combo_action[2]
        
        # Posicionamento baseado no papel da carta
        return self._get_role_based_position(game_state, state)
    
    def _get_role_based_position(self, game_state: GameStateInfo, state) -> Tuple[int, int]:
        """Posicionamento baseado no papel da carta"""
        
        # Win conditions: atrás da torre do rei ou na ponte
        if self.has_role(CardRole.WIN_CONDITION):
            if game_state.should_attack:
                return (9, 7)  # Ponte
            else:
                return (9, 4)  # Atrás da torre do rei
        
        # Defesas: posições defensivas baseadas na ameaça
        if self.has_role(CardRole.DEFENSE):
            threat = game_state.get_primary_threat()
            if threat:
                # Posicionar próximo à ameaça
                threat_x, threat_y = threat.position
                if threat_x <= 9:  # Lado esquerdo
                    return (7, 10)
                else:  # Lado direito
                    return (11, 10)
            return (9, 10)  # Posição defensiva padrão
        
        # Suporte: atrás de outras tropas
        if self.has_role(CardRole.SUPPORT):
            return (9, 6)
        
        # Posição padrão
        return (self.tile_x, self.tile_y)
    
    @abstractmethod
    def calculate_score(self, state) -> List[float]:
        """Implementação original do cálculo de score (deve ser mantida)"""
        pass
    
    def __repr__(self):
        return f"Enhanced{self.CARD.name}Action at ({self.tile_x}, {self.tile_y})"

