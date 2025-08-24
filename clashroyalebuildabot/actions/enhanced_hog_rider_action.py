"""
Lógica aprimorada do Corredor (Hog Rider) com comportamento inteligente.
O Corredor é especialista em contra-ataques rápidos e pressão constante.
"""

from clashroyalebuildabot import Cards
from ..core.enhanced_action import EnhancedAction
from ..core.card_roles import CardRole
from ..core.game_state import GameStateInfo, ThreatLevel


class EnhancedHogRiderAction(EnhancedAction):
    """Ação aprimorada do Corredor com inteligência contextual"""
    
    CARD = Cards.HOG_RIDER
    
    def calculate_score(self, state):
        """Cálculo de score aprimorado para o Corredor"""
        
        # Score base: Corredor precisa de timing certo
        if state.numbers.elixir.number < 4:
            return [0.0]
        
        # Usar sistema aprimorado se disponível
        if self.game_state_analyzer:
            return self._calculate_intelligent_score(state)
        
        # Fallback para lógica melhorada
        return self._calculate_improved_basic_score(state)
    
    def _calculate_intelligent_score(self, state):
        """Cálculo inteligente usando análise de contexto"""
        
        game_state = self.game_state_analyzer.analyze_state(state)
        
        # Corredor é principalmente para contra-ataque
        counter_attack_score = self._get_counter_attack_score(game_state, state)
        
        # Score baseado na pressão que pode exercer
        pressure_score = self._get_pressure_score(game_state, state)
        
        # Score baseado na ausência de contadores inimigos
        counter_avoidance_score = self._get_counter_avoidance_score(game_state, state)
        
        # Score baseado no timing
        timing_score = self._get_timing_score(game_state, state)
        
        # Combinar scores (Corredor é muito dependente de timing)
        final_score = counter_attack_score * counter_avoidance_score * timing_score * pressure_score
        
        # Informação de posicionamento (Corredor sempre vai para a ponte)
        position_info = self._get_lane_priority(game_state, state)
        
        return [final_score, position_info]
    
    def _get_counter_attack_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado em oportunidades de contra-ataque"""
        
        base_score = 0.3
        
        # SITUAÇÃO IDEAL: Inimigo gastou muito elixir
        if game_state.enemy_elixir_deficit >= 5:
            base_score += 0.6  # Score muito alto
        elif game_state.enemy_elixir_deficit >= 3:
            base_score += 0.4  # Score alto
        elif game_state.enemy_elixir_deficit >= 1:
            base_score += 0.2  # Score moderado
        else:
            base_score -= 0.1  # Penalizar se inimigo tem elixir
        
        # BOOST APÓS DEFESA BEM-SUCEDIDA
        # Se acabamos de defender e inimigo gastou elixir
        if (len(game_state.threats) == 0 and 
            game_state.enemy_elixir_deficit >= 3):
            base_score += 0.4
        
        # PENALIZAR SE ESTAMOS DEFENDENDO
        if game_state.should_defend:
            primary_threat = game_state.get_primary_threat()
            if primary_threat and primary_threat.requires_immediate_response:
                base_score *= 0.3  # Reduzir drasticamente
        
        return min(1.0, base_score)
    
    def _get_pressure_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado na pressão que pode exercer"""
        
        # Corredor é excelente para pressão constante
        base_score = 1.0
        
        # Melhor quando inimigo não tem defesas prontas
        if len(game_state.threats) == 0:
            base_score += 0.2
        
        # Estratégia de cycle favorece Corredor
        if (self.deck_analyzer and 
            self.deck_analyzer.strategy == "CYCLE"):
            base_score += 0.3
        
        # Fase do jogo
        if game_state.phase.value == 'early':
            base_score += 0.1  # Boa pressão inicial
        elif game_state.phase.value == 'late':
            base_score += 0.2  # Pressão final importante
        
        return base_score
    
    def _get_counter_avoidance_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado na ausência de contadores inimigos"""
        
        # Contadores principais do Corredor
        hard_counters = ['cannon', 'tesla', 'tombstone', 'skeleton_army', 'barbarians']
        soft_counters = ['knight', 'valkyrie', 'mini_pekka', 'guards']
        
        base_score = 1.0
        
        # Verificar se há contadores no campo
        for threat in game_state.threats:
            threat_name = threat.card_name.lower()
            
            # Contadores duros = penalidade alta
            if any(counter in threat_name for counter in hard_counters):
                if threat.distance_to_tower <= 8:  # Perto da torre
                    base_score *= 0.3
                else:
                    base_score *= 0.6
            
            # Contadores suaves = penalidade moderada
            elif any(counter in threat_name for counter in soft_counters):
                if threat.distance_to_tower <= 6:
                    base_score *= 0.7
                else:
                    base_score *= 0.9
        
        return base_score
    
    def _get_timing_score(self, game_state: GameStateInfo, state) -> float:
        """Score baseado no timing da jogada"""
        
        base_score = 1.0
        
        # TIMING PERFEITO: Logo após inimigo gastar elixir pesado
        if game_state.enemy_elixir_deficit >= 4:
            base_score += 0.4
        
        # BOM TIMING: Quando não há ameaças ativas
        if len(game_state.threats) == 0:
            base_score += 0.2
        
        # TIMING RUIM: Durante defesa crítica
        if game_state.game_mode == "EMERGENCY_DEFENSE":
            base_score *= 0.2
        
        # TIMING FORÇADO: Elixir cheio
        if state.numbers.elixir.number >= 9:
            base_score += 0.3
        
        # COMBO TIMING: Se faz parte de combo
        if self.combo_manager:
            combo_boost = self.combo_manager.get_combo_priority_boost(self.CARD)
            if combo_boost > 1.0:
                base_score *= combo_boost
        
        return base_score
    
    def _get_lane_priority(self, game_state: GameStateInfo, state) -> float:
        """Determina qual lane atacar"""
        
        # Analisar defesas em cada lane
        left_defenses = 0
        right_defenses = 0
        
        for threat in game_state.threats:
            if threat.position[0] <= 9:  # Lado esquerdo
                if any(defense in threat.card_name.lower() 
                      for defense in ['cannon', 'tesla', 'tombstone']):
                    left_defenses += 1
            else:  # Lado direito
                if any(defense in threat.card_name.lower() 
                      for defense in ['cannon', 'tesla', 'tombstone']):
                    right_defenses += 1
        
        # Atacar lado com menos defesas
        if left_defenses < right_defenses:
            return -1.0  # Preferir esquerda
        elif right_defenses < left_defenses:
            return 1.0   # Preferir direita
        else:
            # Se igual, atacar lado oposto à última ameaça
            if game_state.threats:
                last_threat_x = game_state.threats[0].position[0]
                if last_threat_x <= 9:
                    return 1.0   # Última ameaça à esquerda, atacar direita
                else:
                    return -1.0  # Última ameaça à direita, atacar esquerda
        
        return 0.0  # Sem preferência
    
    def _calculate_improved_basic_score(self, state):
        """Versão melhorada da lógica básica"""
        
        base_score = 0.3
        
        # Boost baseado em elixir disponível
        if state.numbers.elixir.number >= 6:
            base_score += 0.3
        elif state.numbers.elixir.number >= 8:
            base_score += 0.5
        
        # Analisar inimigos no campo
        building_enemies = 0
        troop_enemies = 0
        
        for enemy in state.enemies:
            # Simplificado: assumir que inimigos em posições defensivas são construções
            if enemy.position.tile_y >= 12:  # Perto das torres
                building_enemies += 1
            else:
                troop_enemies += 1
        
        # Penalizar se há muitas defesas
        if building_enemies >= 2:
            base_score *= 0.5
        elif building_enemies == 1:
            base_score *= 0.7
        
        # Boost se há poucas tropas inimigas
        if troop_enemies == 0:
            base_score += 0.4
        elif troop_enemies == 1:
            base_score += 0.2
        
        return [max(0.0, min(1.0, base_score)), 0.0]
    
    def get_optimal_position(self, game_state: GameStateInfo, state):
        """Posicionamento ótimo do Corredor (sempre na ponte)"""
        
        # Se faz parte de combo, usar posição do combo
        if self.combo_manager and self.combo_manager.has_active_combo():
            combo_action = self.combo_manager.get_next_combo_action(0.0)
            if combo_action and combo_action[0] == self.CARD:
                return combo_action[2]
        
        if not game_state:
            return (9, 7)  # Ponte central
        
        # Determinar lane baseado na análise
        lane_priority = self._get_lane_priority(game_state, state)
        
        if lane_priority < -0.5:
            return (7, 7)   # Ponte esquerda
        elif lane_priority > 0.5:
            return (11, 7)  # Ponte direita
        else:
            return (9, 7)   # Ponte central
    
    def should_wait_for_support(self, game_state: GameStateInfo, state) -> bool:
        """Determina se deve esperar por cartas de suporte"""
        
        # Corredor raramente espera - é carta de timing
        
        # Só esperar se há contador direto no campo
        hard_counters = ['cannon', 'tesla', 'tombstone', 'skeleton_army']
        
        for threat in game_state.threats:
            if any(counter in threat.card_name.lower() for counter in hard_counters):
                if threat.distance_to_tower <= 6:
                    return True  # Esperar por feitiço ou suporte
        
        # Não esperar se há oportunidade de contra-ataque
        if game_state.enemy_elixir_deficit >= 4:
            return False
        
        # Não esperar se elixir está cheio
        if state.numbers.elixir.number >= 9:
            return False
        
        return False
    
    def get_combo_synergy_score(self, game_state: GameStateInfo) -> float:
        """Calcula sinergia com outras cartas para combos"""
        
        base_synergy = 0.7
        
        # Sinergia com feitiços (Gelo, Tronco, Raio)
        # (implementação simplificada)
        
        # Sinergia com cartas de cycle
        if (self.deck_analyzer and 
            self.deck_analyzer.strategy == "CYCLE"):
            base_synergy += 0.2
        
        # Melhor sinergia quando inimigo tem baixo elixir
        if game_state.enemy_elixir_deficit >= 3:
            base_synergy += 0.3
        
        return min(1.0, base_synergy)
    
    def is_good_counter_attack_moment(self, game_state: GameStateInfo) -> bool:
        """Verifica se é um bom momento para contra-ataque"""
        
        # Critérios para bom contra-ataque:
        # 1. Inimigo gastou elixir
        # 2. Não há contadores diretos
        # 3. Não estamos defendendo ameaça crítica
        
        if game_state.enemy_elixir_deficit < 3:
            return False
        
        if game_state.should_defend:
            primary_threat = game_state.get_primary_threat()
            if primary_threat and primary_threat.requires_immediate_response:
                return False
        
        # Verificar contadores no campo
        hard_counters = ['cannon', 'tesla', 'tombstone']
        for threat in game_state.threats:
            if any(counter in threat.card_name.lower() for counter in hard_counters):
                if threat.distance_to_tower <= 8:
                    return False
        
        return True

