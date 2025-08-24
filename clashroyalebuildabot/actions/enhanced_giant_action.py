"""
Lógica aprimorada do Gigante com comportamento inteligente baseado em contexto.
O Gigante atua como tanque principal e iniciador de combos.
"""

from clashroyalebuildabot import Cards
from ..core.enhanced_action import EnhancedAction
from ..core.card_roles import CardRole
from ..core.game_state import GameStateInfo


class EnhancedGiantAction(EnhancedAction):
    """Ação aprimorada do Gigante com inteligência contextual"""
    
    CARD = Cards.GIANT
    
    def calculate_score(self, state):
        """Cálculo de score aprimorado para o Gigante"""
        
        # Score base: só jogar se temos elixir suficiente
        if state.numbers.elixir.number < 5:
            return [0.0]
        
        base_score = 0.3  # Score base moderado
        
        # Usar sistema aprimorado se disponível
        if self.game_state_analyzer:
            return self._calculate_intelligent_score(state)
        
        # Fallback para lógica original melhorada
        return self._calculate_improved_basic_score(state)
    
    def _calculate_intelligent_score(self, state):
        """Cálculo inteligente usando análise de contexto"""
        
        game_state = self.game_state_analyzer.analyze_state(state)
        
        # Não jogar Gigante se há ameaça crítica que precisa de defesa
        if game_state.should_defend:
            primary_threat = game_state.get_primary_threat()
            if primary_threat and primary_threat.requires_immediate_response:
                return [0.1]  # Score muito baixo, mas não zero
        
        # Score baseado na situação estratégica
        strategic_score = self._get_strategic_score(game_state, state)
        
        # Score baseado na oportunidade de combo
        combo_score = self._get_combo_score(game_state, state)
        
        # Score baseado no timing
        timing_score = self._get_timing_score(game_state, state)
        
        # Combinar scores
        final_score = strategic_score * combo_score * timing_score
        
        # Adicionar informação de posicionamento
        position_info = self._get_position_priority(game_state, state)
        
        return [final_score, position_info]
    
    def _get_strategic_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado na estratégia do deck e situação atual"""
        
        base_score = 0.4
        
        # Gigante é melhor quando temos vantagem de elixir
        if game_state.enemy_elixir_deficit >= 3:
            base_score += 0.4
        elif game_state.enemy_elixir_deficit >= 1:
            base_score += 0.2
        
        # Gigante é melhor quando não há defesas pesadas inimigas
        heavy_defenses = ['inferno_tower', 'pekka', 'mini_pekka']
        enemy_has_heavy_defense = any(
            any(defense in threat.card_name.lower() for defense in heavy_defenses)
            for threat in game_state.threats
        )
        
        if not enemy_has_heavy_defense:
            base_score += 0.3
        else:
            base_score -= 0.2
        
        # Melhor em fases mid/late do jogo
        if game_state.phase.value in ['mid', 'late']:
            base_score += 0.2
        
        # Forçar jogada se elixir está cheio
        if state.numbers.elixir.number >= 9:
            base_score += 0.3
        
        return min(1.0, base_score)
    
    def _get_combo_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado em oportunidades de combo"""
        
        if not self.combo_manager:
            return 1.0
        
        # Verificar se há combo ativo que precisa do Gigante
        combo_boost = self.combo_manager.get_combo_priority_boost(self.CARD)
        if combo_boost > 1.0:
            return combo_boost
        
        # Verificar se podemos iniciar um combo
        # Assumindo que temos acesso às cartas na mão (simplificado)
        has_support_cards = True  # Simplificado - em implementação real, verificar cartas na mão
        
        if has_support_cards and state.numbers.elixir.number >= 8:
            return 1.4  # Bonus por poder iniciar combo
        
        return 1.0
    
    def _get_timing_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado no timing da jogada"""
        
        # Não jogar Gigante se inimigo acabou de jogar contador
        # (implementação simplificada)
        
        # Melhor timing quando inimigo gastou elixir
        if game_state.enemy_elixir_deficit >= 4:
            return 1.3
        elif game_state.enemy_elixir_deficit >= 2:
            return 1.1
        
        # Timing neutro
        if game_state.game_mode in ['NEUTRAL', 'ATTACK']:
            return 1.0
        
        # Timing ruim se estamos defendendo
        if game_state.game_mode in ['EMERGENCY_DEFENSE', 'ACTIVE_DEFENSE']:
            return 0.6
        
        return 1.0
    
    def _get_position_priority(self, game_state: GameStateInfo, state) -> float:
        """Determina prioridade de posicionamento"""
        
        # Priorizar lado com menos defesas inimigas
        left_threats = sum(1 for t in game_state.threats if t.position[0] <= 9)
        right_threats = sum(1 for t in game_state.threats if t.position[0] > 9)
        
        if left_threats < right_threats:
            return -1.0  # Preferir lado esquerdo
        elif right_threats < left_threats:
            return 1.0   # Preferir lado direito
        else:
            return 0.0   # Sem preferência
    
    def _calculate_improved_basic_score(self, state):
        """Versão melhorada da lógica básica original"""
        
        # Lógica original melhorada
        base_score = 0.5 if state.numbers.elixir.number >= 8 else 0.2
        
        # Melhorar score baseado em inimigos
        for enemy in state.enemies:
            # Se inimigo está longe, é boa oportunidade para Gigante
            distance = ((enemy.position.tile_x - 9) ** 2 + (enemy.position.tile_y - 14) ** 2) ** 0.5
            
            if distance >= 8:  # Inimigo longe das torres
                base_score += 0.3
            elif distance <= 4:  # Inimigo perto, não é bom momento
                base_score -= 0.2
        
        # Posicionamento inteligente
        position_score = 0.0
        
        # Verificar qual lado tem menos inimigos
        left_enemies = sum(1 for e in state.enemies if e.position.tile_x <= 9)
        right_enemies = sum(1 for e in state.enemies if e.position.tile_x > 9)
        
        if left_enemies < right_enemies:
            position_score = -1.0  # Preferir esquerda
        elif right_enemies < left_enemies:
            position_score = 1.0   # Preferir direita
        
        return [max(0.0, base_score), position_score]
    
    def get_optimal_position(self, game_state: GameStateInfo, state):
        """Posicionamento ótimo do Gigante"""
        
        # Se faz parte de combo, usar posição do combo
        if self.combo_manager and self.combo_manager.has_active_combo():
            combo_action = self.combo_manager.get_next_combo_action(0.0)
            if combo_action and combo_action[0] == self.CARD:
                return combo_action[2]
        
        # Posicionamento estratégico baseado no contexto
        if game_state:
            # Atacar lado com menos defesas
            left_threats = sum(1 for t in game_state.threats if t.position[0] <= 9)
            right_threats = sum(1 for t in game_state.threats if t.position[0] > 9)
            
            if left_threats < right_threats:
                return (7, 4)   # Atrás da torre do rei, lado esquerdo
            elif right_threats < left_threats:
                return (11, 4)  # Atrás da torre do rei, lado direito
            else:
                return (9, 4)   # Centro, atrás da torre do rei
        
        # Posição padrão
        return (9, 4)
    
    def should_wait_for_support(self, game_state: GameStateInfo, state) -> bool:
        """Determina se deve esperar por cartas de suporte antes de jogar"""
        
        if not self.deck_analyzer:
            return False
        
        # Se temos pouco elixir, esperar
        if state.numbers.elixir.number < 7:
            return True
        
        # Se há ameaça crítica, não esperar
        if game_state.should_defend:
            primary_threat = game_state.get_primary_threat()
            if primary_threat and primary_threat.requires_immediate_response:
                return False
        
        # Se temos cartas de suporte na mão, não esperar muito
        # (implementação simplificada)
        support_cards = self.deck_analyzer.get_support_cards()
        
        # Se estratégia do deck favorece combos, esperar um pouco
        if self.deck_analyzer.strategy in ['HEAVY_TANK', 'BALANCED']:
            return state.numbers.elixir.number < 8
        
        return False

